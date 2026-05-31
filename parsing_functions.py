import json
import requests
import ast

import pandas as pd
import numpy as np
from pandas import read_excel, concat
import time
import os


import warnings
warnings.filterwarnings('ignore')


def load_data():
    df_st = pd.read_excel('./files/all_standings.xlsx')
    feeds_st = df_st['feed_st']
    names_st = df_st['name_st']
    ids_st_bk = df_st['id_st_bk']
    names_st_bk = df_st['name_st_bk']
    league_c = len(names_st)

    df_teams = pd.read_excel('./files/all_teams.xlsx')
    teams = [list(df_teams['teams_fl']), list(df_teams['teams_bk'])]

    return feeds_st, names_st, ids_st_bk, names_st_bk, teams, league_c


feeds_standings, names_standings, ids_standings_bk, names_standings_bk, all_teams, league_count = load_data()





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





def fetch_upcoming_league_matches(num):
    data = get_data(feeds_standings[num] + '1')
    feeds = []


    for el in data:
        if '~LMS' in list(el.keys())[0]:
            if el.get('~LMS') == '?' and el.get('LME') not in feeds:
                match = [int(el.get('LMC')), el.get('LME'), el.get('LMJ'), el.get('LMK'), -1, -1]
                feeds.append(match)

    return feeds





def update_current_odds():

    url = 'https://line05w.bk6bba-resources.com/events/list?lang=en&version=62413671543&scopeMarket=1600'

    bl_res = False
    response = None
    while not bl_res:
        try:
            response = requests.get(url=url)
            bl_res = True
        except:
            pass

    data = json.loads(response.text)

    for num in range(league_count):
        filename = names_standings[num].replace(' ', '_')

        try:
            old_coefs = read_excel('adds_total_' + filename + '.xlsx')
            old_match = [list(old_coefs['team1']), list(old_coefs['team2'])]
            old_match[0].append('Home')
            old_match[1].append('Away')
        except FileNotFoundError:
            old_match = [['Home'], ['Away']]

        team1 = []
        team2 = []
        fact = []
        startTime = []
        to_delete = []
        for el in data['events']:
            if el.get('sportId') == ids_standings_bk[num]:
                if 'parentId' not in list(el.keys())  and 'matches' not in el.get('name'):

                    for indx in range(len(old_match[0])):
                        if (el.get('team1') == old_match[0][indx]) and (el.get('team2') == old_match[1][indx]):
                            to_delete.append(indx)
                            break

                    fact.append(el.get('id'))
                    team1.append(el.get('team1'))
                    team2.append(el.get('team2'))
                    startTime.append(el.get('startTime'))


        id_total = [[930, 931, 1696, 1697, 1727, 1728, 1730, 1731, 1733, 1734, 1736, 1737, 1739, 1791, 1793, 1794, 1796,
                     1797], [1809, 1810, 1812, 1813, 1815, 1816, 1818, 1819, 1821, 1822, 1824, 1825],
                    [1854, 1871, 1873, 1874, 1880, 1881, 1883, 1884, 1886, 1887, 1893, 1894, 1896, 1887, 1899, 1900]]
        coefs = {'team1': [], 'team2': [], 'startTime': [], '0.5': [], '1': [], '1.5': [], '2': [], '2.5': [], '3': [], '3.5': [], '4': [],
                 '4.5': [], '5': [], '5.5': []}

        for el in data['customFactors']:
            if el.get('e') in fact:
                index = fact.index(el.get('e'))
                coefs['team1'].append(team1[index])
                coefs['team2'].append(team2[index])
                coefs['startTime'].append(startTime[index])

                cf = [[[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []]]
                for i in range(3):
                    for p in el['factors']:
                        if p.get('f') in id_total[i]:
                            cf[int(float(p.get('pt')) * 2 - 1)][i].append(p.get('v'))

                for column in list(coefs.keys())[3:]:
                    coefs[column].append(cf[int(float(column) * 2) - 1])


        df = pd.DataFrame(coefs)



        try:
            old_coefs = read_excel('adds_total_' + filename + '.xlsx')
            to_delete = list(set(to_delete))
            to_delete.sort(reverse=True)
            for indx in reversed(to_delete):
                old_coefs = old_coefs.drop(indx)
            df = concat([df, old_coefs], ignore_index=True)
            df.to_excel('adds_total_' + filename + '.xlsx', index=False)
        except FileNotFoundError:
            df.to_excel('adds_total_' + filename + '.xlsx', index=False)






def fetch_opening_odds():
    url = 'https://line05w.bk6bba-resources.com/events/list?lang=en&version=62413671543&scopeMarket=1600'

    bl_res = False
    response = None
    while not bl_res:
        try:
            response = requests.get(url=url)
            bl_res = True
        except FileNotFoundError:
            pass

    data = json.loads(response.text)

    for num in range(league_count):
        filename = names_standings[num].replace(' ', '_')
        try:
            old_adds = pd.read_excel('opening_adds_' + filename + '.xlsx')
            old_adds = old_adds.to_dict(orient='list')
        except FileNotFoundError:
            old_adds =  {'team1': [], 'team2': [], 'startTime': [], 'openTime':[], '1': [], 'X': [], '2': [], '1X': [], '12': [], 'X2': [],
                'BtS_Yes': [], 'BtS_No': [], 'total_0.5': [], 'total_1': [], 'total_1.5': [], 'total_2': [],
                'total_2.5': [], 'total_3': [], 'total_3.5': [], 'total_4': [], 'total_4.5': [], 'total_5': [],
                'total_5.5': []}


        team1 = []
        team2 = []
        fact = []
        startTime = []
        adds = []
        for el in data['events']:
            if el.get('sportId') == ids_standings_bk[0]:
                if 'parentId' not in list(el.keys()) and 'matches' not in el.get('name'):

                    # проверяем не собраны ли коэффициенты на рассматриваемый матч
                    if el.get('startTime') < time.time():
                        continue
                    bl = False
                    for i in range(len(old_adds['team1'])):
                        if old_adds['team1'][i] == el.get('team1') and old_adds['team2'][i] == el.get('team2') and old_adds['startTime'][i] == el.get('startTime'):
                            bl = True
                            break
                    if bl:
                        continue

                    fact.append(el.get('id'))
                    team1.append(el.get('team1'))
                    team2.append(el.get('team2'))
                    startTime.append(el.get('startTime'))

        # базовые коэффициенты и коэффициенты по тоталам
        ids = [921, 922, 923, 924, 1571, 925, 4241, 4242]
        id_total = [[930, 931, 1696, 1697, 1727, 1728, 1730, 1731, 1733, 1734, 1736, 1737, 1739, 1791, 1793, 1794, 1796,
                     1797], [1809, 1810, 1812, 1813, 1815, 1816, 1818, 1819, 1821, 1822, 1824, 1825],
                    [1854, 1871, 1873, 1874, 1880, 1881, 1883, 1884, 1886, 1887, 1893, 1894, 1896, 1887, 1899, 1900]]

        adds = {'team1': [], 'team2': [], 'startTime': [], 'openTime': [], '1': [], 'X': [], '2': [], '1X': [], '12': [], 'X2': [],
                'BtS_Yes': [], 'BtS_No': [], 'total_0.5': [], 'total_1': [], 'total_1.5': [], 'total_2': [],
                'total_2.5': [], 'total_3': [], 'total_3.5': [], 'total_4': [], 'total_4.5': [], 'total_5': [],
                'total_5.5': []}

        for el in data['customFactors']:
            if el.get('e') in fact:
                index = fact.index(el.get('e'))
                adds['team1'].append(team1[index])
                adds['team2'].append(team2[index])
                adds['startTime'].append(startTime[index])
                adds['openTime'].append(time.time())

                for p in el.get('factors'):
                    if p.get('f') in ids:
                        index = ids.index(p.get('f'))
                        keys_list = list(adds.keys())
                        adds[keys_list[index + 4]].append(p.get('v'))

                cf = [[[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []],
                      [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []], [[], [], []],
                      [[], [], []]]
                for i in range(3):
                    for p in el['factors']:
                        if p.get('f') in id_total[i]:
                            cf[int(float(p.get('pt')) * 2 - 1)][i].append(p.get('v'))

                for column in list(adds.keys())[12:]:
                    adds[column].append(cf[int(float(column[6:]) * 2) - 1])

        df = pd.DataFrame(adds)
        old_df = pd.DataFrame(old_adds)
        df = pd.concat([df, old_df])
        df.to_excel('opening_adds_' + filename + '.xlsx', index=False)







def fetch_league_standings(st):
    """
        Используя feed лиги, парсит 3 таблицы лиги, включая домашнюю и гостевую
        :param st: feed лиги
        :return: список из трех таблиц
    """

    keys_standing = {'standing': '~TR', 'zone': 'TU', 'team': 'TN', 'url': 'TIU', 'match': 'TM',
                     'wins': 'TWR',
                     'draws': 'TDR', 'loss': 'TLR', 'total': 'TG', 'U_total': 'TPF', 'points': 'TP'}

    list_data_teams = []
    keys_st = keys_standing.values()
    inx = ['1', '2', '3']
    for i in inx:
        data_list = get_data(st + i)

        # для каждой таблицы собираем данные в двумерный список
        data_teams = []
        for el in data_list:
            if 'TR' in list(el.keys())[0]:
                data_team = []
                for key in keys_st:
                    data_team.append(el.get(key))
                data_teams.append(data_team)

        list_data_teams.append(data_teams)
    return list_data_teams






def fetch_league_matches(feed_standings):
    """
        По feed-у лиги собирает feed-ы всех предыдущих сезонов этой лиги вместе с годом начала
        :param feed_standings: feed лиги
        :return: 2 массива, feed-ы лиги и года начала
    """

    feed1 = feed_standings.split('_')[1]
    feed2 = feed_standings.split('_')[2]

    standings = []
    starts = []
    url = 'https://2.ds.lsapp.eu/pq_graphql?_hash=lph&tournamentId=' + feed1 + '&tournamentStageId=' + feed2 + '&projectId=2'  # для каждой лиги запрашиваем json-файл с информацией об старых сезонах
    response = get_response(url)
    data = response.json()
    data = data.get('data').get('getTournamentSeasons')
    data = data.get('other')

    for el_ in data:  # убрав все лишнее, вытаскиваем составные части feed-а лиги и собираем из него сам feed
        starts.append(el_.get('start'))
        feed1 = el_.get('tournamentId')
        feed2 = el_.get('tournamentStages').get('other')[0].get('id')
        feed_standings = 'to_' + feed1 + '_' + feed2 + '_'
        standings.append(feed_standings)

    return standings, starts






def initialize_data(num):
    """
        Собирает feed-ы всех игр футбольной лиги на сайте flashscore и сохраняет их в excel-файл.
        Так же отдельно собираются таблицы всех сезонов лиги, в том числе домашние и гостевые
        :param num: индекс лиги в excel-файле all_standings
    """

    keys_standing = {'standing': '~TR', 'zone': 'TU', 'team': 'TN', 'url': 'TIU', 'match': 'TM',
                     'wins': 'TWR',
                     'draws': 'TDR', 'loss': 'TLR', 'total': 'TG', 'U_total': 'TPF', 'points': 'TP'}



    # перебирает все feed-ы лиг и по ним находит все feed-ы прошлых сезонов этих лиг
    filename = names_standings[num].replace(' ', '_')
    standings, starts = fetch_league_matches(feeds_standings[num])
    standings.append(feeds_standings[num])
    starts.append('current')


    print(names_standings[num] + ' finish get st feeds')

    # сбираем все команды собранных сезонов
    teams = []
    urls_teams = []
    for st_i in range(len(standings)):
        st = standings[st_i]

        data_list = get_data(st + '1')  # по feed-у лиги собираем названия команд и ссылки на них
        for el in data_list:
            if '~TR' in el.keys():
                team = el.get('TN')
                url_t = el.get('TIU')
                if team not in teams:
                    teams.append(team)
                    urls_teams.append(url_t)


        # так же парсим таблицы всех сезонов
        inx = ['1', '2', '3']
        list_data_teams = fetch_league_standings(st)
        for i in range(3):
            data_teams =  list_data_teams[i]
            inx_i = inx[i]

            # преобразуем этот двумерный список с dataframe, устанавливая колонками ключи словаря keys_standing
            # и сохраняем в excel-файл отдельной вкладкой с названием f'{год начала сезона}_{1, 2, или 3}'
            df = pd.DataFrame(data_teams, columns=list(keys_standing.keys()))

            if not os.path.exists('all_standings_' + filename + '.xlsx'):
                with pd.ExcelWriter('all_standings_' + filename + '.xlsx') as writer:
                    df.to_excel(writer, sheet_name=f'{starts[st_i]}_{inx_i}', index=False)
            else:
                with pd.ExcelWriter('all_standings_' + filename + '.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=f'{starts[st_i]}_{inx_i}', index=False)




    print(teams)

    feeds_match = {}  # для каждой команды мы в этом словаре запишем список feed-ов ее игр
    for i in range(len(urls_teams) - 1):  # перебираем команды(ссылки на них
        for j in range(i + 1, len(urls_teams)):

            url_team_1 = urls_teams[i][6:-1].replace('/', '-')
            url_team_2 = urls_teams[j][6:-1].replace('/', '-')

            url = f'https://www.flashscore.com/match/football/{url_team_1}/{url_team_2}/?'  # составляем ссылку на матч и находим в полученном html файле feed этого матча
            response = get_response(url)

            data = response.text.split('<script>\n    ')

            feed_match = None  # вытягиваем feed матча
            for el in data:
                if 'window.environment = {"event_id_c":' in el:
                    feed_match = el[36:44]
                    break

            if feed_match is None:
                continue

            data = get_data('df_hh_1_' + feed_match)

            for el in data[105:]:  # проходимся по всем совместным играм этих команд
                if '~KA' in el.keys() and el.get('KF') != names_standings[num].split(' ')[-1].replace('_', ' '):
                    break
                try:
                    # по порядку: feed, дата, команда1, команда2, тотал1, тотал2
                    row_info = [int(el.get('~KC')), el.get('KP'), el.get('FH'), el.get('FK'), int(el.get('KL').split(':')[0]), int(el.get('KL').split(':')[-1])]

                except TypeError:
                    continue
                except ValueError:
                    continue


                for team in [row_info[2], row_info[3]]:  # и заносим их в словарь весь список
                    if team not in feeds_match.keys():
                        feeds_match |= {team: [row_info]}
                    else:
                        feeds_match[team].append(row_info)

            # print(teams[i], teams[j])

    for team in feeds_match.keys():  # проходимся по всем столбцам
        # print(list_)
        for i in range(len(feeds_match[team]) - 1, -1, -1):
            row_match = feeds_match[team][i]
            if row_match[4] == -1 or row_match[2] not in feeds_match.keys() or row_match[3] not in feeds_match.keys():
                del feeds_match[team][i]

        feeds_match[team].sort(reverse=True)  # сортируем по датам


    max_l = 0
    for el in feeds_match:  # равняем словарь, что бы переконвертировать в Dataframe, а затем в excel-таблицу
        if max_l < len(feeds_match[el]):
            max_l = len(feeds_match[el])
    for el in feeds_match:
        feeds_match[el] += [float('nan')] * (max_l - len(feeds_match[el]))

    df = pd.DataFrame(feeds_match)
    df.to_excel('all_feeds_' + names_standings[num].replace(' ', '_') + '.xlsx', index=False)
    print(names_standings[num] + ' finish get feeds match\n')






def update_data(num):
    """
        Обновляет собранные feed-ы всех игр футбольной лиги на сайте flashscore и сохраняет их в excel-файл.
        Так же как и таблицы всех сезонов лиги, в том числе домашние и гостевые
        :param num: индекс лиги в excel-файле all_standings
    """

    keys_standing = {'standing': '~TR', 'zone': 'TU', 'team': 'TN', 'url': 'TIU', 'match': 'TM',
                     'wins': 'TWR',
                     'draws': 'TDR', 'loss': 'TLR', 'total': 'TG', 'U_total': 'TPF', 'points': 'TP'}

    filename = names_standings[num].replace(' ', '_')
    old_feeds = read_excel('all_feeds_' + filename + '.xlsx')
    old_feeds = old_feeds.to_dict(orient='list')


    data = get_data(feeds_standings[num] + '1')
    feeds = {}
    c = 0
    for i in range(len(data)):
        if '~TR' in data[i]:
            feeds |= {data[i].get('TN'): data[i + 1].get('LME')}

    for team in feeds.keys():

        # удаляем незавершенные матчи и матчи с левыми командами
        for i in range(len(old_feeds[team]) - 1, -1, -1):
            if pd.isna(old_feeds[team][i]):
                continue
            row_match = ast.literal_eval(old_feeds[team][i])
            if row_match[4] == -1 or row_match[2] not in old_feeds.keys() or row_match[3] not in old_feeds.keys():
                del old_feeds[team][i]

        # обходим каждую команду по feed-у ее последней игры
        feed_match = feeds[team]
        data = get_data('df_hh_1_' + feed_match)
        if len(data) == 1:
            continue

        # вытаскиваем последние игры данной команды, которых нет в all_feeds

        matches = []
        if team in data[2].get('~KB'):
            start_i = 3
        else:
            start_i = 54

        for el in data[start_i:start_i + 50]:
            if el.get('KF') == names_standings[num].split(' ')[1].replace('_', ' '):
                if el.get('KP') == feed_match:
                    break
                try:
                    match = [int(el.get('~KC')), el.get('KP'), el.get('FH'), el.get('FK'), int(el.get('KL').split(':')[0]), int(el.get('KL').split(':')[-1])]
                    matches.append(match)
                except ValueError:
                    continue

        # и обновляем таблицу, пристраивая их в самый вверх
        old_feeds[team] = matches + old_feeds[team]

    # возвращаем незавершенные игры в начало списка
    data = get_data(feeds_standings[num] + '1')
    for el in data:
        if '~LMS' in list(el.keys()):
            if el.get('~LMS') == '?':
                match = [int(el.get('LMC')), el.get('LME'), el.get('LMJ'), el.get('LMK'), -1, -1]
                if match not in old_feeds[match[2]]:
                    old_feeds[match[2]] = [match] + old_feeds[match[2]]
                if match not in old_feeds[match[3]]:
                    old_feeds[match[3]] = [match] + old_feeds[match[3]]


    # правим длинны и сохраняем
    max_l = 0
    for team in old_feeds.keys():
        if max_l < len(old_feeds[team]):
            max_l = len(old_feeds[team])
    for team in old_feeds.keys():
        old_feeds[team] = old_feeds[team] + [float('nan')] * (max_l - len(old_feeds[team]))

    df = pd.DataFrame(old_feeds)
    df.to_excel('all_feeds_' + filename + '.xlsx', index=False)


    # ну и так же обновляем текущие таблицы
    inx = ['1', '2', '3']
    list_data_teams = fetch_league_standings(feeds_standings[num])
    for i in range(3):
        data_teams = list_data_teams[i]
        inx_i = inx[i]

        # преобразуем этот двумерный список с dataframe, устанавливая колонками ключи словаря keys_standing
        # и сохраняем в excel-файл отдельной вкладкой с названием f'{год начала сезона}_{1, 2, или 3}'
        df = pd.DataFrame(data_teams, columns=list(keys_standing.keys()))
        with pd.ExcelWriter('all_standings_' + filename + '.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=f'current_{inx_i}', index=False)


    # на случай если текущий сезон уже закончился мы постоянно сохраняем таблицы последнего завершившегося сезона
    # много времени это не занимает, так что можно реализовать вот так на отвали
    standings, starts = fetch_league_matches(feeds_standings[num])
    list_data_standings = fetch_league_standings(standings[0])
    inx = ['1', '2', '3']
    for i in range(3):
        data_teams = list_data_standings[i]
        inx_i = inx[i]

        df = pd.DataFrame(data_teams, columns=list(keys_standing.keys()))
        with pd.ExcelWriter('all_standings_' + filename + '.xlsx', engine='openpyxl', mode='a',
                            if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=f'{starts[0]}_{inx_i}', index=False)

