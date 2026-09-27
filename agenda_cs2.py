import os
import requests
from datetime import datetime, timedelta, timezone
import pytz
from icalendar import Calendar, Event
import time

def creer_calendrier_cs_tier1_pandascore():
    TOKEN = os.environ.get("PANDASCORE_TOKEN")
    url = "https://api.pandascore.co/csgo/matches/upcoming"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json"
    }
    
    EQUIPES_TIER_1 = [
        "vitality", "faze", "g2", "mouz", "natus vincere", "navi", "spirit", "9z", "aurora",
        "virtus.pro", "vp", "astralis", "complexity", "liquid", "heroic", "3dmax"
    ]
    
    MOTS_INTERDITS = ["academy", "ares", "junior", "hyper"]
    
    cal = Calendar()
    cal.add('prodid', '-//Calendrier CS2 Tier 1//FR')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'CS2 - Matchs Tier 1')
    
    tz_paris = pytz.timezone('Europe/Paris')
    matchs_ajoutes = 0
    matchs_totaux_analyses = 0

    print("--- DÉBUT DE LA MISE À JOUR (PANDASCORE - SCAN 1000 MATCHS) ---\n")
    
    # 🔴 BOUCLE DE PAGINATION
    for numero_page in range(1, 11): # De la page 1 à 10
        print(f"📡 Récupération de la page {numero_page}...")
        
        params = {
            "per_page": 100,
            "page": numero_page,
            "sort": "begin_at"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ Erreur API sur la page {numero_page} (Code {response.status_code})")
                break # On arrête la boucle en cas d'erreur
                
            matchs = response.json()
            
            # Si la page est vide, ça veut dire qu'on a atteint la fin du calendrier PandaScore
            if not matchs:
                print("ℹ️ Fin des matchs à venir atteinte sur PandaScore.")
                break
                
            matchs_totaux_analyses += len(matchs)
            
            for match in matchs:
                if match.get('status') == 'canceled':
                    continue
                    
                opponents = match.get('opponents', [])
                if not opponents or len(opponents) < 2:
                    continue
                    
                try:
                    equipe_1 = opponents[0]['opponent']['name']
                    equipe_2 = opponents[1]['opponent']['name']
                except (KeyError, IndexError):
                    continue
                    
                # Filtre des mots interdits (Academy, Ares, etc.)
                if any(mot in equipe_1.lower() or mot in equipe_2.lower() for mot in MOTS_INTERDITS):
                    continue
                    
                # Vérification Tier 1
                est_tier_1 = False
                for equipe_top in EQUIPES_TIER_1:
                    if equipe_top in equipe_1.lower() or equipe_top in equipe_2.lower():
                        est_tier_1 = True
                        break
                        
                if not est_tier_1:
                    continue
                    
                date_debut_str = match.get('begin_at')
                if not date_debut_str:
                    continue
                    
                date_utc = datetime.strptime(date_debut_str, "%Y-%m-%dT%H:%M:%SZ")
                date_utc = date_utc.replace(tzinfo=timezone.utc)
                date_paris = date_utc.astimezone(tz_paris)
                
                # Extraction détaillée de l'événement
                nom_ligue = match.get('league', {}).get('name', 'CS2')
                nom_serie = match.get('serie', {}).get('name', '')
                nom_tournoi = match.get('tournament', {}).get('name', '')
                nom_match = match.get('name', '')
                
                nom_complet = f"{nom_ligue} {nom_serie}".strip()
                avancement = ""
                
                mots_etapes_cles = ["final", "quarter", "semi", "round", "bracket", "decider", "elimination", "stage"]
                
                if " vs " not in nom_match.lower() and any(mot in nom_match.lower() for mot in mots_etapes_cles):
                    avancement = nom_match
                elif nom_tournoi and nom_tournoi.lower() != "playoffs":
                    if " vs " in nom_match.lower():
                        avancement = nom_tournoi
                    else:
                        avancement = f"{nom_tournoi} - {nom_match}"
                else:
                    avancement = nom_tournoi if nom_tournoi else "Match régulier"

                format_match = match.get('number_of_games', 3)
                
                titre = f"[{nom_complet}] {equipe_1} vs {equipe_2}"
                if avancement:
                    titre += f" | {avancement}"
                    
                description = (
                    f"Compétition : {nom_complet}\n"
                    f"Étape : {avancement}\n"
                    f"Format : BO{format_match}\n"
                    f"Données : PandaScore"
                )
                
                event = Event()
                event.add('summary', titre)
                event.add('dtstart', date_paris)
                
                duree_estimee = format_match if format_match > 1 else 1.5 
                event.add('dtend', date_paris + timedelta(hours=duree_estimee))
                event.add('description', description)
                
                cal.add_component(event)
                matchs_ajoutes += 1
                
                print(f"  -> Ajout : {titre} ({date_paris.strftime('%d/%m à %H:%M')})")
                
            # Petite pause entre les requêtes pour respecter les limites de l'API (Rate Limiting)
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"❌ Erreur inattendue sur la page {numero_page}: {e}")
            break

    print(f"\n📊 Bilan : {matchs_totaux_analyses} matchs scannés au total.")

    if matchs_ajoutes > 0:
        nom_fichier = "cs2_tier1_pandascore.ics"
        with open(nom_fichier, 'wb') as f:
            f.write(cal.to_ical())
        print(f"🎉 Terminé ! {matchs_ajoutes} matchs Tier 1 ont été enregistrés dans '{nom_fichier}'.")
    else:
        print("ℹ️ Aucun match des équipes Tier 1 n'a été trouvé.")

if __name__ == "__main__":
    creer_calendrier_cs_tier1_pandascore()