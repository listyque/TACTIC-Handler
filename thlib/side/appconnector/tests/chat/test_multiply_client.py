import sys
import os

module_location = os.path.abspath(__file__).replace("\\", "/").rsplit("/", 4)[0]
sys.path.append(module_location)


def test(connect=False):

    from appconnector.tests.chat import test_client
    import multiprocessing
    for i in range(5):
        p = multiprocessing.Process(target=test_client.test, kwargs={"connect": connect})
        p.start()


if __name__ == "__main__":
    test(connect=True)
