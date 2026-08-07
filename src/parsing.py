

import pandas as pd
import numpy as np


from datetime import datetime
from itertools import combinations

from flahscore import get_data, get_response
from connections import get_connection
from psycopg2.extras import execute_values









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


    with get_connection as conn:
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




def fetch_seasons():
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
            ON CONFLICT (flashscore_team_feed)
            DO NOTHING
            """

            # запрашиваем все feed сезонов
            cur.execute("""
            SELECT tournament_id, tournament_stage_id
            FROM seasons
            """)
            season_feeds = [f'to_{tournament_Id}_{tournament_stage_Id}_1' for tournament_Id, tournament_stage_Id in cur.fetchall()]

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
    Перебираем все инициализированные сезоны и запросом Flashscore получаем набор команд
    с количеством ими отыгранных матчей для каждого сезона
    и сохраняем каждое такое отношение в таблицу season_team_relations
    """

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            query = """
            INSERT INTO season_team_relations (season_id, team_id, count_matches)
            VALUES %s
            ON CONFLICT (season_id, team_id)
            DO UPDATE SET
            count_matches = EXCLUDED.count_matches
            """

            # собираем id и feed всех сезонов
            cur.execute("""
                SELECT season_id, tournament_id, tournament_stage_id
                FROM seasons
                """)
            seasons = [[season_id, f'to_{tournament_id}_{tournament_stage_id}_1']
                       for season_id, tournament_id, tournament_stage_id in cur.fetchall()]

            # уже обработанные сезоны, кроме двух последних
            cur.execute("""
            WITH unique_seasons AS (
                SELECT DISTINCT season_id
                FROM season_team_relations
            ),
            seasons_q AS (
                SELECT
                    s.season_id,
                    s.league_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.league_id
                        ORDER BY s.start_date DESC
                    ) AS num
                FROM unique_seasons us
                JOIN seasons s USING (season_id)
            )
            SELECT season_id
            FROM seasons_q
            WHERE num > 2;
            """)
            old_season_ids = set(season_id for season_id in cur.fetchall())

            # вытаскиваем айдишники команд
            cur.execute("""
            SELECT team_id, flashscore_team_feed
            FROM teams
            """)
            teams = {team_feed: team_id for team_id, team_feed in cur.fetchall()}

            season_team = set()

            # для каждого сезона собираем feed команд в них игравших,
            # получаем по ним их id и загружаем (season_id, team_id)
            for season_id, st_feed in seasons:
                if season_id in old_season_ids:
                    continue

                standings = get_data(st_feed)
                for el in standings:
                    if el.get('~TR') and el.get('TI'):

                        # TI: flashscore_teem_feed
                        # TP: count_matches
                        season_team.add((season_id,
                                         teams.get(el.get('TI')),
                                         el.get('TP'))
                                        )

            execute_values(cur, query, season_team)

        conn.commit()


    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()





def initialize_matches():
    """
    Пробегаемся по инициализированным лигам и комбинированием команд в этих лигах игравших
    собираем историю очных встреч этих комбинаций из Flashscore
    """

    conn = get_connection()

    try:

        with conn.cursor() as cur:


            query = """
            INSERT INTO matches (time, flashscore_match_feed, 
                                home_team_id, away_team_id, 
                                home_score, away_score, 
                                home_penalties, away_penalties,
                                status, season_id, league_id)
            VALUES %s
            ON CONFLICT (flashscore_match_feed)
            DO NOTHING
            """

            # получаем id всех регионов
            cur.execute("""
            SELECT region_id
            FROM regions
            """)
            region_ids = cur.fetchall()
            region_ids = [id_[0] for id_ in region_ids]


            region_ids = [33]


            for region_id in region_ids:
                print(region_id)

                # словарь {команда: id команды}
                cur.execute("""
                    SELECT team_id, team_name
                    FROM teams
                    JOIN season_team_relations USING(team_id)
                    JOIN seasons USING(season_id)
                    JOIN leagues USING(league_id)
                    WHERE region_id = %s
                    """, (region_id,))
                teams = cur.fetchall()
                teams = {team_name: team_id for team_id, team_name in teams}


                # словарь {лига: id лиги}
                cur.execute("""
                    SELECT league_id, flashscore_league_feed
                    FROM leagues
                    WHERE region_id = %s
                    """, (region_id,))
                leagues = {league_name: league_id for league_id, league_name in cur.fetchall()}
                # print(leagues)

                region_matches = set()

                for league_id in leagues.values():

                    # для каждой лиги получаем список url-ов игравших в нем команд
                    cur.execute("""
                        SELECT DISTINCT flashscore_team_url
                        FROM teams
                        JOIN season_team_relations USING(team_id)
                        JOIN seasons USING(season_id)
                        WHERE league_id = %s
                        """, (league_id,))
                    team_urls = [url[0] for url in cur.fetchall()]


                    # для каждой комбинации команд находим feed их последней очной игры
                    for url_team_1, url_team_2 in combinations(team_urls, 2):
                        url_team_1 = url_team_1[6:-1].replace('/', '-')
                        url_team_2 = url_team_2[6:-1].replace('/', '-')

                        url = f'https://www.flashscore.com/match/football/{url_team_1}/{url_team_2}/?'
                        response = get_response(url)


                        # максимально простым способом достаем feed игры
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
                            if el.get('~KB'): # аккуратно выделяем нужные нам игры
                                KB_count += 1
                            if KB_count == 3: # в третьей секции находятся все очные встречи
                                if '~KB' in el.keys():
                                    continue
                                if '~KA' in el.keys():
                                    break

                                print(el)
                                match = [el.get('~KC'), # time
                                         el.get('KP'), # flashscore_match_feed
                                         el.get('FH'), # home_team
                                         el.get('FK'), # away_team
                                         el.get('KU'), # home_score
                                         el.get('KT'), # away_score
                                         el.get('KX'), # home_penalties
                                         el.get('KY'), # away_penalties
                                         'completed', # status
                                         None, # season_id
                                         el.get('KF')] # league_name

                                # если вместо имен команд у нас None, то просто пропускаем этот матч
                                match[2] = teams.get(match[2])
                                match[3] = teams.get(match[3])
                                # если лиги еще нет в бд, то пока просто пропускаем этот матч
                                match[10] = leagues.get(match[10])
                                if match[2] is None or match[3] is None or match[10] is None:
                                    continue

                                for ind in [4, 5]: # если счет представляет собой '' '', то заменяем значения на None
                                    if match[ind] == '':
                                        match[ind] = None

                                # print(match)
                                region_matches.add(tuple(match))

                print(len(region_matches), end='\n\n')
                execute_values(cur, query, list(region_matches))
        conn.commit()


    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()





def update_matches():
    """
    Загружает новые матчи для текущих и предыдущих сезонов.

    Для каждой лиги формирует пары команд, получает H2H feed через Flashscore
    и сохраняет отсутствующие матчи в таблицу matches.
    """
    conn = get_connection()

    try:
        with conn.cursor() as cur:

            query = """
            INSERT INTO matches (time, flashscore_match_feed, 
                                home_team_id, away_team_id, 
                                home_score, away_score, 
                                home_penalties, away_penalties,
                                status, season_id, league_id)
            VALUES %s
            ON CONFLICT (flashscore_match_feed)
            DO NOTHING
            """

            # проходимся отдельно по каждой лиге
            cur.execute("""
            SELECT region_id
            FROM regions
            """)
            region_ids = [el[0] for el in cur.fetchall()]
            region_ids = [33]

            for region_id in region_ids:

                # собираем все команды и отношения команд с сезонами
                cur.execute("""
                    SELECT season_id, team_id
                    FROM season_team_relations
                    JOIN seasons USING(season_id)
                    WHERE region_id = %s
                    """, (region_id,))
                df_relations = pd.DataFrame(cur.fetchall(), columns=['season_id', 'team_id'])

                cur.execute("""
                    SELECT DISTINCT team_id, flashscore_team_url
                    FROM teams
                    JOIN season_team_relations USING(team_id)
                    JOIN seasons USING(season_id)
                    WHERE region_id = %s
                    """, (region_id, ))
                df_teams = pd.DataFrame(cur.fetchall(), columns=['team_id', 'flashscore_team_url'])

                # словарь {команда: id команды}
                cur.execute("""
                    SELECT DISTINCT team_id, flashscore_team_feed
                    FROM teams
                    JOIN season_team_relations USING(team_id)
                    JOIN seasons USING(season_id)
                    WHERE region_id = %s
                    """, (region_id, ))
                teams = {team_feed: team_id for team_id, team_feed in cur.fetchall()}

                # словарь {лига: id лиги}
                cur.execute("""
                    SELECT league_id, league_name
                    FROM leagues
                    WHERE region_id = %s
                    """, (region_id, ))
                leagues = {league_name: league_id for league_id, league_name in cur.fetchall()}

                # берем текущий и предыдущий сезоны каждой лиги
                cur.execute("""
                    WITH cur_seasons AS (
                        SELECT
                            region_id,
                            league_id,
                            season_id,
                            ROW_NUMBER() OVER (
                                PARTITION BY league_id
                                ORDER BY start_date DESC
                            ) AS season_num
                        FROM seasons
                        JOIN leagues USING(league_id)
                    )
                    SELECT league_id, season_id, season_num
                    FROM cur_seasons
                    WHERE region_id = %s
                      AND season_num IN (1, 2)
                    """, (region_id, ))
                df_last_seasons = pd.DataFrame(
                    cur.fetchall(),
                    columns=['league_id', 'season_id', 'season_num']
                )

                matches = set()

                # для каждой лиги собираем все url-ы команд текущего и предыдущего сезонов
                for league_id in set(df_last_seasons['league_id']):

                    league_seasons = df_last_seasons[
                        df_last_seasons['league_id'] == league_id
                    ]

                    season_ids = league_seasons['season_id'].tolist()

                    current_season_id = int(
                        league_seasons.loc[
                            league_seasons['season_num'] == 1,
                            'season_id'
                        ].iloc[0]
                    )

                    team_ids = list(df_relations[df_relations['season_id'].isin(season_ids)]['team_id'])
                    team_urls = list(df_teams[df_teams['team_id'].isin(team_ids)]['flashscore_team_url'])
                    if not team_urls:
                        continue

                    # формируем пары и находим feed их последней очной встречи
                    url_pairs = []
                    for i in range(0, len(team_urls), 2):
                        url_pairs.append((team_urls[i], team_urls[(i + 1) % len(team_urls)]))

                    for pair in url_pairs:
                        url_team_1 = pair[0][6:-1].replace('/', '-')
                        url_team_2 = pair[1][6:-1].replace('/', '-')

                        url = f'https://www.flashscore.com/match/football/{url_team_1}/{url_team_2}/?'
                        response = get_response(url)


                        # максимально простым способом достаем feed игры
                        data = response.text.split('<script>\n    ')
                        feed_match = None
                        for el in data:
                            if 'window.environment = {"event_id_c":' in el:
                                feed_match = el[36:44]
                                break
                        if feed_match is None:
                            continue


                        h2h = get_data('df_hh_1_' + feed_match)

                        # заглядываем только в первые 2 блока (последние игры домашней и гостевой команд)
                        for el in h2h[:104]:
                            if '~KC' in el:
                                print(el)
                                match = [
                                    el.get('~KC'), # time
                                    el.get('KP'), # flashscore_match_feed
                                    el.get('UQ'), # home_team
                                    el.get('UO'), # away_team
                                    el.get('KU'), # home_score
                                    el.get('KT'), # away_score
                                    el.get('KX'), # home_penalties
                                    el.get('KY'), # away_penalties
                                    'completed', # status
                                    current_season_id, # season_id
                                    el.get('KF') # league_name
                                ]

                                if match[0] is not None:
                                    match[0] = datetime.fromtimestamp(int(match[0]))

                                # если вместо имен команд у нас None, то просто пропускаем этот матч
                                match[2] = teams.get(match[2])
                                match[3] = teams.get(match[3])
                                # если лиги еще нет в бд, то пока просто пропускаем этот матч
                                match[10] = leagues.get(match[10])
                                if match[3] is None or match[2] is None or match[10] is None:
                                    continue

                                for ind in [4, 5]:  # если счет представляет собой '' '', то заменяем значения на None
                                    if match[ind] == '':
                                        match[ind] = None


                                matches.add(tuple(match))


                # execute_values(cur, query, list(matches))
        conn.commit()


    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()





def main():

    x = 9

            




if __name__ == '__main__':
    main()
