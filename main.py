import ast
from datetime import datetime, timedelta
from operator import index
from tkinter.font import names
import torch

import pandas as pd
import numpy as np
from pandas import read_excel
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer




from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from pytorch_tabnet.tab_model import TabNetClassifier
from joblib import dump, load

import time

from predicting_functions import make_sample
from parsing_functions import fetch_upcoming_league_matches, load_data



import warnings
warnings.filterwarnings('ignore')

feeds_standings, names_standings, ids_standings_bk, names_standings_bk, all_teams, league_count = load_data()




def main():



    list_league = [i for i in range(league_count) if i not in []]
    all_list_league = [i for i in range(len(names_standings))]




    # X_train, y = collect_X_y_train_new(None, [])
    #
    y = read_excel('./files/data.xlsx')
    y = y.to_dict(orient='list')
    X_train = list(y['X_train'])
    for i in range(len(X_train)):
        X_train[i] = ast.literal_eval(X_train[i])

    print(X_train)

    # y |= {'X_train': X_train}
    # df = pd.DataFrame(y)
    # df.to_excel('data.xlsx', index=False)

    # X_train = np.array(X_train, dtype='float64')
    # y_names = list(y.keys())
    #
    # for num in range(ready_league_count):
    #     print('\n\n', names_standings[num])
    #     l_rate = 0.05   # float(f'0.05{str(num)}1')
    #     n_est = 200
    #     max_d = 5
    #
    #     for i in range(len(y)):
    #
    #         y[y_names[i]] = np.array(y[y_names[i]], dtype='float64')
    #         # print(y[y_names[j]])
    #
    #         model_GB = XGBClassifier(learning_rate=l_rate, n_estimators=n_est, max_depth=max_d,
    #                                                  random_state=42)
    #
    #         model_GB.fit(X_train, y[y_names[i]])
    #         dump(model_GB, 'gradient_boosting_' + y_names[i] + '_' + str(l_rate) + '_' + str(n_est) + '_' + str(
    #             max_d) + '.joblib')
    #
    #
    #
    #
    #     filename = names_standings[num].replace(' ', '_')
    #
    #     feeds = get_upcoming_feeds_league(num)
    #     y = {'time': [], 'feed': [], 'team1':[], 'team2': [], 'total': [], 'total1': [], 'total2': [], 'win': [], 'doubleChance': [], 'BtS': []}
    #     y_names = list(y.keys())
    #
    #     # импортируем таблицы
    #     data_standings = [[], []]
    #     for year in [i for i in range(1900, 2050)] + ['current']:
    #         try:
    #             for j in range(1, 4):
    #                 df_table = read_excel('all_standings_' + filename + '.xlsx', sheet_name=f'{year}_{j}')
    #                 data_standings[0].append(df_table)
    #                 data_standings[1].append(f'{year}_{j}')
    #         except ValueError:
    #             continue
    #
    #     data_feeds = read_excel('all_feeds_' + filename + '.xlsx')
    #
    #     X_test = []
    #     for feed in feeds:
    #         X_1 = collect_data_x_new(data_feeds, data_standings, feed, 0, 0, num, -1)
    #         X_test.append(np.array(X_1, dtype='float64'))
    #
    #         for i in range(4):
    #             y[y_names[i]].append(feed[i])
    #
    #     for i in range(4, len(y)):
    #         gb = load('gradient_boosting_' + y_names[i] + '_' + str(l_rate) + '_' + str(n_est) + '_' + str(max_d) + '.joblib')
    #         y_test = gb.predict(X_test)
    #         y[y_names[i]] = y_test
    #
    #     df = pd.DataFrame(y)
    #     df.to_excel('predicts_' + filename + '.xlsx', index=False)




    #================
    # модель clf
    #===============
    for num in range(1):
        filename = names_standings[num].replace(' ', '_')
        y = read_excel('data.xlsx')
        X_train_ = list(y['X_train'])
        X_train = [ast.literal_eval(el) for el in X_train_]
        # X_train = pd.DataFrame(X_train, columns=[i for i in range(len(X_train[0]))])

        y_train = []
        for i in range(len(X_train)):
            y_train.append(f'{y['total1'][i]}:{y['total2'][i]}')

        # удаляем новые матчи из датасета
        for i in range(len(X_train)):
            if datetime.fromtimestamp(X_train[i][0]) > datetime.now() - timedelta(days=30):
                del X_train[i]
                del y_train[i]

        X_train = np.array(X_train, dtype='float64')
        y_train = np.array(y_train, dtype='str')
        X_train, X_valid, y_train, y_valid = train_test_split(X_train, y_train, test_size=0.2, random_state=42)
    #
    #     try:
    #
    #         clf = TabNetClassifier(
    #             n_d=24, n_a=24,
    #             n_steps=4,
    #             gamma=1.3,
    #             optimizer_fn=torch.optim.Adam,
    #             optimizer_params=dict(lr=2e-2),
    #             scheduler_params={"step_size": 50, "gamma": 0.9},
    #             scheduler_fn=torch.optim.lr_scheduler.StepLR,
    #             device_name='cuda' if torch.cuda.is_available() else 'cpu'
    #         )
    #
    #
    #         clf.fit(
    #             X_train, y_train,
    #             eval_set=[(X_valid, y_valid)],
    #             eval_metric=['balanced_accuracy'],
    #             max_epochs=200,
    #             patience=20,
    #             batch_size=2048,
    #             virtual_batch_size=512
    #         )
    #
    #         dump(clf, 'clf_' + filename + '.joblib')
    #     except ValueError:
    #         pass

    # # ==================
    # # предсказания на основе clf модели
    # # ==================
    # for num in range(1):
    #
    #     filename = names_standings[num].replace(' ', '_')
    #     try:
    #         clf = load('clf_' + filename + '.joblib')
    #     except FileNotFoundError:
    #         continue
    #
    #     # feeds = get_upcoming_feeds_league(num)
    #     y = {'time': [], 'feed': [], 'team1': [], 'team2': [], 'total': []}
    #     y_names = list(y.keys())
    #
    #     # импортируем таблицы
    #     data_standings = [[], []]
    #     for year in [i for i in range(1900, 2050)] + ['current']:
    #         try:
    #             for j in range(1, 4):
    #                 df_table = read_excel('all_standings_' + filename + '.xlsx', sheet_name=f'{year}_{j}')
    #                 data_standings[0].append(df_table)
    #                 data_standings[1].append(f'{year}_{j}')
    #         except ValueError:
    #             continue
    #
    #     data_feeds = read_excel('all_feeds_' + filename + '.xlsx')
    #
    #     # собираем матчи, на которые, будем делать предсказания
    #     feeds = fetch_upcoming_league_matches(num)
    #     for row_match in feeds:
    #         for idx in range(4):
    #             y[y_names[idx]].append(row_match[idx])
    #     for team in data_feeds.keys():
    #         for i in range(5):
    #             if pd.isna(data_feeds.loc[i, team]):
    #                 continue
    #             row_match = ast.literal_eval(data_feeds.loc[i, team])
    #             if datetime.fromtimestamp(row_match[0]) < datetime.now() - timedelta(
    #                     days=30) or row_match in feeds:
    #                 continue
    #             feeds.append(row_match)
    #             for idx in range(4):
    #                 y[y_names[idx]].append(row_match[idx])
    #
    #     X_test = []
    #     for feed in feeds:
    #         X_1 = make_sample(data_feeds, data_standings, feed, 3, 0, num, -1)
    #         X_test.append(X_1)
    #
    #         # for i in range(4):
    #         #     y[y_names[i]].append(feed[i])
    #
    #     if len(X_test) == 0:
    #         continue
    #     X_test = np.array(X_test, dtype='float64')
    #     y_test = clf.predict(X_test)
    #     y['total'] = y_test
    #
    #     proba = clf.predict_proba(X_test)
    #     for i in range(len(proba)):
    #         proba[i] = [el.round(2) for el in proba[i]]
    #     proba = pd.DataFrame(proba, columns=list(clf.preds_mapper.values()))
    #
    #
    #     df = pd.DataFrame(y)
    #     df = pd.concat([df, proba], axis=1)
    #     df.to_excel('predicts_clf_' + filename + '.xlsx', index=False)

    ##===============
    ## проверка предсказаний
    ##===============
    # for num in range(league_count):
    #     filename = names_standings[num].replace(' ', '_')
    #     best_cost = None
    #     try:
    #         clf = load('clf_' + filename + '.joblib')
    #         best_cost = clf.best_cost
    #     except FileNotFoundError:
    #         continue
    #     predicts = read_excel('predicts_clf_' + filename + '.xlsx')
    #     predicts = predicts.to_dict(orient='list')
    #     predicts |= {'res': ['-'] * len(predicts['time'])}
    #     data_feeds = read_excel('all_feeds_' + filename + '.xlsx')
    #     data_feeds = data_feeds.to_dict(orient='list')
    #
    #
    #
    #     for team in data_feeds.keys():
    #         for j in range(5):
    #             if pd.isna(data_feeds[team][j]):
    #                 continue
    #             row_match = ast.literal_eval(data_feeds[team][j])
    #             if row_match[4] == -1:
    #                 continue
    #
    #             for i in range(len(predicts['time'])):
    #                 if row_match[0] == predicts['time'][i] and row_match[2] == predicts['team1'][i] and row_match[3] == predicts['team2'][i]:
    #                     if f'{row_match[4]}:{row_match[5]}' == predicts['total'][i]:
    #                         predicts['res'][i] = 'win'
    #                     else:
    #                         predicts['res'][i] = 'loss'
    #
    #     win = predicts['res'].count('win')
    #     loss = predicts['res'].count('loss')
    #     print(names_standings[num],best_cost, win, loss)





if __name__ == '__main__':
    main()
