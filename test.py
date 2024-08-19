import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import re

# Initialize lists to store data
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

# Loop through the range of game IDs
for game_id in range(1, 4707):
    # Print the current game ID to monitor progress
    print(f'Processing game ID: {game_id}')
    
    # Construct the full URL
    url = f'{base_url}{game_id}'
    
    # Send a GET request
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the page content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            # Extract the opponent and home team
            h2_tag = soup.find('h2')
            if h2_tag:
                team_links = h2_tag.find_all('a')
                if len(team_links) >= 2:
                    home_team = team_links[0].text.strip()
                    away_team = team_links[1].text.strip()
                    score = h2_tag.text.split()[-1]
                    
                    # Determine the opponent and home status
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

            # Extract the attendance
            attendance_tag = soup.find('span', class_='legende', text='Zuschauer*innen')
            if attendance_tag:
                attendance_text = attendance_tag.find_next_sibling(text=True)
                attendance = int(attendance_text.strip().replace("'", "").replace(",", ""))
            else:
                attendance = None

            # Extract the date, time, type of game, and round from the first <p> tag
            p_tag = soup.find('p')
            if p_tag:
                # Extract the full text
                full_text = p_tag.text.strip()

                # Use regex to find date, time, and round
                date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', full_text)
                time_match = re.search(r'(\d{2}:\d{2})', full_text)
                round_match = re.search(r'Runde:\s*(\d+)', full_text)

                # Extract the date, time, and round
                date = date_match.group(1) if date_match else None
                time = time_match.group(1) if time_match else None
                round_num = round_match.group(1) if round_match else None

                # Extract the type of game by splitting the string appropriately
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
            
            # Extract the stadium
            stadium_tag = soup.find('span', class_='legende', text='Stadion/Ort')
            if stadium_tag:
                stadium = stadium_tag.find_next_sibling(text=True).strip().split(',')[0]
            else:
                stadium = None
            
            # Append the data to the lists
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
            # Handle pages with missing data by appending None
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

# Create a DataFrame
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

# Save the DataFrame to a CSV file
df.to_csv('fc_zurich_games.csv', index=False)

print('Data scraping completed and saved to fc_zurich_games.csv')
