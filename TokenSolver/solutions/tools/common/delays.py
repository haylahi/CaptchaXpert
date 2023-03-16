import random
import sys
import time

if sys.platform == 'win32':
    pass


class TimeoutException(Exception):
    pass


class Delay:

    def __init__(self, verbose=False):
        self.is_verbose = verbose
        self.very_small_delay = self.one100_one1000
        self.small_delay = self.one10_one
        self.medium_delay = self.one_3
        self.long_delay = self.five_10
        self.very_long_delay = self.ten_15

    def _sleep(self, secs):
        if self.is_verbose:
            print(f"Sleeping for {secs}s")
        time.sleep(secs)

    def one100_one1000(self):
        """Sleep Program for Random Between 0.001 - 0.01 seconds"""
        self._sleep(random.randint(1, 10) / 1000)

    def random_delay(self):
        """Sleep program for either very small delay or small delay or medium delay"""
        x = random.choice([1, 2, 3])
        self.very_small_delay() if x == 1 else self.small_delay() if x == 2 else self.medium_delay()

    def one10_one(self):
        """Sleep Program for Random Between 0.1 - 1 seconds"""
        self._sleep(random.randint(100, 1000) / 1000)

    def one_3(self):
        """Sleep Program for Random Between 1 - 3 seconds"""
        self._sleep(random.randint(1000, 3000) / 1000)

    def five_10(self):
        """Sleep Program for Random Between 5 - 10 seconds"""
        self._sleep(random.randint(5000, 1000) / 1000)

    def ten_15(self):
        """Sleep Program for Random Between 10 - 15 seconds"""
        self._sleep(random.randint(10000, 15000) / 1000)

    def btw(self, _min, _max):
        """Sleep Program for Random Between min - max seconds"""
        self._sleep(random.randint(_min * 100, _max * 100) / 100)

    def custom(self, secs):
        """Sleep program for time 't'"""
        self._sleep(secs)
