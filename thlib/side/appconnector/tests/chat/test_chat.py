import sys
import os

module_location = os.path.abspath(__file__).replace("\\", "/").rsplit("/", 4)[0]
sys.path.append(module_location)


def test(connect=False):

    from appconnector.tests.chat import test_client
    from appconnector.tests.chat import test_server
    import multiprocessing

    ps = multiprocessing.Process(target=test_server.test, kwargs={"start": connect})
    ps.start()

    pc = multiprocessing.Process(target=test_client.test, kwargs={"connect": connect})
    pc.start()


if __name__ == "__main__":
    test(connect=True)
