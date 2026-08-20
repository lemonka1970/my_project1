import json
from datetime import datetime, timezone, timedelta
from src.connections import get_producer




def resolve(cache: dict, key, refresh_func):
    # один раз обновляем cache, если все равно нету нужного нам ключа, 
    # возвращаем none с обновленным словарем

    if cache.get(key) is None:
        cache = refresh_func()
    value = cache.get(key)
    return value, cache


def handle_retry(massege, topic):
    # отправляем massege обратно в свой topic или в dead_masseges, если она израсходавала свои попытки
    
    producer = get_producer()
    payload = massege.get('payload')
    retry_count = massege.get('retry_count')
    time_started_at = datetime.fromisoformat(massege.get('time_started_at'))

    # если с последней попытки прошло больше 2-х минут, то обновляем time_started_at и увеличиваем retry_count
    if timedelta(minutes=2) < datetime.now(timezone.utc) - time_started_at:
        time_started_at = datetime.now(timezone.utc)
        retry_count += 1

    # если retry_count становиться больше определенного уровня, то отправляем его в dead_massege
    if retry_count > 10:
        massege = create_retry_massege(payload)
        producer.produce(
            topic='dead_masseges',
            value=massege
        )
        return

    # если все прошло успешно, кидаем massege дальше по кругу
    massege = create_retry_massege(payload, retry_count, time_started_at)
    producer.produce(
        topic=topic,
        value=massege
    )