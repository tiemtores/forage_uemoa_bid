import streamlit as st
import pandas as pd
import folium
import plotly.express as px
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, Fullscreen
import branca

# Configuration de la page
st.set_page_config(page_title="UEMOA - WebSIG Hydraulique", layout="wide")

# En-tête avec Logo Forage (Méthode HTML robuste)
st.markdown(
    """
    <div style="display: flex; align-items: center; background-color: #e3f2fd; padding: 15px; border-radius: 12px; margin-bottom: 25px; border-left: 8px solid #1976d2;">
        <img src="https://cdn-icons-png.flaticon.com/512/2942/2942515.png" width="100">
        <div style="margin-left: 25px;">
            <h1 style="margin: 0; color: #0d47a1; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">💧 WebSIG - Forages UEMOA</h1>
            <p style="margin: 0; font-size: 1.1rem; color: #555; font-weight: bold;">Plateforme de Monitoring des Infrastructures Hydrauliques</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Chargement et Nettoyage
@st.cache_data
def load_data():
    # Correction du chemin : on cherche le fichier dans le même dossier que app.py
    df = pd.read_csv('forage_uemoa_.csv', sep=';', encoding='latin-1')
    
    # Nettoyage robuste des colonnes
    df.columns = df.columns.str.strip()
    
    # Mapping flexible pour trouver Latitude et Longitude quelle que soit la casse
    col_map = {c.lower(): c for c in df.columns}
    
    if 'latitude' in col_map:
        df = df.rename(columns={col_map['latitude']: 'Latitude'})
    if 'longitude' in col_map:
        df = df.rename(columns={col_map['longitude']: 'Longitude'})
    if 'pays' in col_map:
        df = df.rename(columns={col_map['pays']: 'PAYS'})
    if 'type' in col_map:
        df = df.rename(columns={col_map['type']: 'Type'})

    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])
    
    # Nettoyage Debit
    debit_col = [c for c in df.columns if 'debit' in c.lower()]
    if debit_col:
        df = df.rename(columns={debit_col[0]: 'Debit (m3/h)'})
        df['Debit (m3/h)'] = pd.to_numeric(df['Debit (m3/h)'], errors='coerce').fillna(0)
    
    return df

df = load_data()

# --- COULEURS ET LÉGENDE ---
TYPE_COLORS = {
    'PMH': 'blue',
    'PEA': 'green',
    'AEP': 'orange',
    'AEPS': 'darkred',
    'SMV': 'purple',
    'OTHER': 'gray'
}

# --- BARRE LATÉRALE ---
st.sidebar.header("🔍 Recherche & Filtres")
search_query = st.sidebar.text_input("Chercher un Village ou Commune", "")
countries = sorted(df['PAYS'].unique().tolist())
selected_country = st.sidebar.selectbox("Filtrer par Pays", ["Tous les pays"] + countries)
types = sorted(df['Type'].dropna().unique().tolist())
selected_type = st.sidebar.multiselect("Type d'ouvrage", options=types, default=types)

# --- FILTRAGE ---
filtered_df = df.copy()
if search_query:
    filtered_df = filtered_df[filtered_df['Village'].str.contains(search_query, case=False, na=False) | filtered_df['Commune'].str.contains(search_query, case=False, na=False)]
if selected_country != "Tous les pays":
    filtered_df = filtered_df[filtered_df['PAYS'] == selected_country]
filtered_df = filtered_df[filtered_df['Type'].isin(selected_type)]

# --- DASHBOARD ---
st.markdown("### 📊 Statistiques de la sélection")
k1, k2, k3 = st.columns(3)
k1.metric("Total Ouvrages", len(filtered_df))
debit_total = filtered_df['Debit (m3/h)'].sum()
k2.metric("Débit cumulé", f"{debit_total:.1f} m³/h")
k3.metric("Pays couverts", filtered_df['PAYS'].nunique())

col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    fig_type = px.pie(filtered_df, names='Type', title="Répartition par Type", hole=0.4, color_discrete_map=TYPE_COLORS)
    st.plotly_chart(fig_type, use_container_width=True)
with col_chart2:
    if selected_country == "Tous les pays":
        avg_debit = filtered_df.groupby('PAYS')['Debit (m3/h)'].mean().reset_index()
        fig_avg = px.bar(avg_debit, x='PAYS', y='Debit (m3/h)', title="Débit moyen par pays (m³/h)", color='PAYS')
        st.plotly_chart(fig_avg, use_container_width=True)
    else:
        fig_dist = px.histogram(filtered_df, x='Debit (m3/h)', title="Distribution des débits dans le pays", nbins=20)
        st.plotly_chart(fig_dist, use_container_width=True)

# --- CARTE SIG ---
st.divider()
st.subheader(f"🗺️ Spatialisation par type : {selected_country}")

if not filtered_df.empty:
    center_lat, center_lon, zoom = filtered_df['Latitude'].mean(), filtered_df['Longitude'].mean(), (6 if selected_country == "Tous les pays" else 8)
else:
    center_lat, center_lon, zoom = 12.0, 2.0, 5

m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="cartodbpositron")
m.add_child(Fullscreen())

marker_cluster = MarkerCluster(name="Forages").add_to(m)

for index, row in filtered_df.iterrows():
    # Déterminer la couleur
    icon_color = TYPE_COLORS.get(row['Type'], TYPE_COLORS['OTHER'])
    
    popup_content = f"""
    <div style="font-family: Arial; min-width: 200px;">
        <h4 style="color:#004a99; border-bottom: 1px solid #ccc; margin-bottom: 5px;">{row['Village']}</h4>
        <table style="width:100%; font-size:11px;">
    """
    for col in ['ID_Station', 'Type', 'Commune', 'Debit (m3/h)', 'PAYS']:
        if col in row: popup_content += f"<tr><td><b>{col}:</b></td><td>{row[col]}</td></tr>"
    popup_content += "</table></div>"
    
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_content, max_width=350),
        tooltip=f"{row['Village']} ({row['Type']})",
        icon=folium.Icon(color=icon_color, icon='tint', prefix='fa')
    ).add_to(marker_cluster)

# Ajout de la légende flottante
legend_html = f'''
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 150px; height: 160px; 
     background-color: white; border:2px solid grey; z-index:9999; font-size:12px;
     padding: 10px; opacity: 0.8; border-radius: 10px;">
     <b>Légende (Types)</b><br>
     <i class="fa fa-map-marker" style="color:blue"></i> PMH<br>
     <i class="fa fa-map-marker" style="color:green"></i> PEA<br>
     <i class="fa fa-map-marker" style="color:orange"></i> AEP<br>
     <i class="fa fa-map-marker" style="color:darkred"></i> AEPS<br>
     <i class="fa fa-map-marker" style="color:purple"></i> SMV<br>
     <i class="fa fa-map-marker" style="color:gray"></i> Autres
     </div>
     '''
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width="100%", height=600, key=f"map_color_{selected_country}")

# Inventaire
st.divider()
st.subheader("📋 Inventaire détaillé")
st.dataframe(filtered_df, use_container_width=True)
