import requests
import numpy as np
import time



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
            response.raise_for_status()
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
            response_.raise_for_status()
            bl_ = False
        except:
            pass
    return response_



def get_feed_last_match(url_team_1, url_team_2):

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
        return None

    return feed_match



def main():

    c = 0

if __name__ == '__main__':
    main()