"""
    gevent_tasks
    ~~~~~~~~~~~~

    Tasks executing in ``gevent`` Pool

    .. note:: You need to apply gevent monkey-patch yourself, see
      `docs <http://www.gevent.org/gevent.monkey.html>`_

"""
from concurrent import futures
from gevent.pool import Pool
import gevent

from .tasks import Task, MultiTask


# TODO docs about monkey_patch
class GeventPoolExecutor(futures.Executor):
    """ Wrapper for `gevent.pool.Pool`
    """

    def __init__(self, max_workers):
        self.max_workers = max_workers
        self._pool = Pool(max_workers)

    def submit(self, fn, *args, **kwargs):
        greenlet = self._pool.spawn(fn, *args, **kwargs)
        return GeventFuture(greenlet)

    def shutdown(self, wait=True):
        self._pool.kill(block=wait)


# TODO more greenlet methods, also check not overridden Future methods
class GeventFuture(futures.Future):
    """ Wrapper for `Greenlet`
    """
    def __init__(self, greenlet):
        super(GeventFuture, self).__init__()
        #self._greenlet = gevent.Greenlet()
        self._greenlet = greenlet

    def result(self, timeout=None):
        try:
            return self._greenlet.get(timeout=timeout)
        except gevent.Timeout as e:
            raise futures.TimeoutError(e)

    def exception(self, timeout=None):
        # todo timeout
        return self._greenlet.exception

    def running(self):
        return not self.done()

    def done(self):
        return self._greenlet.ready()


class GTask(Task):
    """ Task executed in `gevent` Pool
    """
    executor_class = GeventPoolExecutor


class MultiGTask(MultiTask):
    """ Multiple tasks executed in `gevent` Pool simultaneously
    """
    executor_class = GeventPoolExecutor

    def wait(self, executor, spawned_futures, timeout=None):
        executor._pool.join(timeout)
        return all(f.done() for f in spawned_futures)
