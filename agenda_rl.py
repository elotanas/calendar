import os
import requests
from datetime import datetime, timedelta, timezone
import pytz
from icalendar import Calendar, Event
import time

def creer_calendrier_rl_tier1_pandascore():
    # Votre clé d'API PandaScore (la même que pour CS2)
    TOKEN = os.environ.get("PANDASCORE_TOKEN")
    
    # 🔴 NOUVELLE URL : On cible le jeu Rocket League (rl)
    url = "https://api.pandascore.co/rl/matches/upcoming"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json"
    }
    
    # 🔴 NOUVELLE LISTE D'ÉQUIPES TIER 1 (Rocket League)
    EQUIPES_TIER_1 = [
        "karmine corp", "kc", "team bds", "bds", "vitality", "gentle mates", "m8",
        "gen.g", "g2", "furia", "falcons", "spacestation", "ssg", "complexity"
    ]
    
    # Filtres spécifiques (à adapter si besoin pour RL)
    MOTS_INTERDITS = ["academy"] 
    
    cal = Calendar()
    cal.add('prodid', '-//Calendrier Rocket League Tier 1//FR')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Rocket League - Matchs Tier 1')
    
    tz_paris = pytz.timezone('Europe/Paris')
    matchs_ajoutes = 0
    matchs_totaux_analyses = 0

    print("--- DÉBUT DE LA MISE À JOUR (ROCKET LEAGUE) ---\n")
    
    # Boucle de pagination (jusqu'à 10 pages = 1000 matchs)
    for numero_page in range(1, 11):
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
                break 
                
            matchs = response.json()
            
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
                    
                if any(mot in equipe_1.lower() or mot in equipe_2.lower() for mot in MOTS_INTERDITS):
                    continue
                    
                # Vérification Tier 1
                est_tier_1 = False
                for equipe_top in EQUIPES_TIER_1:
                    # Dans RL, les noms d'équipes peuvent être courts (ex: "g2"), on fait attention
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
                
                nom_ligue = match.get('league', {}).get('name', 'Rocket League')
                nom_serie = match.get('serie', {}).get('name', '')
                nom_tournoi = match.get('tournament', {}).get('name', '')
                nom_match = match.get('name', '')
                
                nom_complet = f"{nom_ligue} {nom_serie}".strip()
                avancement = ""
                
                mots_etapes_cles = ["final", "quarter", "semi", "round", "bracket", "stage", "swiss"]
                
                if " vs " not in nom_match.lower() and any(mot in nom_match.lower() for mot in mots_etapes_cles):
                    avancement = nom_match
                elif nom_tournoi and nom_tournoi.lower() != "playoffs":
                    if " vs " in nom_match.lower():
                        avancement = nom_tournoi
                    else:
                        avancement = f"{nom_tournoi} - {nom_match}"
                else:
                    avancement = nom_tournoi if nom_tournoi else "Match RLCS"

                format_match = match.get('number_of_games', 5) # Souvent BO5 ou BO7 dans RL
                
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
                
                # 🔴 DURÉE ROCKET LEAGUE : Les matchs sont plus courts que CS.
                # Un BO5 dure environ 45min, un BO7 environ 1h.
                duree_minutes = 45 if format_match <= 5 else 60
                event.add('dtend', date_paris + timedelta(minutes=duree_minutes))
                
                event.add('description', description)
                
                cal.add_component(event)
                matchs_ajoutes += 1
                
                print(f"  -> Ajout : {titre} ({date_paris.strftime('%d/%m à %H:%M')})")
                
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"❌ Erreur inattendue sur la page {numero_page}: {e}")
            break

    print(f"\n📊 Bilan : {matchs_totaux_analyses} matchs scannés au total.")

    if matchs_ajoutes > 0:
        nom_fichier = "rocket_league_tier1.ics"
        with open(nom_fichier, 'wb') as f:
            f.write(cal.to_ical())
        print(f"🎉 Terminé ! {matchs_ajoutes} matchs ont été enregistrés dans '{nom_fichier}'.")
    else:
        print("ℹ️ Aucun match des équipes ciblées n'a été trouvé.")

if __name__ == "__main__":
    creer_calendrier_rl_tier1_pandascore()