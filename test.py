# This file prepares data of FC Zürich games in order to make predictions about gameday attendance

import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import re

game_ids = []
dates = []
scores = []
types_of_games = []
rounds = []
stadiums = []
times = []
attendances = []
opponents = []
home_teams = []

# Define the base URL
base_url = 'https://dbfcz.ch/spiel.php?spiel_id='

for game_id in range(1, 100):
    print(f'Processing game ID: {game_id}')
    
    url = f'{base_url}{game_id}'
    
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            h2_tag = soup.find('h2')
            if h2_tag:
                team_links = h2_tag.find_all('a')
                if len(team_links) >= 2:
                    home_team = team_links[0].text.strip()
                    away_team = team_links[1].text.strip()
                    score = h2_tag.text.split()[-1]
                    
                    if 'FCZ' in home_team:
                        opponent = away_team
                        home = 1
                    elif 'FCZ' in away_team:
                        opponent = home_team
                        home = 0
                    else:
                        opponent = None
                        home = None
                else:
                    home_team = None
                    away_team = None
                    opponent = None
                    score = None
                    home = None
            else:
                home_team = None
                away_team = None
                opponent = None
                score = None
                home = None

            attendance_tag = soup.find('span', class_='legende', text='Zuschauer*innen')
            if attendance_tag:
                attendance_text = attendance_tag.find_next_sibling(text=True)
                attendance = int(attendance_text.strip().replace("'", "").replace(",", ""))
            else:
                attendance = None

            p_tag = soup.find('p')
            if p_tag:
                full_text = p_tag.text.strip()

                date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', full_text)
                time_match = re.search(r'(\d{2}:\d{2})', full_text)
                round_match = re.search(r'Runde:\s*(\d+)', full_text)

                date = date_match.group(1) if date_match else None
                time = time_match.group(1) if time_match else None
                round_num = round_match.group(1) if round_match else None

                type_game_start = full_text.find(' - ') + 3
                type_game_end = full_text.find('Runde:')
                if type_game_start > 0 and type_game_end > type_game_start:
                    type_of_game = full_text[type_game_start:type_game_end].strip().strip('-')
                else:
                    type_of_game = None

            else:
                date = None
                time = None
                type_of_game = None
                round_num = None
            
            stadium_tag = soup.find('span', class_='legende', text='Stadion/Ort')
            if stadium_tag:
                stadium = stadium_tag.find_next_sibling(text=True).strip().split(',')[0]
            else:
                stadium = None
            
            game_ids.append(game_id)
            dates.append(date)
            times.append(time)
            types_of_games.append(type_of_game)
            rounds.append(round_num)
            scores.append(score)
            opponents.append(opponent)
            attendances.append(attendance)
            stadiums.append(stadium)
            home_teams.append(home)
        except AttributeError:
            print(f'Missing data for game ID: {game_id}')
            game_ids.append(game_id)
            dates.append(None)
            times.append(None)
            types_of_games.append(None)
            rounds.append(None)
            scores.append(None)
            opponents.append(None)
            attendances.append(None)
            stadiums.append(None)
            home_teams.append(None)
    
    # Add a delay to be polite to the server
    sleep(0.5)

df = pd.DataFrame({
    'Game ID': game_ids,
    'Date': dates,
    'Time': times,
    'Type of Game': types_of_games,
    'Round': rounds,
    'Score': scores,
    'Opponent': opponents,
    'Attendance': attendances,
    'Stadium': stadiums,
    'Home': home_teams
})

df.index = pd.to_datetime(df["Date"])

df['home_goals'] = df['Score'].str.extract(r'\((\d+):(\d+)\)').fillna(0)[0].astype(int)  # fill NaN with 0
df['away_goals'] = df['Score'].str.extract(r'\((\d+):(\d+)\)').fillna(0)[1].astype(int)  # fill NaN with 0


df['win'] = ((df['Home'] == 1) & (df['home_goals'] > df['away_goals'])) | \
            ((df['Home'] == 0) & (df['away_goals'] > df['home_goals']))

df['draw'] = df['home_goals'] == df['away_goals']

df.loc[df['Score'] == '*', ['win', 'draw']] = 0

df['win'] = df['win'].astype(int)
df['draw'] = df['draw'].astype(int)

print(df)


df.to_csv('fc_zurich_games.csv', index=False)
