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





def get_connection(db_name='football_core'):
    return psycopg2.connect(host='localhost',
                            port=5432,
                            dbname=db_name,
                            user='postgres',
                            password='postgres')





def initialize_database():
    """
    Инициализирует базу данных и таблицы
    """

    conn = get_connection('postgres')
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
    SELECT 1 FROM pg_database WHERE datname = %s
    """, ('football_core', ))

    if cur.fetchone() is None:
        cur.execute("""
        CREATE DATABASE football_core
        """)

    cur.close()
    conn.close()


    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS regions (
    region_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flashscore_region_id INT UNIQUE NOT NULL,
    region_name TEXT UNIQUE NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS leagues (
    league_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flashscore_league_feed VARCHAR(8) UNIQUE NOT NULL,
    competition_type VARCHAR(1) NOT NULL,
    stage_type INT,
    category_id INT NOT NULL,
    league_url TEXT UNIQUE NOT NULL,
    league_name TEXT NOT NULL,
    region_id INT REFERENCES regions(region_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS seasons (
    season_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tournament_id VARCHAR(8) NOT NULL,
    tournament_stage_id VARCHAR(8) NOT NULL,
    start_date INT,
    end_date INT,
    is_current BOOLEAN NOT NULL,
    league_id INT REFERENCES leagues(league_id),
    UNIQUE(tournament_id, tournament_stage_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS teams 
    (
        team_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        team_name TEXT NOT NULL,
        flashscore_team_feed VARCHAR(8) UNIQUE NOT NULL,
        flashscore_team_url TEXT UNIQUE NOT NULL
    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS season_team_relations
    (
        season_id INT NOT NULL REFERENCES seasons (season_id),
        team_id   INT NOT NULL REFERENCES teams (team_id),
        count_matches INT NOT NULL,
        UNIQUE (season_id, team_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS matches (
    match_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    time TIMESTAMP NOT NULL,
    flashscore_match_feed VARCHAR(8) UNIQUE NOT NULL,
    home_team_id INT NOT NULL REFERENCES teams(team_id),
    away_team_id INT NOT NULL REFERENCES teams(team_id),
    home_score INT,
    away_score INT,
    home_penalties INT,
    away_penalties INT,
    status VARCHAR(10),
    season_id INT REFERENCES seasons(season_id),
    league_id INT REFERENCES leagues(league_id)
    )
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_matches_time
    ON matches(time);
    
    CREATE INDEX IF NOT EXISTS idx_matches_home
    ON matches(home_team_id);
        
    CREATE INDEX IF NOT EXISTS idx_matches_away
    ON matches(away_team_id)
    """)


    conn.commit()
    cur.close()
    conn.close()





def fetch_regions():
    """
    Собирает регионы из Flashscore (главная страница на неделю назад и неделю вперед)
    и сохраняет их в таблицу regions.
    """

    query = """
            INSERT INTO regions (flashscore_region_id, region_name)
            VALUES %s
            ON CONFLICT (flashscore_region_id)
            DO NOTHING
    """

    regions = set()

    # с главного табло сайта flashscore грузим страны и регионы и информацию о них
    for day in range(-7, 8):
        feed = f'f_1_{day}_3_ru-kz_1'
        data = get_data(feed)

        for el in data:
            if el.get('~ZA') and el.get('ZB'):
                # ZB: flashscore_region_id
                # ZY: region_name
                regions.add((el.get('ZB'), el.get('ZY')))


    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, query, list(regions))




def fetch_leagues():
    """
    Собирает лиги из Flashscore (главная страница на неделю назад и неделю вперед)
    и сохраняет их в таблицу leagues.
    """

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            query = """
            INSERT INTO leagues (flashscore_league_feed, competition_type, stage_type, category_id, league_url, league_name,
                   region_id)
            VALUES %s
            ON CONFLICT (flashscore_league_feed)
            DO NOTHING
            """

            cur.execute("""
            SELECT region_id, flashscore_region_id
            FROM regions
            """)
            regions = {el[1]: el[0] for el in cur.fetchall()}

            # ZEE: flashscore_league_feed, ZD: compotition_type,
            # ZG: stage_type, ZJ: category_id,
            # ZL: league_url, ~ZA: full_name, ZB: flashscore_region_id
            keys = ['ZEE', 'ZD', 'ZG', 'ZJ', 'ZL', '~ZA', 'ZB']
            leagues = set()

            # из главного табло сайта flashscore грузим все текущие лиги и информацию о них
            # так же из бд берем region_id
            for day in range(-7, 8):

                feed = f'f_1_{day}_3_ru-kz_1'
                data = get_data(feed)
                for el in data:
                    if el.get('~ZA'):

                        row = [el.get(keys[i]) for i in range(len(keys))]
                        row[5] = row[5].split(': ')[1]
                        row[6] = regions.get(int(row[6]))

                        leagues.add(tuple(row))


            execute_values(cur, query, list(leagues))

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()




def fetch_seasons(only_required = False):
    """
    Собирает сезоны из Flashscore (главная страница на неделю назад и неделю вперед)
    и сохраняет их в таблицу seasons.
    """

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            query = """
                INSERT INTO seasons (tournament_id, tournament_stage_id, start_date, end_date, is_current, league_id)
                VALUES %s
                ON CONFLICT (tournament_id, tournament_stage_id)
                DO UPDATE SET
                is_current = EXCLUDED.is_current
                """

            # id лиги по его feed-у
            cur.execute("""
            SELECT league_id, flashscore_league_feed
            FROM leagues
            """)
            leagues = {el[1]: el[0] for el in cur.fetchall()}

            # выбираем лиги, матчи которых, по сезонам распределены
            required_leagues = set()
            if only_required:
                cur.execute("""
                SELECT DISTINCT league_id
                FROM matches
                WHERE season_id IS NOT NULL
                """)
                required_leagues = {el[0] for el in cur.fetchall()}

            current_seasons = set()
            seasons = set()

            # из главного табло сайта flashscore загружаем текущие сезоны и информацию о них
            # так же из бд берем league_id
            for day in range(-7, 8):
                feed = f'f_1_{day}_3_ru-kz_1'
                data = get_data(feed)
                for el in data:
                    if '~ZA' in el.keys():

                        # ZE: tournament_id
                        # ZC: tournament_stage_id
                        # ZEE: flashscore_league_feed
                        # dates: 0, 0
                        # is_current: True
                        row = [el.get('ZE'), el.get('ZC'), 0, 0, True, el.get('ZEE')]
                        row[5] = leagues.get(row[5])

                        current_seasons.add(tuple(row))


            # для каждого текущего сезона загружаем все его предшествующие
            for current_row in map(list, current_seasons):
                if current_row[0] == '0':
                    continue

                if only_required and current_row[5] not in required_leagues:
                    continue

                url = f'https://2.ds.lsapp.eu/pq_graphql?_hash=lph&tournamentId={current_row[0]}&tournamentStageId={current_row[1]}&projectId=2'
                response = get_response(url)
                data = response.json().get('data').get('getTournamentSeasons').get('other')
                if len(data) == 0:
                    continue

                # правим даты текущего сезона и загружаем и его тоже
                start = int(data[0]["start"])
                end = int(data[0]["end"])

                current_row[2] = start + 1
                current_row[3] = end + 1
                seasons.add(tuple(current_row))


                for el in data:
                    row = [el.get('tournamentId'),
                           el.get('tournamentStages').get('other')[0].get('id'),
                           el.get('start'),
                           el.get('end'),
                           False,
                           current_row[5],
                           ]

                    seasons.add(tuple(row))

            # print(seasons)
            execute_values(cur, query, list(seasons))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()





def fetch_teams():
    """
    Собирает команды по таблицам инициализированных сезонов из Flashscore
    и сохраняет в таблицу teams
    """

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            query = """
            INSERT INTO teams (team_name, flashscore_team_feed, flashscore_team_url)
            VALUES %s
            ON CONFLICT (flashscore_team_feed, flashscore_team_url)
            DO NOTHING
            """

            # запрашиваем все feed сезонов
            cur.execute("""
            SELECT tournament_id, tournament_stage_id
            FROM seasons
            """)
            season_feeds = [f'to_{el[0]}_{el[1]}_1' for el in cur.fetchall()]

            # собираем все команды, игравшие в наших лигах
            teams = set()

            for st_feed in season_feeds:
                standings = get_data(st_feed)
                for el in standings:
                    if el.get('~TR'):
                        # TN: team_name
                        # TI: flashscore_team_feed
                        # TIU: flashscore_team_url
                        teams.add((el.get('TN'), el.get('TI'), el.get('TIU')))

            execute_values(cur, query, list(teams))
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()







def build_season_team_relations():
    """

    """

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            query = """
            INSERT INTO season_team_relations (season_id, team_id)
            VALUES (%s)
            ON CONFLICT
            DO NOTHING
            """

            # собираем id и feed всех сезонов
            cur.execute("""
                SELECT season_id, tournament_id, tournament_stage_id
                FROM seasons
                """)
            data = [[el[0], f'to_{el[1]}_{el[2]}_1'] for el in cur.fetchall()]

            # уже обработанные сезоны
            cur.execute("""
            SELECT DISTINCT(season_id)
            FROM season_team_relations
            """)
            old_season_ids = [el[0] for el in cur.fetchall()]

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
                    if el.get('~TR'):
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

    except Exception:
        raise





def initialize_matches():
    conn = psycopg2.connect(host='localhost', dbname='football_data', user='postgres', port=5432, password=1234)
    cur = conn.cursor()

    query = """
    INSERT INTO matches (time, flashscore_match_feed, 
                        home_team_id, away_team_id, 
                        home_score, away_score, 
                        home_penalties, away_penalties,
                        status, season_id, region_id)
    VALUES (%s)
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

    fetch_seasons()






if __name__ == '__main__':
    main()
