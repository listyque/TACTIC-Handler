#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    engine
    ~~~~~~~

    Core functionality.
"""
import sys
import types
import time
from functools import wraps
from concurrent import futures

from .tasks import Task, MultiTask, ProcessTask, MultiProcessTask
try:
    # needed for type checks for list of tasks
    from .gevent_tasks import GTask, MultiGTask
except ImportError:
    GTask = MultiGTask = None
# TODO method to execute something in gui thread
# TODO should i call multiprocessing.freeze_support() ?
# TODO documentation
# TODO callbacks
# TODO cancel tasks, or stop engine


POOL_TIMEOUT = 0.02


class ReturnResult(Exception):
    """ Exception Used to return result from generator
    """
    def __init__(self, result):
        super(ReturnResult, self).__init__()
        self.result = result


class Engine(object):
    """ Engine base class

    After creating engine instance, set :attr:`main_app` property
    (not needed with PyQt/PySide)

    Decorate generator with :meth:`@async <async>` to execute tasks yielded
    from generator in separate executor and rest operations in GUI thread.

    Subclasses should implement :meth:`update_gui`.
    """
    def __init__(self, pool_timeout=POOL_TIMEOUT):
        """
        :param pool_timeout: time in seconds which GUI can spend in a loop
        """
        self.pool_timeout = pool_timeout
        #: main application instance
        self.main_app = None

    def async(self, func):
        """ Decorator for asynchronous generators.

        Any :class:`Task`, :class:`ProcessTask` or :class:`GTask` yielded from
        generator will be executed in separate thread, process or greenlet
        accordingly. For example gui application can has following button
        click handler::

            engine = PyQtEngine()
            ...
            @engine.async
            def on_button_click():
                # do something in GUI thread
                data = yield Task(do_time_consuming_work, param)
                update_gui_with(data)  # in main GUI thread

        If some task raises :class:`ReturnResult`, it's value will be returned
        .. seealso:: :func:`return_result`
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            gen = func(*args, **kwargs)
            if isinstance(gen, types.GeneratorType):
                return self.create_runner(gen).run()
        return wrapper

    def create_runner(self, gen):
        """ Creates :class:`Runner` instance

        :param gen: generator which returns async tasks

        Can be overridden if you want custom ``Runner``
        """
        return Runner(self, gen)

    def update_gui(self):
        """ Allows GUI to process events

        Should be overridden in subclass
        """
        time.sleep(self.pool_timeout)


class Runner(object):
    """ Internal class that runs tasks returned by generator
    """
    def __init__(self, engine, gen):
        """
        :param engine: :class:`Engine` instance
        :param gen: Generator which yields tasks
        """
        self.engine = engine
        self.gen = gen

    def run(self):
        """ Runs generator and executes tasks
        """
        gen = self.gen
        try:
            task = next(gen)  # start generator and receive first task
        except StopIteration:
            return
        while True:
            try:
                if isinstance(task, (list, tuple)):
                    assert len(task), "Empty tasks sequence"
                    first_task = task[0]
                    if isinstance(first_task, ProcessTask):
                        task = MultiProcessTask(task)
                    elif GTask and isinstance(first_task, GTask):
                        task = MultiGTask(task)
                    else:
                        task = MultiTask(task)

                with task.executor_class(task.max_workers) as executor:
                    if isinstance(task, MultiTask):
                        task = self._execute_multi_task(gen, executor, task)
                    else:
                        task = self._execute_single_task(gen, executor, task)
            except StopIteration:
                break
            except ReturnResult as e:
                gen.close()
                return e.result

    def _execute_single_task(self, gen, executor, task):
        future = executor.submit(task)
        while True:
            try:
                result = future.result(self.engine.pool_timeout)
            except futures.TimeoutError:
                self.engine.update_gui()
            # TODO canceled error
            except Exception:
                return gen.throw(*sys.exc_info())
            else:
                return gen.send(result)

    def _execute_multi_task(self, gen, executor, task):
        if task.unordered:
            results_gen = self._execute_multi_gen_task(gen, executor, task)
            return gen.send(results_gen)

        future_tasks = [executor.submit(t) for t in task.tasks]
        while True:
            if not task.wait(executor, future_tasks, self.engine.pool_timeout):
                self.engine.update_gui()
            else:
                break
        if task.skip_errors:
            results = []
            for f in future_tasks:
                try:
                    results.append(f.result())
                except Exception:
                    pass
        else:
            try:
                results = [f.result() for f in future_tasks]
            except Exception:
                return gen.throw(*sys.exc_info())
        return gen.send(results)

    def _execute_multi_gen_task(self, gen, executor, task):
        unfinished = set(executor.submit(t) for t in task.tasks)
        while unfinished:
            if not task.wait(executor, unfinished, self.engine.pool_timeout):
                self.engine.update_gui()
            done = set(f for f in unfinished if f.done())
            for f in done:
                try:
                    result = f.result()
                except Exception:
                    if not task.skip_errors:
                        raise
                else:
                    yield result
            unfinished.difference_update(done)


def return_result(result):
    """ Allows to return result from generator

    Internally it raises :class:`ReturnResult` exception, so take in mind, that
    it can be catched in catch-all block
    """
    raise ReturnResult(result)
