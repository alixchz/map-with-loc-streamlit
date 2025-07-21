import streamlit as st
import requests
from PIL import Image
import io
import contextily as ctx
import matplotlib.pyplot as plt
from pyproj import Transformer 
import matplotlib.image as mpimg
from episodes import get_episodes

st.set_page_config(page_title="Génération automatique de carte", layout="centered")
st.title("Génération automatique de carte - Doudou podcast R&I")

lat_france, lon_france = 46.603354, 1.888334

def search_city(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 10,
        "countrycodes": "fr"  # limiter à la France
    }
    headers = {
        "User-Agent": "streamlit_app_v1"  # important pour Nominatim
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return []

query = st.text_input("Tapez le nom de la ville")

ville_selectionnee = None

if query:
    with st.spinner("Recherche en cours..."):
        results = search_city(query)
        if results:
            options = []
            for r in results:
                city = r.get("display_name", "")
                # Extraire ville et département si possible
                addr = r.get("address", {})
                ville = addr.get("city") or addr.get("town") or addr.get("village") or ""
                departement = addr.get("county") or ""
                label = f"{ville} ({departement})"
                options.append((label, r))
            
            labels = [o[0] for o in options]
            choice = st.selectbox("Sélectionnez la ville :", labels)
            ville_selectionnee = next(r for l, r in options if l == choice)
        else:
            st.info("Aucune ville trouvée.")

if ville_selectionnee:
    lat = float(ville_selectionnee["lat"])
    lon = float(ville_selectionnee["lon"])
    st.success(f"Ville sélectionnée : {choice} ({lat}, {lon})")

    with st.spinner("Génération de la carte..."):
        # Initialiser le transformeur lon/lat -> Web Mercator
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)

        # Convertir bbox France en EPSG:3857
        xmin, xmax, ymin, ymax = -9.0, 14.0, 37.0, 55.5
        xmin, ymin = transformer.transform(xmin, ymin)
        xmax, ymax = transformer.transform(xmax, ymax)

        fig, ax = plt.subplots(figsize=(8, 6))

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        # Ajouter fond satellite Esri
        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, zoom=6)

        # Charger logo PNG (exemple : 50x50 px)
        logo_path = 'logo_loc.png'
        logo_img = mpimg.imread(logo_path)
        #logo_width_px = logo_img.shape[1]
        #logo_height_px = logo_img.shape[0]

        # Convertir coordonnées ville en EPSG:3857
        x, y = transformer.transform(lon, lat)


        # Choisir la taille du logo sur la carte (en mètres)
        h_px, w_px = logo_img.shape[0], logo_img.shape[1]
        aspect_ratio = h_px / w_px
        logo_width_m = 420000  # largeur en mètres (~20 km)
        logo_height_m = logo_width_m * aspect_ratio  # hauteur proportionnelle
        buffer = io.BytesIO()

        ratio_offset_x = 5.6 #st.number_input("Ratio décalage du logo h", value=6.0, step=1.0)
        ratio_offset_y = 30 #st.number_input("Ratio décalage du logo v", value=10.0, step=1.0)
        offset_x = -logo_width_m/ratio_offset_x
        offset_y = -logo_height_m/ratio_offset_y # pour ancrer le bas du pin à la position

        # Afficher le logo
        #ax.plot(x, y, 'ro', markersize=1)
        ax.imshow(
            logo_img,
            extent=(
                x + offset_x,
                x + offset_x + logo_width_m,
                y + offset_y,
                y + offset_y + logo_height_m
            ),
            zorder=10
        )

        ax.axis('off')
        ax.set_aspect('equal')

        plt.savefig(buffer, format="png", bbox_inches='tight', pad_inches=0, dpi=300)
        buffer.seek(0)

        # Crop l'image
        x, y, w, h = 100, 150, 1000, 1000
        image = Image.open(buffer)
        image_cropped = image.crop((x, y, x + w, y + h))
        # Afficher l’image cropée dans Streamlit
        st.image(image_cropped, caption="Carte satellite recadrée", use_column_width=True)

        # Sauvegarder dans un buffer pour téléchargement
        buffer_cropped = io.BytesIO()
        image_cropped.save(buffer_cropped, format="PNG")
        buffer_cropped.seek(0)
        st.download_button(
            label="Télécharger",
            data=buffer_cropped,
            file_name=f"carte_{ville_selectionnee.get('name')}.png",
            mime="image/png",
            type="secondary"
        )
        titles_list = get_episodes()
        st.subheader("Épisodes du podcast Doudou R&I")
        if titles_list:
            for title in titles_list:
                st.write(f"- {title}")
        else:
            st.write("Aucun épisode trouvé.")


    if False:
        # Ajouter des cases pour les coordonnées de recadrage
        x = st.number_input("Coordonnée X", value=x, step=10)
        y = st.number_input("Coordonnée Y", value=y, step=10)
        w = st.number_input("Largeur (W)", value=w, step=10)
        h = st.number_input("Hauteur (H)", value=h, step=10)

        # Recalculer et afficher l'image recadrée
        if buffer:
            image = Image.open(buffer)
            image_cropped = image.crop((x, y, x + w, y + h))
            st.image(image_cropped, caption="Carte satellite recadrée", use_container_width=True)

            # Sauvegarder dans un buffer pour téléchargement
            buffer_cropped = io.BytesIO()
            image_cropped.save(buffer_cropped, format="PNG")
            buffer_cropped.seek(0)

            st.download_button(
                label="Télécharger la carte satellite recadrée",
                data=buffer_cropped,
                file_name="carte_satellite_recadree.png",
                mime="image/png"
            )