import os
import requests
from datetime import datetime, timedelta, timezone
import pytz
from icalendar import Calendar, Event

def recuperer_et_creer_calendrier():
    API_KEY = os.environ.get("RAPIDAPI_KEY")
    API_HOST = "handballapi.p.rapidapi.com"
    
    # Dictionnaire contenant les équipes et leurs IDs
    # 6272 = Equipe de France Masculine
    # Remplacer "ID_FEMININ" par le vrai ID quand vous l'aurez trouvé (voir explications plus bas)
    EQUIPES = {
        "France (M)": 6272,
        "France (F)": 6885 # <--- Remplacez par le bon ID (sans guillemets)
    }
    
    headers = {
        "x-rapidapi-host": API_HOST,
        "x-rapidapi-key": API_KEY
    }
    
    # 1. Initialisation du fichier Calendrier (ICS)
    cal = Calendar()
    cal.add('prodid', '-//Calendrier Equipes de France Handball//FR')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'France Handball (M & F)')
    
    tz_paris = pytz.timezone('Europe/Paris')
    matchs_ajoutes = 0

    print("--- DÉBUT DE LA MISE À JOUR DE L'AGENDA ---\n")

    # 2. Boucle sur les équipes pour interroger l'API
    for nom_equipe, team_id in EQUIPES.items():
        if team_id == "ID_FEMININ":
            print(f"⚠️ {nom_equipe} ignorée : Vous devez d'abord configurer son ID dans le code.")
            continue
            
        print(f"🔍 Recherche des prochains matchs pour : {nom_equipe} (ID: {team_id})...")
        
        # On demande la page 0 (qui contient les prochains matchs à venir)
        url = f"https://handballapi.p.rapidapi.com/api/handball/team/{team_id}/matches/next/0"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Erreur API (Code {response.status_code}) pour {nom_equipe}")
                continue
                
            donnees = response.json()
            evenements = donnees.get('events', [])
            
            if not evenements:
                print(f"   Aucun match futur trouvé dans l'API pour {nom_equipe}.")
                continue
                
            # 3. Traitement de chaque match trouvé
            for match in evenements:
                # Extraction des données de l'API (format SofaScore)
                home = match.get('homeTeam', {}).get('name', 'Domicile')
                away = match.get('awayTeam', {}).get('name', 'Extérieur')
                titre = f"[{nom_equipe}] {home} vs {away}"
                
                # Le "startTimestamp" est un format universel en secondes
                timestamp = match.get('startTimestamp')
                if not timestamp:
                    continue
                    
                # Conversion du timestamp (UTC) vers l'heure de Paris
                date_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                date_paris = date_utc.astimezone(tz_paris)
                
                tournoi = match.get('tournament', {}).get('name', 'Compétition Inconnue')
                
                # 4. Ajout au calendrier
                event = Event()
                event.add('summary', titre)
                event.add('dtstart', date_paris)
                # On estime la durée d'un match de handball à 2h
                event.add('dtend', date_paris + timedelta(hours=2))
                event.add('description', f"Compétition : {tournoi}\nDonnées fournies par HandballAPI.")
                
                cal.add_component(event)
                matchs_ajoutes += 1
                
            print(f"   ✅ {len(evenements)} matchs trouvés et ajoutés pour {nom_equipe}.")
            
        except Exception as e:
            print(f"❌ Erreur inattendue pour {nom_equipe} : {e}")

    # 5. Sauvegarde du fichier ICS
    if matchs_ajoutes > 0:
        nom_fichier = "france_handball.ics"
        with open(nom_fichier, 'wb') as f:
            f.write(cal.to_ical())
        print(f"\n🎉 Terminé ! {matchs_ajoutes} matchs ont été enregistrés dans '{nom_fichier}'.")
    else:
        print("\nℹ️ Aucun match n'a été ajouté au calendrier.")

if __name__ == "__main__":
    recuperer_et_creer_calendrier()