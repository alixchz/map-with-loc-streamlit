from bs4 import BeautifulSoup
import requests

URL = "https://www.vodio.fr/rssmedias.php?valeur=1671"

def get_episodes():
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(URL)
        response.raise_for_status()  # Vérifier que la requête a réussi
        # Analyser le contenu HTML avec BeautifulSoup
        soup = BeautifulSoup(response.text, features="xml")
        print(soup)
        episodes = soup.find_all("item")
        # Parcourir et extraire titre + description
        titles = []
        for ep in episodes:
            title = ep.find("title").text.strip() if ep.find("title") else "Titre non trouvé"
            description = ep.find("description").text.strip() if ep.find("description") else "Description non trouvée"

            print(f"Titre : {title}\nDescription : {description}\n{'-'*60}")
            titles.append(title)
    except Exception as e:
        print(f"Erreur lors de la récupération des données : {e}")
        return None