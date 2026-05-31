import json
import requests

import pandas as pd
import numpy as np
from networkx import cd_index
from pandas import read_excel, concat
import ast

from joblib import dump, load

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
# from pytorch_tabnet.tab_model import TabNetClassifier

import time
import datetime
from parsing_functions import load_data


import warnings
warnings.filterwarnings('ignore')

feeds_standings, names_standings, ids_standings_bk, names_standings_bk, all_teams, league_count = load_data()





def generate_prediction(num, ML_method, min_coef = 1.7, control_gap = 0.5, with_predictability = False):


    filename = names_standings[num].replace(' ', '_')

    # all_match_info = read_excel('all_match_info_' + filename + '.xlsx')
    # upcoming_match = [[], []]
    # times = []
    # for i in range(len(all_match_info['total1'])):
    #     if (pd.isna(all_match_info.loc[i, 'total1']) and not bl_test) or bl_test:
    #         upcoming_match[0].append(all_match_info.loc[i, 'team1'])
    #         upcoming_match[1].append(all_match_info.loc[i, 'team2'])
    #         times.append(all_match_info.loc[i, 'time'])

    try:
        old_res = read_excel('predict_adds_total_' + ML_method + '_' + str(min_coef) + '_' + filename + '.xlsx')
        old_match = [list(old_res['team1']), list(old_res['team2']), list(old_res['time'])]
    except FileNotFoundError:
        old_match = [[], [], []]
    to_delete = []

    try:
        pred = read_excel('predict_total_' + ML_method + '_' + filename + '.xlsx')
    except FileNotFoundError:
        print('нет предсказаний ' + filename)
        return

    try:
        coefs = read_excel('adds_total_' + filename + '.xlsx')
    except FileNotFoundError:
        print('нет коэффициентов ' + filename)
        return

    data_match_info = None; data_match_stats = None; data_standings = None; data_feeds_match = None; gb = None
    if with_predictability:
        gb = load('predictability_' + ML_method + '_' + str(min_coef) + '.joblib')
        filename = names_standings[num].replace(' ', '_')

        data_match_info = read_excel('all_match_info_' + filename + '.xlsx')
        data_match_stats = read_excel('all_match_stats_' + filename + '.xlsx')
        data_standings0 = read_excel('standings_' + filename + '.xlsx', sheet_name='overall')
        data_standings1 = read_excel('standings_' + filename + '.xlsx', sheet_name='home')
        data_standings2 = read_excel('standings_' + filename + '.xlsx', sheet_name='away')
        data_standings = [data_standings0, data_standings1, data_standings2]
        data_feeds_match = read_excel('all_feeds_match_' + filename + '.xlsx')

    res_coefs_total = {'feed': [], 'team1': [], 'team2': [], 'time': [], 'total': [], 'ou_type': [], 'team_scope': [], 'odds': [], 'res': []}


    for i in range(len(pred['team1'])): # проходимся по всем матчам в предсказаниях

        pred_row = pred.loc[i]
        feed = pred_row['feeds']
        time_ = pred_row['time']




        # bl = True    # проверяем, является ли рассматриваемый матч незавершенным
        # for j in range(len(upcoming_match[0])):
        #     if pred_row['team1'] == upcoming_match[0][j] and pred_row['team2'] == upcoming_match[1][j]:
        #         time_ = times[j]
        #         bl = False
        #         break
        #
        # if not bl_test:
        #     if bl: # обрабатываем только незавершенные матчи если мы целенаправленно не обрабатываем уже закончившиеся
        #         continue



        total_OU = [[0] * 11 for _ in range(6)]



        index_team1 = all_teams[0].index(pred_row['team1'])
        index_team2 = all_teams[0].index(pred_row['team2'])
        for j in range(len(coefs['team1'])):    # находим в таблице с коэффициентами рассматриваемый матч
            if coefs.loc[j, 'team1'] == all_teams[1][index_team1] and coefs.loc[j, 'team2'] == all_teams[1][index_team2] and coefs.loc[j, 'startTime'] == pred_row['time']:


                for indx in range(len(old_match[0])):   # проверяем, обрабатывался ли ранее этот матч
                    if (all_teams[0][index_team1] == old_match[0][indx]) and (all_teams[0][index_team2] == old_match[1][indx]) and (pred_row['time'] == old_match[2][indx]):
                        # if datetime.datetime.now() - datetime.timedelta(days=30) < datetime.datetime.fromtimestamp(old_match[2][indx]):
                        to_delete.append(indx)
                        break

                for ppp in list(coefs.loc[j])[3:]:  # перепланируем все коэффициенты

                    index = list(coefs.loc[j])[3:].index(ppp)
                    ppp = eval(ppp)

                    if len(ppp[0]) == 2:
                        total_OU[0][index] = ppp[0][0]
                        total_OU[1][index] = ppp[0][1]
                    if len(ppp[1]) == 2:
                        total_OU[2][index] = ppp[1][0]
                        total_OU[3][index] = ppp[1][1]
                    if len(ppp[2]) == 2:
                        total_OU[4][index] = ppp[2][0]
                        total_OU[5][index] = ppp[2][1]


        res_coefs = [] # находим предполагаемые подходящие прогнозы
        markets = []
        for j in range(6):
            if j % 2 == 0:
                cf = total_OU[j]
                for el in cf:
                    if el >= min_coef:
                        res_coefs.append(el)
                        markets.append((cf.index(el) + 1) / 2)
                        break
            else:
                cf = total_OU[j].copy()
                cf.reverse()
                for el in cf:
                    if el >= min_coef or el == cf[-1]:
                        res_coefs.append(el)

                        markets.append((total_OU[j].index(el) + 1) / 2)
                        break

        if len(markets) != 6:
            continue


        team_scopes = [0, 0, 1, 1, 2, 2]
        indices = ['total', 'total', 'total1', 'total1', 'total2', 'total2']
        ou_types = ['O', 'U']

        processed_matches = {}


        for j in range(6):  # сверяемся с предсказаниями и записываем подходящие варианты в словарь
            if j % 2 == 0:
                condition = markets[j] + control_gap < pred_row[indices[j]]
                ou_type_index = 0
            else:
                condition = markets[j] - control_gap > pred_row[indices[j]]
                ou_type_index = 1

            if condition:
                # Создаем ключ для идентификации матча
                match_id = (pred_row['team1'], pred_row['team2'])

                if match_id not in processed_matches:
                    # Если матч еще не обработан, добавляем его в таблицу
                    res_coefs_total['feed'].append(pred_row['feeds'])
                    res_coefs_total['team1'].append(pred_row['team1'])
                    res_coefs_total['team2'].append(pred_row['team2'])
                    res_coefs_total['time'].append(time_)
                    res_coefs_total['total'].append([markets[j]])
                    res_coefs_total['ou_type'].append([ou_types[ou_type_index]])
                    res_coefs_total['team_scope'].append([team_scopes[j]])
                    res_coefs_total['odds'].append([res_coefs[j]])
                    res_coefs_total['res'].append(['-'])

                    # Запоминаем, что матч был обработан
                    processed_matches[match_id] = len(res_coefs_total['team1']) - 1  # Индекс добавленной строки

                else:
                    # Если матч уже был обработан, добавляем новые варианты ставок в существующие списки
                    index = processed_matches[match_id]

                    res_coefs_total['total'][index].append(markets[j])
                    res_coefs_total['ou_type'][index].append(ou_types[ou_type_index])
                    res_coefs_total['team_scope'][index].append(team_scopes[j])
                    res_coefs_total['odds'][index].append(res_coefs[j])
                    res_coefs_total['res'][index].append('-')

    df = pd.DataFrame(res_coefs_total)



    try:
        old_res = read_excel('predict_adds_total_' + ML_method + '_' + str(min_coef) + '_' + filename + '.xlsx')
        to_delete = list(set(to_delete))
        to_delete.sort(reverse=True)
        for indx in to_delete:
            old_res = old_res.drop(indx)
        df = concat([df, old_res], ignore_index=True)
        df.to_excel('predict_adds_total_' + ML_method + '_' + str(min_coef) + '_' + filename + '.xlsx', index=False)

    except FileNotFoundError:
        df.to_excel('predict_adds_total_' + ML_method + '_' + str(min_coef) + '_' + filename + '.xlsx', index=False)








def compare_predictions(num, ML_method, min_coef = 1.7):


    filename = names_standings[num].replace(' ', '_')

    try:
        data_match_info = read_excel('all_match_info_' + filename + '.xlsx')
        predict_adds_total = read_excel('predict_adds_total_' + ML_method + '_' + str(min_coef) + '_' +  filename + '.xlsx')
    except FileNotFoundError:
        return -1

    for i in range(len(predict_adds_total['team1'])): # идем по предсказаниям с коэффициентами и достаем из таблицы всю информацию
        total = eval(predict_adds_total.loc[i, 'total'])
        ou_type = eval(predict_adds_total.loc[i, 'ou_type'])
        team_scope = eval(predict_adds_total.loc[i, 'team_scope'])
        odds = eval(predict_adds_total.loc[i, 'odds'])
        res = eval(predict_adds_total.loc[i, 'res'])
        if res[0] == '-':

            for j in range(len(data_match_info['team1'])): # ищем матч в data_match_info, что бы проверить предсказания
                if predict_adds_total.loc[i, 'team1'] == data_match_info.loc[j, 'team1'] and predict_adds_total.loc[
                    i, 'team2'] == data_match_info.loc[j, 'team2'] and predict_adds_total.loc[i, 'time'] == data_match_info.loc[j, 'time']:

                    # # если проверяются мачти, что уже давно закончились, то на время смотреть не нужно
                    # if not bl_test:
                    #     if not( datetime.datetime.now() - datetime.timedelta(days=15) < datetime.datetime.fromtimestamp(data_match_info.loc[j, 'time']) and datetime.datetime.fromtimestamp(data_match_info.loc[j, 'time']).year == datetime.datetime.now().year):
                    #         continue

                    if pd.isna(data_match_info.loc[j, 'total1']):
                        break

                    for k in range(len(total)):

                        if ou_type[k] == 'O':
                            if team_scope[k] == 0:
                                if data_match_info.loc[j, 'total1'] + data_match_info.loc[j, 'total2'] == total[k]:
                                    res[k] = 'refund'
                                elif data_match_info.loc[j, 'total1'] + data_match_info.loc[j, 'total2'] > total[k]:
                                    res[k] = 'win'
                                else:
                                    res[k] = 'loss'
                            elif team_scope[k] == 1:
                                if data_match_info.loc[j, 'total1'] == total[k]:
                                    res[k] = 'refund'
                                elif data_match_info.loc[j, 'total1'] > total[k]:
                                    res[k] = 'win'
                                else:
                                    res[k] = 'loss'
                            elif team_scope[k] == 2:
                                if data_match_info.loc[j, 'total2'] == total[k]:
                                    res[k] = 'refund'
                                elif data_match_info.loc[j, 'total2'] > total[k]:
                                    res[k] = 'win'
                                else:
                                    res[k] = 'loss'

                        if ou_type[k] == 'U':
                            if team_scope[k] == 0:
                                if data_match_info.loc[j, 'total1'] + data_match_info.loc[j, 'total2'] == total[k]:
                                    res[k] = 'refund'
                                elif data_match_info.loc[j, 'total1'] + data_match_info.loc[j, 'total2'] < total[k]:
                                    res[k] = 'win'
                                else:
                                    res[k] = 'loss'
                            elif team_scope[k] == 1:
                                if data_match_info.loc[j, 'total1'] == total[k]:
                                    res[k] = 'refund'
                                elif data_match_info.loc[j, 'total1'] < total[k]:
                                    res[k] = 'win'
                                else:
                                    res[k] = 'loss'
                            elif team_scope[k] == 2:
                                if data_match_info.loc[j, 'total2'] == total[k]:
                                    res[k] = 'refund'
                                elif data_match_info.loc[j, 'total2'] < total[k]:
                                    res[k] = 'win'
                                else:
                                    res[k] = 'loss'

            predict_adds_total.loc[i, 'res'] = str(res)


    predict_adds_total.to_excel('predict_adds_total_' + ML_method + '_' + str(min_coef) + '_' + filename + '.xlsx', index=False)


    # change_lan_adds(num)




def make_sample(data_feeds, data_standings, feed_row, feed_y, feed_x, num_league, filler):
    X_1 = []

    # подготавливаем необходимые переменные
    filename = names_standings[num_league].replace(' ', '_')
    teams = list(data_feeds.keys())

    # [1761753600, 'WS2gJPxe', 'Dyn. Kyiv', 'Shakhtar Donetsk', 2, 1]
    if feed_row is None:
        feed_row = ast.literal_eval(data_feeds.loc[feed_y, teams[feed_x]])
    time_match = feed_row[0]
    year_league = int((time_match // (60 * 60 * 24 * 365.25)) + 1970)

    # print(feed_row[2], feed_row[3])
    X_1.extend([time_match, num_league])


    # и таблицы 3-х ближайших лет (overall, home и away)
    tables = []
    tm = [-1, 0, 1]
    for i in range(3):
        t = []
        try:
            for j in range(1, 4):
                index_table = data_standings[1].index(f'{year_league + tm[i]}_{j}')
                df_table = data_standings[0][index_table]
                t.append(df_table)
        except ValueError:
            for j in range(1, 4):
                index_table = data_standings[1].index(f'current_{j}')
                df_table = data_standings[0][index_table]
                t.append(df_table)
        tables.append(t)



    # тоталы и номера обеих команд
    st_index_list = []
    for team in [feed_row[2], feed_row[3]]:
        for i in range(3):
            for j in range(1, 4):
                try:
                    st_index = tables[i][j - 1]['team'].loc[tables[i][j - 1]['team'] == team].index.tolist()[0]
                    st_index_list.append(st_index)

                    X_1.extend([int(tables[i][j - 1].loc[st_index, 'total'].split(':')[0]), int(tables[i][j - 1].loc[st_index, 'total'].split(':')[1])])
                except IndexError:
                    st_index_list.append(-1)
                    X_1.extend([filler] * 2)
    X_1.extend(st_index_list)


    # данные от 5 последних матчей
    for team in [feed_row[2], feed_row[3]]:
        for i in range(feed_y + 1, feed_y + 6):

            if pd.isna(data_feeds.loc[i, team]):
                X_1.extend([filler] * 31)
                continue

            # try:
            feed_row5 = ast.literal_eval(data_feeds.loc[i, team])
            # except ValueError:
            #     print(data_feeds.loc[i, team])
            #     feed_row5 = ast.literal_eval(data_feeds.loc[i, team])


            # тоталы этих 5 последних матчей
            X_1.extend([feed_row5[4] + feed_row5[5], feed_row5[4], feed_row5[5],
                        1 if team == feed_row5[2] else 2])

            # тоталы противника и его номера так же в этих 5 последних матчах
            st_index_list_opp = []
            opp = feed_row5[2] if team == feed_row5[3] else feed_row5[3]

            for i_ in range(3):
                for j_ in range(3):
                    try:
                        st_opp = tables[i_][j_]['team'].loc[tables[i_][j_]['team'] == opp].index.tolist()[0]
                        st_index_list_opp.append(st_opp)

                        X_1.extend([int(tables[i_][j_].loc[st_opp, 'total'].split(':')[0]),
                                    int(tables[i_][j_].loc[st_opp, 'total'].split(':')[1])])

                    except IndexError:
                        st_index_list_opp.append(filler)
                        X_1.extend([filler] * 2)

            X_1.extend(st_index_list_opp)


    # тоталы за последние 10/15/20 игр
    total = 0
    ind_total = 0
    opp_total = 0
    for team in [feed_row[2], feed_row[3]]:
        for i in range(feed_y + 1, feed_y + 21):


            try:
                feed_row20 = ast.literal_eval(data_feeds.loc[i, team])
            except (IndexError, ValueError, KeyError):
                if i - feed_y < 10:
                    X_1.extend([filler] * 9)
                elif i - feed_y < 15:
                    X_1.extend([filler] * 6)
                elif i - feed_y < 20:
                    X_1.extend([filler] * 3)
                break


            total += feed_row20[4] + feed_row20[5]
            ind_total += feed_row20[4] if team == feed_row20[2] else feed_row20[5]
            opp_total += feed_row20[4] if team == feed_row20[3] else feed_row20[5]


            if i - feed_y == 10 or i - feed_y == 15 or i - feed_y == 20:
                X_1.extend([total, ind_total, opp_total])

    # if len(X_1) != 384:
    #     print(feed_row, len(X_1), X_1.count(-1))

    return X_1







def build_dataset(num_league, feeds_none, len_f = None, start_f = 0):

    if feeds_none is None:
        feeds_none = []
    X_train = []


    y = {'total': [], 'total1': [], 'total2': [], 'win': [], 'doubleChance': [], 'BtS': []}
    y_names = list(y.keys())

    if num_league is None:
        list_league = [i for i in range(league_count)]
    else:
        list_league = [num_league]

    for num_league in list_league:  # проходимся по каждой лиге
        print(names_standings[num_league])
        filename = names_standings[num_league].replace(' ', '_')

        data_standings = [[], []]
        for year in [i for i in range(1900, 2050)] + ['current']:
            try:
                for j in range(1, 4):
                    df_table = read_excel('all_standings_' + filename + '.xlsx', sheet_name=f'{year}_{j}')
                    data_standings[0].append(df_table)
                    data_standings[1].append(f'{year}_{j}')
            except ValueError:
                continue

        data_feeds = read_excel('all_feeds_' + filename + '.xlsx')

        for j in range(len(data_feeds.keys())):  # перебираем feed-ы матчей и обрабатываем, если они не равны nan
            team = data_feeds.keys()[j]
            # print(team)

            if len_f is None or start_f + len_f > len(data_feeds[team]):
                len_f = len(data_feeds[team]) - start_f - 20



            for i in range(start_f, start_f + len_f):

                feed_row = data_feeds.loc[i, team]
                if pd.isna(feed_row):
                    continue

                feed_row = ast.literal_eval(feed_row)
                feed_row[4] = int(feed_row[4])
                feed_row[5] = int(feed_row[5])

                if feed_row[1] in feeds_none or feed_row[4] == -1:
                    continue

                X_1 = make_sample(data_feeds, data_standings, None, i, j, num_league, -1)
                if len(X_1) != 384:
                    continue

                X_train.append(X_1)

                feeds_none.append(feed_row[1])

                # и сбор результатов
                y['total'].append(feed_row[4] + feed_row[5])
                y['total1'].append(feed_row[4])
                y['total2'].append(feed_row[5])
                win = 0
                if feed_row[4] > feed_row[5]:
                    win = 1
                elif feed_row[4] < feed_row[5]:
                    win = 2
                y['win'].append(win)
                doubleChance = 0
                if feed_row[4] > feed_row[5]:
                    doubleChance = 1
                elif feed_row[4] < feed_row[5]:
                    doubleChance = 2
                y['doubleChance'].append(doubleChance)
                y['BtS'].append(0 if feed_row[4] == 0 or feed_row[5] == 0 else 1)




    print('collect X_train finished')
    print(f'features: {len(X_train)}')
    print(f'samples: {len(X_train[0])}')




    return X_train, y
