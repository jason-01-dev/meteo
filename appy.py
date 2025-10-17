from flask import Flask, request, render_template
import requests

app = Flask(__name__)

# ----- CLE API UNSPLASH -----
UNSPLASH_ACCESS_KEY = "e8Fx9xicMnQVZekwHWvu3f9bVMPfRqthth9q-juQxRg"  # Remplace par ta clé

def get_city_image(ville):
    """Récupère une image aléatoire de la ville depuis Unsplash."""
    url = f"https://api.unsplash.com/photos/random?query={ville}&client_id={UNSPLASH_ACCESS_KEY}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            return data['urls']['regular']  # petite image adaptée pour web
    except:
        pass
    # image par défaut si problème
    return "https://via.placeholder.com/200x150?text=Ville+non+trouvée"

# ----- ROUTE PRINCIPALE -----
@app.route("/", methods=["GET", "POST"])
def index():
    ville = None
    meteo_actuelle = None
    details = {}
    prevision = []
    city_image_url = None

    if request.method == "POST":
        ville = request.form.get("ville")
        city_image_url = get_city_image(ville)  # récupère la photo

        try:
            response = requests.get(f"https://wttr.in/{ville}?format=j1")
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]

                # Météo actuelle
                meteo_actuelle = f"{current['FeelsLikeC']}°C, {current['weatherDesc'][0]['value']}"

                # Détails actuels
                details = {
                    "Humidité": current['humidity'] + "%",
                    "Vent": f"{current['windspeedKmph']} km/h {current['winddir16Point']}",
                    "Pression": current['pressure'] + " hPa",
                    "UV": current['uvIndex'],
                    "Visibilité": current['visibility'] + " km"
                }

                # Prévision 3 jours
                for jour in data['weather'][:3]:
                    prevision.append({
                        "date": jour['date'],
                        "max_temp": jour['maxtempC'],
                        "min_temp": jour['mintempC'],
                        "condition": jour['hourly'][4]['weatherDesc'][0]['value'],  # milieu de journée
                        "vent": jour['hourly'][4]['windspeedKmph'] + " km/h",
                        "humidite": jour['hourly'][4]['humidity'] + "%",
                        "uv_index": jour['hourly'][4]['uvIndex']
                    })
            else:
                meteo_actuelle = "Impossible d'obtenir la météo."
        except requests.exceptions.RequestException:
            meteo_actuelle = "Erreur de connexion Internet."

    return render_template(
        "index_detailed.html",
        ville=ville,
        meteo_actuelle=meteo_actuelle,
        details=details,
        prevision=prevision,
        city_image_url=city_image_url
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
