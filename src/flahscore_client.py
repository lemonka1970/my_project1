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

def main():

    c = 0

if __name__ == '__main__':
    main()