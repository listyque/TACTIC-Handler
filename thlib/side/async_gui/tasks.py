#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    tasks
    ~~~~~

    Contains task classes which when yilded from async generator will be
    executed in thread pool, or process pool
"""
import multiprocessing
from concurrent import futures


class Task(object):
    """ Represents single async operation.

    Accepts callable and optionally its ``args`` and ``kwargs``::

        result = yield Task(time_consuming_operation, arg, some_kwarg=1)
    """

    #: Executor class (from `concurrent.futures`) overridden in subclasses
    #: default is `ThreadPoolExecutor`
    executor_class = futures.ThreadPoolExecutor
    #: Maximum number of workers, mainly used in MultiTask
    max_workers = 1

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def start(self):
        return self.func(*self.args, **self.kwargs)

    __call__ = start

    def __repr__(self):
        return ('<%s(%s, %r, %r)>' %
                (self.__class__.__name__, self.func.__name__,
                 self.args, self.kwargs))


class ProcessTask(Task):
    """ Task executed in separate process pool
    """
    executor_class = futures.ProcessPoolExecutor


class MultiTask(Task):
    """ Tasks container, executes passed tasks simultaneously in ThreadPool
    """
    def __init__(self, tasks, max_workers=None, skip_errors=False,
                 unordered=False):
        """
        :param tasks: list/tuple/generator of tasks
        :param max_workers: number of simultaneous workers,
                            default is number of tasks
        :param skip_errors: if True, tasks which raised exceptions will not be
                            in resulting list/generator
        :param unordered: if True, result will be returned as  generator,
                            which yields task's results as it's ready.
        """
        self.tasks = list(tasks)
        self.max_workers = max_workers if max_workers else len(self.tasks)
        self.skip_errors = skip_errors
        self.unordered = unordered

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self.tasks)

    def wait(self, executor, spawned_futures, timeout=None):
        """ Return True if all tasks done, False otherwise
        """
        return not futures.wait(spawned_futures, timeout).not_done


class MultiProcessTask(MultiTask):
    """ Tasks container, executes passed tasks simultaneously in ProcessPool
    """
    executor_class = futures.ProcessPoolExecutor

    def __init__(self, tasks, max_workers=None, skip_errors=False, **kwargs):
        """
        Same parameters as :class:`MultiTask` but one is different:

        :param max_workers: number of simultaneous workers,
                            default is number of CPU cores
        """
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        super(MultiProcessTask, self).__init__(
            tasks, max_workers, skip_errors, **kwargs
        )
