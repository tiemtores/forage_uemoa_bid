import pandas as pd
import numpy as np

# Liste des pays de l'UEMOA avec échappement correct des apostrophes
uemoa_countries = ["Bénin", "Burkina Faso", "Côte d'Ivoire", "Guinée-Bissau", "Mali", "Niger", "Sénégal", "Togo"]

data = []
for country in uemoa_countries:
    # Coordonnées approximatives des capitales pour centrer les données
    centers = {
        "Bénin": [9.3, 2.3], "Burkina Faso": [12.2, -1.6], "Côte d'Ivoire": [7.5, -5.5],
        "Guinée-Bissau": [11.8, -15.2], "Mali": [17.6, -4.0], "Niger": [17.6, 8.1],
        "Sénégal": [14.5, -14.4], "Togo": [8.6, 0.8]
    }
    lat_c, lon_c = centers[country]
    
    for i in range(20):
        data.append({
            'ID_Station': f"ST-{country[:3].upper()}-{i:03d}",
            'Nom': f"Station {country} {i+1}",
            'Pays': country,
            'Commune': f"Commune {i+1}",
            'Type': np.random.choice(['Forage', 'Puits moderne', 'Château d\'eau']),
            'Etat': np.random.choice(['Fonctionnel', 'En panne', 'En maintenance']),
            'Debit_m3h': round(np.random.uniform(2.5, 18.0), 1),
            'Profondeur_m': np.random.randint(30, 150),
            'Annee_Installation': np.random.randint(2005, 2024),
            'latitude': lat_c + np.random.uniform(-1.5, 1.5),
            'longitude': lon_c + np.random.uniform(-1.5, 1.5)
        })

df = pd.DataFrame(data)
df.to_csv('uemoa-water-app/stations_uemoa.csv', index=False)
print("Fichier CSV de démonstration généré.")
