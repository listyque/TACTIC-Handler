import multiprocessing
import sys
import os
sys.path.insert(0, os.path.abspath(__file__).replace("\\", "/").rsplit("/", 4)[0])
from appconnector.tests.chat import test_client
from appconnector.tests.chat import test_server


def test(connect=False):
    ps = multiprocessing.Process(target=test_server.test, kwargs={"start": connect})
    ps.start()

    for i in range(100):
        pc = multiprocessing.Process(target=test_client.test, kwargs={"connect": connect})
        pc.start()


if __name__ == "__main__":
    test(connect=True)
