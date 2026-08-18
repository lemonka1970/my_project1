import requests
import logging
import time
import math

logger = logging.getLogger("my_project.flashscore")

HEADERS = {"x-fsign": "SW9D1eZo"}


def sleep_with_backoff(attempt: int):
    spleep_time = math.ceil(attempt / 4)
    time.sleep(spleep_time)




def get_data(feed):
    """
    Получает данные с Flashscore API и парсит их из кастомного формата.
    :param feed: Идентификатор данных
    :return: list[dict]: Список словарей с данными
    """

    response = None
    max_attempts = 20
    attempt = 1

    url = f'https://global.flashscore.ninja/2/x/feed/{feed}'

    while True:

        sleep_with_backoff(attempt)
        try:
            response = requests.get(url=url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            logger.warning("get_data: попытка %d/%d для url=%s не удалась", attempt, max_attempts, url)
            if attempt > max_attempts:
                logger.error("get_data: url=%s не доступен %s", url, e)
                return []
            attempt += 1


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
    max_attempts = 20
    attempts = 1
    while True:

        sleep_with_backoff(attempts)
        try:
            response_ = requests.get(url_, headers=HEADERS, timeout=10)
            response_.raise_for_status()
            break
        except requests.RequestException as e:
            logger.warning("get_response: попытка %d/%d для url=%s не удалась", attempts, max_attempts, url_)
            if attempts > max_attempts:
                logger.error("get_response: url:%s не доступен %s", url_, e)
                return None
            attempts += 1
            pass
    return response_



def get_feed_last_match(url_team_1, url_team_2):

    url = f'https://www.flashscore.com/match/football/{url_team_1}/{url_team_2}/?'
    response = get_response(url)
    if not response:
        logger.error("get_feed_last_match: страница для %s не была получена", url)
        return None


    # максимально простым способом достаем feed игры
    data = response.text.split('<script>\n    ')
    feed_match = None
    for el in data:
        if 'window.environment = {"event_id_c":' in el:
            el = el.split('window.environment = {"event_id_c":"')[1]
            feed_match = el[:8]
            break
    if feed_match is None:
        logger.error("get_feed_last_match: не был найден feed для %s", url)
        return None

    return feed_match



def main():
    c = 0
    

if __name__ == '__main__':
    main()