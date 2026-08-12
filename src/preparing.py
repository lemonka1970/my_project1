from src.database.queries import get_region_id_by_flashscore_id, get_league_id_by_flashscore_feed
from src.database.queries import get_league_id_by_tournaments, get_team_id_by_feed
from src.database.queries import get_season_id_by_tournamnts, get_league_id_by_name
from src.database.queries import resolve_with_retry

import time
from datetime import datetime


def parsing_regions(payload):
    regions = set()

    scoreboard = payload.get('scoreboard', [])
    if scoreboard:
        scoreboard = scoreboard[0]
        
    # выделяем из него регионы и готовим к загрузке
    if scoreboard.get('~ZA') and scoreboard.get('ZB'):
        regions.add((
            scoreboard.get('ZB'), # flashscore_region_id
            scoreboard.get('ZY') # region_name
            ))
        
    return regions



def prepare_leagues(payload, regions):

    leagues = set()

    keys = [
        'ZEE', # flashscore_league_feed
        'ZD', # competition_type
        'ZG', # stage_type
        'ZJ', # category_id
        'ZL', # league_url
        '~ZA', # league_full_name
        'ZB' # flashcore_region_id
        ]


    scoreboard = payload.get('scoreboard', [])
    if scoreboard:
        scoreboard = scoreboard[0]


    # вылавлинваем из json наши лиги
    # и тоговим данные к загрузке в postgres
    if scoreboard.get('~ZA'):

        row = [scoreboard.get(key) for key in keys]
        row[5] = row[5].split(': ')[1]

        # на случай, если какого-то региона у нас не оказалось
        row[6], regions = resolve_with_retry(regions, row[6], get_region_id_by_flashscore_id())

        leagues.add(tuple(row))

    return leagues, regions



def prepare_current_seasons(payload, leagues):

    scoreboard = payload.get('scoreboard', [])
    if scoreboard:
        scoreboard = scoreboard[0]
    current_seasons = set()

    if scoreboard.get('~ZA'):
        
        row = [
            scoreboard.get('ZE'), # tournament_id
            scoreboard.get('ZC'), #  tournament_stage_id
            0, 0, # dates
            True, # is_current
            scoreboard.get('ZEE') # flashscore_league_feed
            ]

        row[5], leagues = resolve_with_retry(leagues, row[5], get_league_id_by_flashscore_feed())

        current_seasons.add(tuple(row))

    return current_seasons, leagues



def prepare_seasons(payload, league_ids):

    past_seasons = payload.get('past_seasons')

    seasons = set()

    # id-шники текушего сезона
    tournament_id = payload.get('tournament_id')
    tournament_stage_id = payload.get('tournament_stage_id')

    # если эту лигу еще не успелли обработать
    league_id, league_ids = resolve_with_retry(league_ids, 
                                               (tournament_id, tournament_stage_id), 
                                               get_league_id_by_tournaments())


    current_row = [tournament_id,
                    tournament_stage_id,
                    0, 0, True,
                    league_id
                    ]

    # правим даты текущего сезона и загружаем и его тоже
    start = int(past_seasons[0]["start"])
    end = int(past_seasons[0]["end"])

    current_row[2] = start + 1
    current_row[3] = end + 1
    seasons.add(tuple(current_row))

    # и проходимся по остальным сезонам
    for el in past_seasons:
        row = [el.get('tournamentId'),
            el.get('tournamentStages').get('other')[0].get('id'),
            el.get('start'),
            el.get('end'),
            False,
            current_row[5],
            ]

        seasons.add(tuple(row))

    return seasons, league_ids



def parsing_teams(payload):

    standings = payload.get('standings', [])
    
    teams = set()

    for el in standings:
        if el.get('~TR'):
            teams.add((
                el.get('TN'), # team_name
                el.get('TI'), # flashscore_team_feed
                el.get('TIU') # flashscore_team_url
                ))

    return teams



def prepare_relations(payload, old_season_tournaments, seasons):

    tournaments = (payload.get('tournament_id'), payload.get('tournament_stage_id'))
    standings = payload.get('standings')

    league_id = get_league_id_by_tournaments().get(tournaments)
    teams = get_team_id_by_feed(league_id)

    if tournaments in old_season_tournaments:
        return None

    relations = set()

    season_id, seasons = resolve_with_retry(seasons, tournaments, get_season_id_by_tournamnts())


    for el in standings:
        team_feed = el.get('TI')
        team_id = None

        team_id, teams = resolve_with_retry(teams, team_feed, get_team_id_by_feed())

        relations.add((
            season_id,
            team_id,
            el.get('TP')
            ))

    return relations, seasons, teams




def parsing_initializetion_matches(payload):

    league_id = payload.get('league_id')
    h2h = payload.get('h2h')

    
    teams = get_team_id_by_feed(league_id)
    league_names = get_league_id_by_name(league_id)
    league_matches = set()


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

        
            match = [
                el.get('~KC'), # time
                el.get('KP'), # flashscore_match_feed
                el.get('UQ'), # home_team_feed
                el.get('UO'), # away_team_feed
                el.get('KU'), # home_score
                el.get('KT'), # away_score
                el.get('KX'), # home_penalties
                el.get('KY'), # away_penalties
                'completed', # status
                None, # season_id
                el.get('KF') # league_name
                ] 

            if match[0] is not None:
                match[0] = datetime.fromtimestamp(int(match[0]))

            # если вместо имен команд у нас None, то просто пропускаем этот матч
            match[2] = teams.get(match[2])
            match[3] = teams.get(match[3])
            # если лиги еще нет в бд, то пока просто пропускаем этот матч
            match[10] = league_names.get(match[10])
            if match[2] is None or match[3] is None or match[10] is None:
                continue

            for ind in [4, 5]: # если счет представляет собой '' '', то заменяем значения на None
                if match[ind] == '':
                    match[ind] = None

            # print(match)
            league_matches.add(tuple(match))

    return league_matches


def parsing_updating_matches(payload):

    league_id = payload.get('league_id')
    season_id = payload.get('season_id')
    h2h = payload.get('h2h')

    teams = get_team_id_by_feed(league_id)
    league_names = get_league_id_by_name(league_id)
    matches = set()


    # заглядываем только в первые 2 блока (последние игры домашней и гостевой команд)
    for el in h2h[:104]:
        if '~KC' in el:
            print(el)
            match = [
                el.get('~KC'), # time
                el.get('KP'), # flashscore_match_feed
                el.get('UQ'), # home_team_feed
                el.get('UO'), # away_team_feed
                el.get('KU'), # home_score
                el.get('KT'), # away_score
                el.get('KX'), # home_penalties
                el.get('KY'), # away_penalties
                'completed', # status
                season_id, # season_id
                el.get('KF') # league_name
            ]

            if match[0] is not None:
                match[0] = datetime.fromtimestamp(int(match[0]))

            # если вместо имен команд у нас None, то просто пропускаем этот матч
            match[2] = teams.get(match[2])
            match[3] = teams.get(match[3])
            # если лиги еще нет в бд, то пока просто пропускаем этот матч
            match[10] = league_names.get(match[10])
            if match[3] is None or match[2] is None or match[10] is None:
                continue

            for ind in [4, 5]:  # если счет представляет собой '' '', то заменяем значения на None
                if match[ind] == '':
                    match[ind] = None


            matches.add(tuple(match))

    return matches, league_names