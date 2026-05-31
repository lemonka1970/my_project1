import json
import requests
import ast

import pandas as pd
import numpy as np
from pandas import read_excel, concat
import time
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime



def get_data(feed):
    """
    Получает данные с Flashscore API и парсит их из кастомного формата.
    :param feed: Идентификатор данных
    :return: list[dict]: Список словарей с данными
    """

    bl_res = False
    response = None
    max_attempts = 20
    attempt = 0
    while not bl_res:

        sleep_time = np.random.randint(0, 2)
        time.sleep(sleep_time)
        url = f'https://global.flashscore.ninja/2/x/feed/{feed}'

        try:
            response = requests.get(url=url, headers={"x-fsign": "SW9D1eZo"})
            bl_res = True
        except:
            if attempt > max_attempts:
                print('что-то не так, проверьте подключение или впн')
            attempt += 1
            # print('произошла ошибка, но все збс')


    data = response.text.split('¬')

    data_list = [{}]

    for item in data:
        key = item.split('÷')[0]
        value = item.split('÷')[-1]

        if '~' in key:
            data_list.append({key: value})
        else:
            data_list[-1].update({key: value})

    return data_list




def get_response(url_):
    """
        Возвращает ответ от сервера по url. Используется для получения http или json с flashscore api
        :param url_: Url для запроса
        :return: Response object
    """
    response_ = None
    bl_ = True
    while bl_:
        sleep_time = np.random.randint(0, 2)
        time.sleep(sleep_time)
        try:
            response_ = requests.get(url_, headers={"x-fsign": "SW9D1eZo"})
            bl_ = False
        except:
            pass
    return response_

# CREATE TABLE regions (
# region_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
# flashscore_region_id INT UNIQUE NOT NULL,
# region_name VARCHAR(30) UNIQUE NOT NULL
# )

# CREATE TABLE leagues (
# league_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
# flashscore_league_feed VARCHAR(8) UNIQUE NOT NULL,
# competition_type VARCHAR(1) NOT NULL,
# stage_type INT,
# category_id INT NOT NULL,
# league_url TEXT UNIQUE NOT NULL,
# league_name TEXT NOT NULL,
# region_id INT REFERENCES regions(region_id)
# )

# CREATE TABLE seasons (
# season_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
# tournament_id VARCHAR(8) NOT NULL,
# tournament_stage_id VARCHAR(8) NOT NULL,
# start_date INT,
# end_date INT,
# is_current BOOLEAN NOT NULL,
# league_id INT REFERENCES leagues(league_id),
# region_id INT REFERENCES regions(region_id)
# UNIQUE(tournament_id, tournament_stage_id)
# )


# CREATE TABLE teams (
# team_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
# team_name VARCHAR(30) UNIQUE NOT NULL,
# flashscore_team_feed VARCHAR(8) UNIQUE NOT NULL,
# flashscore_team_url TEXT UNIQUE NOT NULL
# )

# CREATE TABLE season_team_relations (
# season_id INT NOT NULL REFERENCES seasons(season_id),
# team_id INT NOT NULL REFERENCES teams(team_id)
# )

# CREATE TABLE matches (
# match_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
# time INT NOT NULL,
# flashscore_match_feed VARCHAR(8) UNIQUE NOT NULL,
# home_team_id INT NOT NULL,
# away_team_id INT NOT NULL,
# home_score INT NOT NULL,
# away_score INT NOT NULL,
# home_penalties INT,
# away_penalties INT,
# status VARCHAR(10),
# season_id INT REFERENCES seasons(season_id),
# region_id INT REFERENCES leagues(league_id)
# )




def fetch_regions():
    conn = psycopg2.connect(host='localhost', port=5432, dbname='football_data', user='postgres', password=1234)
    cur = conn.cursor()

    query = """
            INSERT INTO regions (flashscore_region_id, region_name)
            VALUES %s
            ON CONFLICT
            DO NOTHING
            """

    regions = []
    columns = ['region_id', 'flashscore_region_id', 'region_name']



    # с главного табло сайта flashscore грузим страны и регионы и информацию о них
    for day in range(-7, 8):
        feed = f'f_1_{day}_3_ru-kz_1'
        data = get_data(feed)

        for el in data:
            if '~ZA' in el.keys() and el.get('ZB'):
                regions.append((el.get('ZB'), el.get('ZY')))


    execute_values(cur, query, regions)

    conn.commit()
    cur.close()
    conn.close()



def fetch_leagues():
    conn = psycopg2.connect(host='localhost', port=5432, dbname='football_data', user='postgres', password=1234)
    cur = conn.cursor()

    query = """
            INSERT INTO leagues (flashscore_league_feed, competition_type, stage_type, category_id, league_url, league_name,
                   region_id)
            VALUES %s
            ON CONFLICT 
            DO NOTHING
            """

    keys = ['ZEE', 'ZD', 'ZG', 'ZJ', 'ZL', '~ZA', 'ZB']
    leagues = []

    # из главного табло сайта flashscore грузим все текущие лиги и информацию о них
    # так же из бд берем region_id
    for day in range(-7, 8):
        feed = f'f_1_{day}_3_ru-kz_1'
        data = get_data(feed)
        for el in data:
            if '~ZA' in el.keys():
                row = [el.get(keys[i]) for i in range(len(keys))]
                row[5] = row[5].split(': ')[1]
                cur.execute(
                    """SELECT region_id
                    FROM regions
                    WHERE flashscore_region_id = %s
                    """, (row[6],)
                )
                res = cur.fetchone()
                if res is None:
                    continue
                row[6] = res[0]
                leagues.append(tuple(row))


    execute_values(cur, query, leagues)

    conn.commit()
    cur.close()
    conn.close()



def fetch_seasons():
    conn = psycopg2.connect(host='localhost', dbname='football_data', port=5432, password=1234, user='postgres')
    cur = conn.cursor()

    query = """
        INSERT INTO seasons (tournament_id, tournament_stage_id, start_date, end_date, is_current, league_id, region_id)
        VALUES %s
        ON CONFLICT (tournament_id, tournament_stage_id)
        DO UPDATE SET
        is_current = EXCLUDED.is_current
        """

    current_seasons = []
    columns = ['tournament_id', 'tournament_stage_id', 'start_date', 'end_date','is_current', 'league_id', 'region_id']

    # из главного табло сайта flashscore загружаем текущие сезоны и информацию о них
    # так же из бд берем league_id
    for day in range(-7, 8):
        feed = f'f_1_{day}_3_ru-kz_1'
        data = get_data(feed)
        for el in data:
            if '~ZA' in el.keys():
                row = [el.get('ZE'), el.get('ZC'), 0, 0, True, el.get('ZEE'), 0]
                cur.execute("""
                    SELECT league_id, region_id
                    FROM leagues
                    WHERE flashscore_league_feed = %s
                    """, (row[5],)
                )
                res = cur.fetchone()
                if res is None:
                    continue

                row[5] = res[0]
                row[6] = res[1]
                if row not in current_seasons:
                    current_seasons.append(row)

    # для каждого текущего сезона загружаем все его предшествующие
    for current_row in current_seasons:
        if current_row[0] == '0':
            continue
        seasons = []

        url = f'https://2.ds.lsapp.eu/pq_graphql?_hash=lph&tournamentId={current_row[0]}&tournamentStageId={current_row[1]}&projectId=2'
        response = get_response(url)
        data = response.json().get('data').get('getTournamentSeasons').get('other')
        if len(data) == 0:
            continue

        current_row[2] = int(data[0].get('start')) + 1
        current_row[3] = current_row[2] + int(data[0].get('end')) - int(data[0].get('start'))
        seasons.append(tuple(current_row))


        for el in data:
            row = [el.get('tournamentId'),
                   el.get('tournamentStages').get('other')[0].get('id'),
                   el.get('start'),
                   el.get('end'),
                   False,
                   current_row[5],
                   current_row[6]
                   ]

            seasons.append(tuple(row))

        # print(seasons)
        execute_values(cur, query, seasons)
        conn.commit()


    cur.close()
    conn.close()



def fetch_teams():
    conn = psycopg2.connect(host='localhost', dbname='football_data', user='postgres', port=5432, password=1234)
    cur = conn.cursor()

    query = """
    INSERT INTO teams (team_name, flashscore_team_feed, flashscore_team_url)
    VALUES %s
    ON CONFLICT
    DO NOTHING
    """

    # запрашиваем все feed сезонов
    cur.execute("""
    SELECT tournament_id, tournament_stage_id
    FROM seasons
    """)
    data = cur.fetchall()
    data = [f'to_{el[0]}_{el[1]}_1' for el in data]

    # собираем все команды, игравшие в наших лигах
    teams = []

    for st_feed in data:
        standings = get_data(st_feed)
        for el in standings:
            if '~TR' in el.keys():
                teams.append((el.get('TN'), el.get('TI'), el.get('TIU')))


        execute_values(cur, query, teams)
        conn.commit()

    cur.close()
    conn.close()



def build_season_team_relations():
    conn = psycopg2.connect(host='localhost', dbname='football_data', user='postgres', port=5432, password=1234)
    cur = conn.cursor()

    query = """
    INSERT INTO season_team_relations (season_id, team_id)
    VALUES %s
    ON CONFLICT
    DO NOTHING
    """

    # собираем id и feed всех сезонов
    cur.execute("""
        SELECT season_id, tournament_id, tournament_stage_id
        FROM seasons
        """)
    data = cur.fetchall()
    data = [[el[0], f'to_{el[1]}_{el[2]}_1'] for el in data]

    # уже обработанные сезоны
    cur.execute("""
    SELECT DISTINCT(season_id)
    FROM season_team_relations
    """)
    old_season_ids = cur.fetchall()
    old_season_ids = [el[0] for el in old_season_ids]

    # для каждого сезона собираем feed команд в них игравших,
    # получаем по ним их id и загружаем (season_id, team_id)
    for i in range(len(data)):
        season_id = data[i][0]
        st_feed = data[i][1]
        if season_id in old_season_ids:
            continue

        season_team = []
        # print(season_id, st_feed)

        standings = get_data(st_feed)
        feed_teams = []
        for el in standings:
            if '~TR' in el.keys():
                feed_teams.append(el.get('TI'))

        cur.execute("""
        SELECT team_id
        FROM teams
        WHERE flashscore_team_feed = ANY(%s)
        """, (feed_teams,))

        team_ids = cur.fetchall()
        for id_ in team_ids:
            season_team.append((season_id, id_[0]))

        execute_values(cur, query, season_team)
        conn.commit()


    cur.close()
    conn.close()



def initialize_matches():
    conn = psycopg2.connect(host='localhost', dbname='football_data', user='postgres', port=5432, password=1234)
    cur = conn.cursor()

    query = """
    INSERT INTO matches (time, flashscore_match_feed, 
                        home_team_id, away_team_id, 
                        home_score, away_score, 
                        home_penalties, away_penalties,
                        status, season_id, region_id)
    VALUES %s
    ON CONFLICT
    DO NOTHING
    """

    # получаем id всех регионов
    cur.execute("""
    SELECT region_id
    FROM regions
    """)
    region_ids = cur.fetchall()
    region_ids = [id_[0] for id_ in region_ids]


    # region_ids = [131, 147, 152, 224, 302]


    for id_ in region_ids:
        print(id_)

        # словарь {команда: id команды}
        cur.execute("""
            SELECT team_id, team_name
            FROM teams
            JOIN season_team_relations USING(team_id)
            JOIN seasons USING(season_id)
            WHERE region_id = %s
            """, (id_,))
        teams = cur.fetchall()
        teams = {team_name: team_id for team_id, team_name in teams}


        # словарь {лига: id лиги}
        cur.execute("""
            SELECT league_id, league_name
            FROM leagues
            WHERE region_id = %s
            """, (id_,))
        leagues = cur.fetchall()
        leagues = {league_name: league_id for league_id, league_name in leagues}
        # print(leagues)


        # для каждого региона получаем список url-ов игравших в нем команд
        cur.execute("""
            SELECT flashscore_team_url
            FROM teams
            JOIN season_team_relations USING(team_id)
            JOIN seasons USING(season_id)
            WHERE region_id = %s
            """, (id_,))
        team_urls = cur.fetchall()
        team_urls = [url[0] for url in team_urls]
        team_urls = list(set(team_urls))


        region_matches = []

        # для каждой комбинации команд находим feed их последней очной игры
        for i in range(len(team_urls)):
            for j in range(i + 1, len(team_urls)):
                url_team_1 = team_urls[i][6:-1].replace('/', '-')
                url_team_2 = team_urls[j][6:-1].replace('/', '-')

                url = f'https://www.flashscore.com/match/football/{url_team_1}/{url_team_2}/?'
                response = get_response(url)

                data = response.text.split('<script>\n    ')
                feed_match = None
                for el in data:
                    if 'window.environment = {"event_id_c":' in el:
                        feed_match = el[36:44]
                        break
                if feed_match is None:
                    continue

                # print(feed_match)
                h2h = get_data('df_hh_1_' + feed_match)

                # идем по всем совместным играм
                KB_count = 0
                for el in h2h:
                    if '~KB' in el.keys(): # аккуратно выделяем нужные нам игры
                        KB_count += 1
                    if KB_count == 3:
                        if '~KB' in el.keys():
                            continue
                        if '~KA' in el.keys():
                            break

                        # print(el)
                        match = [el.get('~KC'), el.get('KP'),
                                 el.get('FH'), el.get('FK'),
                                 el.get('KU'), el.get('KT'),
                                 el.get('KX'), el.get('KY'),
                                 'completed', None, el.get('KF')]

                        try: # если вместо имен команд у нас None, то просто пропускаем этот матч
                            match[2] = teams[match[2]]
                            match[3] = teams[match[3]]
                        except KeyError:
                            continue
                        for ind in [4, 5]: # если счет представляет собой '' '', то заменяем значения на None
                            if match[ind] == '':
                                match[ind] = None
                        try: # если лиги еще нет в бд, то пока просто пропускаем этот матч
                            match[10] = leagues[match[10]]
                        except KeyError:
                            continue
                        # print(match)
                        region_matches.append(match)

        print(len(region_matches), end='\n\n')
        execute_values(cur, query, region_matches)
        conn.commit()

    cur.close()
    conn.close()



def main():

    # на примере загруженных матчей нужно будет научиться определять сезон.ждщшг8н6
    # для initialize_matches нужно будет написать update_matches для быстрого обновления таблицы matches


    conn = psycopg2.connect(host='localhost', dbname='football_data', user='postgres', port=5432, password=1234)
    cur = conn.cursor()


    cur.execute("""
    """)


    conn.commit()
    cur.close()
    conn.close()











if __name__ == '__main__':
    main()
