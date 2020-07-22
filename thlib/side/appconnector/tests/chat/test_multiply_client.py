import multiprocessing
import sys
import os
sys.path.insert(0, os.path.abspath(__file__).replace("\\", "/").rsplit("/", 4)[0])
from appconnector.tests.chat import test_client


def test(connect=False):
    for i in range(100):
        p = multiprocessing.Process(target=test_client.test, kwargs={"connect": connect})
        p.start()


if __name__ == "__main__":
    test(connect=True)
