from PIL import Image
import os

# --- CONFIGURATION ---
# Image source (doit être carrée)
source_image = "logo.png"  # place ton logo à la racine de JEU
output_dir = "static/icons"  # dossier de sortie

# Tailles d'icônes recommandées pour PWA
sizes = [16, 32, 48, 64, 72, 96, 128, 144, 152, 192, 256, 384, 512]

# --- CRÉATION DU DOSSIER DE SORTIE ---
os.makedirs(output_dir, exist_ok=True)

# --- OUVRIR L'IMAGE SOURCE ---
img = Image.open(source_image)

# --- GÉNÉRER LES ICÔNES ---
for size in sizes:
    img_resized = img.resize((size, size), Image.Resampling.LANCZOS)

    output_path = os.path.join(output_dir, f"icon-{size}x{size}.png")
    img_resized.save(output_path)
    print(f"Icon générée : {output_path}")

print("✅ Toutes les icônes ont été générées avec succès !")
