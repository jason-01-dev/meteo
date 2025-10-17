from flask import Flask, request, render_template
import requests
from datetime import datetime

app = Flask(__name__)

# ----- CLÉS API (inchangées) -----
# Clé Unsplash pour les photos de ville
UNSPLASH_ACCESS_KEY = "e8Fx9xicMnQVZekwHWvu3f9bVMPfRqthth9q-juQxRg"

# ⚠️ FONCTIONS GÉOGRAPHIQUES MISE À JOUR : Récupère le pays ET l'altitude ⚠️
def get_city_info(ville):
    """Récupère le nom de la ville, le pays et l'altitude pour l'affichage."""
    
    # 1. Utilisation de Nominatim (OpenStreetMap) pour le pays et les coordonnées de base
    nominatim_url = f"https://nominatim.openstreetmap.org/search?q={ville}&format=json&limit=1"
    headers = {'User-Agent': 'MeteoProApp/1.0'}
    
    city_display_name = ville
    city_name_for_image = ville
    latitude = None
    longitude = None
    altitude = "N/A"
    
    try:
        r = requests.get(nominatim_url, headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        if data:
            item = data[0]
            latitude = item.get('lat')
            longitude = item.get('lon')
            display_name = item.get('display_name', ville)
            
            parts = display_name.split(', ')
            country = parts[-1]
            city_name = parts[0]
            
            city_display_name = f"{city_name}, {country}"
            city_name_for_image = city_name

    except requests.exceptions.RequestException as e:
        print(f"Erreur API Nominatim: {e}")

    # 2. Utilisation d'Open-Meteo Geocoding pour l'altitude (si les coordonnées sont trouvées)
    if latitude and longitude:
        altitude_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name_for_image}&count=1&language=fr&format=json"
        
        try:
            r_alt = requests.get(altitude_url, timeout=5)
            r_alt.raise_for_status()
            alt_data = r_alt.json()
            
            if 'results' in alt_data and alt_data['results']:
                # On prend le premier résultat et on le formate
                alt = alt_data['results'][0].get('elevation')
                if alt is not None:
                    altitude = f"{int(alt)} m"

        except requests.exceptions.RequestException as e:
            print(f"Erreur API Open-Meteo Geocoding (Altitude): {e}")

    # Retourne les informations complètes
    return city_display_name, city_name_for_image, altitude


# ----- FONCTIONS EXISTANTES (Alertes et Images) -----

# ... (get_seismic_alert, get_severe_weather_alert, get_city_image restent inchangées) ...
def get_seismic_alert():
    """Récupère la dernière alerte de séisme majeure (M > 4.5) de l'USGS."""
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()

        if data['features']:
            quake = data['features'][0]['properties']
            time_utc = datetime.fromtimestamp(quake['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            tsunami_risk = quake.get('tsunami', 0) == 1
            tsunami_alert = None
            if tsunami_risk:
                tsunami_alert = {
                    "niveau": "SURVEILLANCE CÔTIÈRE",
                    "zones": f"Régions côtières proches de {quake['place']}",
                    "conseil": "Quittez immédiatement les zones de faible altitude.",
                    "lien_details": quake['url']
                }

            return {
                "seisme": {
                    "magnitude": f"{quake['mag']:.1f}",
                    "echelle": "Moment",
                    "lieu": quake['place'],
                    "heure": time_utc,
                    "lien_details": quake['url']
                },
                "tsunami": tsunami_alert
            }
    except requests.exceptions.RequestException as e:
        print(f"Erreur API USGS : {e}")
    
    return {"seisme": None, "tsunami": None}

def get_severe_weather_alert():
    """Simule la récupération d'une alerte météo sévère."""
    return None 

def get_city_image(ville):
    """Récupère une image aléatoire de la ville depuis Unsplash."""
    url = f"https://api.unsplash.com/photos/random?query={ville}&client_id={UNSPLASH_ACCESS_KEY}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data['urls']['regular']
    except requests.exceptions.RequestException:
        pass
    return "{{ url_for('static', filename='placeholder.png') }}"
# ... (Fin des fonctions existantes) ...


# ----- ROUTE PRINCIPALE MISE À JOUR -----
@app.route("/", methods=["GET", "POST"])
def index():
    ville = None
    meteo_actuelle = None
    details = {}
    prevision = []
    city_image_url = None
    
    # 1. Récupération des alertes
    alertes = get_seismic_alert()
    alerte_seisme = alertes["seisme"]
    alerte_tsunami = alertes["tsunami"]
    alerte_meteo_severe = get_severe_weather_alert() 

    if request.method == "POST":
        ville_recherchee = request.form.get("ville")
        
        # --- ÉTAPE CLÉ 1 : Récupérer le nom complet (Ville, Pays) ET l'altitude ---
        ville_affichee, ville_pour_image, altitude_value = get_city_info(ville_recherchee)
        ville = ville_affichee
        city_image_url = get_city_image(ville_pour_image)
        
        # --- ÉTAPE CLÉ 2 : Utilisation de l'API wttr.in pour la météo ---
        try:
            response = requests.get(f"https://wttr.in/{ville_recherchee}?format=j1")
            response.raise_for_status() 
            data = response.json()
            
            # Traitement des données wttr.in
            current = data['current_condition'][0]
            meteo_actuelle = f"{current['FeelsLikeC']}°C, {current['weatherDesc'][0]['value']}"
            details = {
                "Humidité": current['humidity'] + "%",
                "Vent": f"{current['windspeedKmph']} km/h {current['winddir16Point']}",
                "Pression": current['pressure'] + " hPa",
                "UV": current['uvIndex'],
                "Visibilité": current['visibility'] + " km",
                "Altitude": altitude_value # NOUVEAU : Ajout de l'altitude
            }
            
            for jour in data['weather'][:3]:
                # ... (Les prévisions restent inchangées) ...
                prevision.append({
                    "date": jour['date'],
                    "max_temp": jour['maxtempC'],
                    "min_temp": jour['mintempC'],
                    "condition": jour['hourly'][4]['weatherDesc'][0]['value'],
                    "vent": jour['hourly'][4]['windspeedKmph'] + " km/h",
                    "humidite": jour['hourly'][4]['humidity'] + "%",
                    "uv_index": jour['hourly'][4]['uvIndex']
                })
                
        except (requests.exceptions.RequestException, KeyError, IndexError):
            meteo_actuelle = "Ville non trouvée ou erreur de données. Réessayez."

    # 3. Rendu du template avec toutes les données
    return render_template(
        "index_detailed.html",
        ville=ville, 
        meteo_actuelle=meteo_actuelle,
        details=details,
        prevision=prevision,
        city_image_url=city_image_url,
        alerte_seisme=alerte_seisme,
        alerte_tsunami=alerte_tsunami,
        alerte_meteo_severe=alerte_meteo_severe
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)