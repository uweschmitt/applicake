# encoding: utf-8
from __future__ import print_function

import datetime
try:
    import psutil
except ImportError:
    psutil = None
import subprocess
import thread
import time

# mem = lambda process: psutil.Process(process.pid).memory_info()[0] / float(2 ** 20)

def mem(process):
    if psutil is None:
        return -1
    return psutil.Process(process.pid).memory_info()[0] / float(2 ** 20)


def _observer(p, log_fun, delta_t_report=60.0, delta_t_measure=10.0):

    started = datetime.datetime.now()
    mem_start = mem(p)
    log_fun("")
    log_fun("start observation at  : %s", started)
    log_fun("memory at start in mB : %.1f", mem_start)
    log_fun("")
    tic_report = time.time()
    tic_measure = time.time()
    peak_mem = mem_start
    while p.returncode is None:
        time.sleep(.1)
        if time.time() - tic_report > delta_t_report:
            tic_report = time.time()
            run_time = datetime.datetime.now() - started
            peak_mem = max(mem(p), peak_mem)
            log_fun("")
            log_fun("current run time        : %s", run_time)
            log_fun("current mem consumption : %.1f MB", mem(p))
            log_fun("peak mem consumption    : %.1f MB", peak_mem)
            log_fun("")
        if time.time() - tic_measure > delta_t_measure:
            tic_measure = time.time()
            peak_mem = max(mem(p), peak_mem)

    run_time = datetime.datetime.now() - started
    log_fun("")
    log_fun("--------------------------------")
    log_fun("final run time       : %s", run_time)
    log_fun("peak mem consumption : %.1f MB", peak_mem)
    log_fun("--------------------------------")
    log_fun("")


def start_background_observer(p, log_fun, delta_t_report=360.0, delta_t_measure=30.0):
    thread.start_new_thread(_observer, (p, log_fun, delta_t_report, delta_t_measure))

