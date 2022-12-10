
import datetime
import random
import time

def random_sleep_time(min_second:float, max_second:float):
    """Random sleep time

    Args:
        min_second (float): Minimun range to generate.
        max_second (float): Maximun range to generate.
    """    
    random_seconds = random.uniform(min_second,max_second)
    time.sleep(random_seconds)

def get_utc_now_datetime():
    return datetime.datetime.now(tz=datetime.timezone.utc)