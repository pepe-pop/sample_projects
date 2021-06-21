
import requests
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import re
import schedule
import time
from datetime import date
from datetime import datetime
from IPython.display import clear_output
from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
from dash import Dash


# #### Informacje o TOP 100 gier - ID, nazwa, kategoria

# Lista wszystkich gier i ich ID
app_id_url = 'https://api.steampowered.com/ISteamApps/GetAppList/v2/'
app_id = requests.get(app_id_url)
x1 = app_id.json()['applist']['apps']


# Lista ID dla TOP 100 gier
app_id_url1 = 'https://store.steampowered.com/stats/Steam-Game-and-Player-Statistics?l=100'
app_id1 = requests.get(app_id_url1)

web_content = BeautifulSoup(app_id1.text,'lxml')
web_content = web_content.findAll('a',{'class':'gameLink'})

# Lista TOP 100 gier i ich ID
top_games = []

for game_no in range(len(web_content)):
    top_games.append(web_content[game_no].text)
    
app_list = {}

for app_id in x1:
    app_list[app_id['name']] =  app_id['appid']
    
games = {'ID':[],'Game':[],'Genre': [], 'No_players': {}}

for app in app_list:
    if app in top_games:
        games["ID"].append(app_list[app])
        games["Game"].append(app)
        
        
# Kategorie dla TOP 100 gier
for appid in games['ID']:
    try:
        app_genre_url = 'https://store.steampowered.com/app/' + str(appid)
        app_genre = requests.get(app_genre_url)
        web_content_genre = BeautifulSoup(app_genre.text,'lxml')
        web_content_genre = web_content_genre.findAll('div', {'class':'blockbg'})[0]
        web_content_genre = web_content_genre.find_all('a')[1].text
        games["Genre"].append(web_content_genre.rsplit(' ', 1)[0])
    except:
        games["Genre"].append('NA')


# #### DATA FRAMEs

# tabela z aktualna liczba graczy w totalu (df_current_no_players)
df_current_no_players = pd.DataFrame() 

# tabela z liczba graczy per gra / kategoria (df_stats)
games['No_players'] = {}
df_games = pd.DataFrame() 
df_stats = pd.DataFrame()


# #### Funkcja pobierająca dane o aktualnej liczbie graczy


def RTA_func():
#### 1. AKTUALNA LICZBA GRACZY W TOTALU
    global df_current_no_players
    
    #Aktualna liczba graczy i peak z ostatnich 48h
    total_players_url = 'https://store.steampowered.com/stats/'
    total_players = requests.get(total_players_url)
    web_content_total = BeautifulSoup(total_players.text,'lxml')

    #Aktualna liczba graczy
    web_content_current = web_content_total.findAll('td', {'class':'users_count'})[0].text
    current_no_players = int(web_content_current.replace(',',''))
    
    #Peak z ostatnich 48h
    web_content_peak = web_content_total.findAll('td', {'class':'users_count'})[1].text
    peak_no_players = int(web_content_peak.replace(',',''))
    
    #Dolaczanie danych
    date = [datetime.now().strftime('%m-%d %H:%M:%S')]
    current_no_players = [current_no_players]
    peak_no_players = [peak_no_players]
    
    dfx = pd.DataFrame(list(zip(date ,current_no_players, peak_no_players)),
                       columns = ['Time','No_players', 'Peak'])
    
    df_current_no_players = df_current_no_players.append(dfx)

    
    
#### 2. AKTUALNA LICZBA GRACZY PER GRA / KATEGORIA
    global games
    global df_games
    global df_stats
    current_time = datetime.now().strftime('%m-%d %H:%M:%S')
    games['No_players'][current_time] = []

    for appid in games['ID']:
        try:
            game_players_url = 'https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?format=json&appid=' + str(appid)
            game_players = requests.get(game_players_url)
            game_players = game_players.json()['response']['player_count']
            games['No_players'][current_time].append(game_players)   
        except:
            games['No_players'][current_time].append(0)    


    # Przeksztalcanie slownika do Data Frame
    df = pd.DataFrame(list(zip(games['ID'], games['Game'], games['Genre'])),
                columns =['ID', 'Game', 'Genre'])

    df_games = pd.DataFrame.from_dict(games['No_players']) 
    df_stats = pd.concat([df.reset_index(drop=True), df_games], axis=1)
    df_stats = df_stats.melt(id_vars=['ID','Game','Genre'], var_name='Time', value_name='No_players')


    
# ======== WIZUALIZACJA W DASH ========
# przekształcenia zbioru

    data = df_stats
    data["Date"] = pd.to_datetime(data['Time'].apply(lambda x: f"2021-{str(x)}"), format='%Y-%m-%d %H:%M')
    data.sort_values("Date", inplace=True)


# dodanie czcionki
    external_stylesheets = [
        {
            "href": "https://fonts.googleapis.com/css2?"
            "family=Lato:wght@400;700&display=swap",
            "rel": "stylesheet",
        },
    ]

    
    app = dash.Dash(__name__,external_stylesheets=external_stylesheets)


    app.layout = html.Div(
        children=[
            html.Div(
                children=[
                    html.P(children="🎮", className="header-emoji"),
                    html.H1(
                        children="Steam analytics", className="header-title"
                    ),
                    html.P(
                        children="Analiza ruchu sieciowego i liczby graczy na platformie Steam",
                        className="header-description",
                    ),
                ],
                className="header",
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.Div(children="Kategoria", className="menu-title"),
                            dcc.Dropdown(
                                id="category-filter",
                                options=[
                                    {"label": kategoria, "value": kategoria}
                                    for kategoria in np.sort(data.Genre.astype(str).unique())
                                ],
                                value=[kategoria for kategoria in np.sort(data.Genre.astype(str).unique()) if kategoria != 'NA'],
                                clearable=False,
                                className="dropdown",
                                multi = True
                            ),
                        ]
                    ),
                 ],
                className="menu",
            ),
            html.Div(
                children=[
                    html.Div(
                        children=dcc.Graph(
                            id="total-chart",
                            config={"displayModeBar": False},
                        ),
                        className="card",
                    ),
                    html.Div(
                        children=dcc.Graph(
                            id="category-chart",
                            config={"displayModeBar": False},
                        ),
                        className="card",
                    ),
                ],
                className="wrapper",
            ),
        ]
    )


    @app.callback(
        [Output("total-chart", "figure"), Output("category-chart", "figure")],
        [
            Input("category-filter", "value"),
        ],
    )
    def update_charts(value):

        filtered_data = data.loc[data['Genre'].isin(value)]
        filtered_data2 = filtered_data.groupby(['Date'])['No_players'].apply(list).reset_index(name='values')
        for i in range(len(filtered_data2)):
            filtered_data2.loc[i,'values1'] = sum(filtered_data2.loc[i,'values'])
        filtered_data3 = filtered_data.groupby(['Genre'])['No_players'].apply(list).reset_index(name='values')
        for i in range(len(filtered_data3)):
            filtered_data3.loc[i,'values1'] = sum(filtered_data3.loc[i,'values'])

        total_chart_figure = {
            "data": [
                {
                    "x": filtered_data2["Date"],
                    "y": filtered_data2['values1'],
                    "type": "lines",

                },
            ],
            "layout": {
                "title": {
                    "text": "Total amount of players",
                    "x": 0.05,
                    "xanchor": "left",
                },
                "xaxis": {"fixedrange": True},
                "yaxis": {"fixedrange": True},
                "colorway": ["#17B897"],
            },
        }

        category_chart_figure = {
            "data": [
                {
                    "x": filtered_data3["Genre"],
                    "y": filtered_data3["values1"],
                    "type": "bar",
                },
            ],
            "layout": {
                "title": {"text": "Liczba graczy w kategoriach", "x": 0.05, "xanchor": "left"},
                "xaxis": {"fixedrange": True},
                "yaxis": {"fixedrange": True},
                "colorway": ["#E12D39"],
            },
        }
        return total_chart_figure, category_chart_figure


    if __name__ == "__main__":
        app.run_server(debug=True,port=8051)




# #### Pobieranie danych w czasie rzeczywistym


# Skrypt uruchamiający powyzsza funkcje co 2 MINUTY
schedule.every(2).minutes.do(RTA_func)

while 1:
    schedule.run_pending()
    time.sleep(1)



