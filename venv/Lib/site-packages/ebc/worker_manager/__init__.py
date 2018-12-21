import functools
import signal
import subprocess
import sys
import threading
import time
import traceback

__all__ = ['run']

_POLL_INTERVAL = 0.1
_SIGTERM_TIMEOUT = 15
_MONITOR_THREAD_TIMEOUT = 5


def run(worker_config):
    '''Run a set of processes defined by `worker-config`

    .. note:: Example Configuration

        {
            'manager': {
                'num_workers': 1,
                'cmd': ['python', 'launcher_manager.py']
            },
            'http_server': {
                'num_workers': 1,
                'cmd': ['gunicorn',
                        '-c', './assets/gunicorn_conf.py',
                        'launcher_http_server:server.app']
            },
            'tcp_server': {
                'num_workers': os.environ.get('TCP_SERVER_NUM_WORKERS', 1),
                'cmd': ['python', 'launcher_tcp_server.py']
            }
        }
    '''

    term_signal = signal.Signals.SIGTERM
    term_event = threading.Event()

    def _signal_handler(signum, frame):
        if term_event.is_set():
            print('Forced termination of manager', flush=True)
            sys.exit(1)

        nonlocal term_signal
        term_signal = signal.Signals(signum)
        term_event.set()
        print('Signal handler called with signal :', term_signal.name, flush=True)

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    max_name_length = 0
    for name, cfg in worker_config.items():
        for idx in range(cfg['num_workers']):
            pname = '%s_%d' % (name, idx + 1)
            if max_name_length < len(pname):
                max_name_length = len(pname)

    def _prefixed_print(prefix, txt, *, is_stdout=False):
        formatstr = '%-{:d}s %s %s'.format(max_name_length)
        print(formatstr % (prefix, '|' if is_stdout else '>', txt), flush=True)

    def _process_monitor(pname, popen_obj):
        while True:
            try:
                output = popen_obj.stdout.readline()
            except Exception:
                print('Error while reading outputs from "%s"\n%s'
                      % (pname, traceback.format_exc()),
                      flush=True)
                break

            if not output:
                break

            _prefixed_print(pname, output.rstrip(), is_stdout=True)

        while True:
            retcode = popen_obj.poll()
            if retcode is not None:
                break
            time.sleep(_POLL_INTERVAL)

        _prefixed_print(pname, 'Terminated (retcode: %s)' % retcode)

    p_info_list = []
    for name, cfg in worker_config.items():
        for idx in range(cfg['num_workers']):
            pname = '%s_%d' % (name, idx + 1)
            popen_obj = subprocess.Popen(cfg['cmd'],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT,
                                         universal_newlines=True,
                                         start_new_session=True)
            p_monitor = threading.Thread(
                target=functools.partial(_process_monitor, pname, popen_obj),
                daemon=True
            )
            p_monitor.start()

            p_info_list.append({
                'pname': pname,
                'popen_obj': popen_obj,
                'p_monitor': p_monitor
            })

    for p_info in p_info_list:
        _prefixed_print(p_info['pname'],
                        'Started a process with PID %d' % p_info['popen_obj'].pid)

    try:
        while not term_event.is_set():
            for p_info in p_info_list:
                if p_info['popen_obj'].poll() is not None:
                    term_event.set()
                    break
            time.sleep(_POLL_INTERVAL)
        else:
            print('Start to terminate worker processes', flush=True)

    except Exception:
        traceback.print_exc()

    for p_info in p_info_list:
        retcode = p_info['popen_obj'].poll()
        if retcode is not None:
            continue
        _prefixed_print(p_info['pname'], '%s is requested' % term_signal.name)
        p_info['popen_obj'].send_signal(term_signal.value)

    wait_until_ts = time.time() + _SIGTERM_TIMEOUT
    while time.time() < wait_until_ts:
        for p_info in p_info_list:
            retcode = p_info['popen_obj'].poll()
            if retcode is None:
                break
        else:
            break
        time.sleep(_POLL_INTERVAL)
    else:
        print('Timeout while waiting the termination of worker processes', flush=True)

    wait_until_ts = time.time() + _MONITOR_THREAD_TIMEOUT
    while time.time() < wait_until_ts:
        for p_info in p_info_list:
            p_info['p_monitor'].join(0)
            if p_info['p_monitor'].is_alive():
                break
        else:
            break
        time.sleep(_POLL_INTERVAL)
    else:
        print('Timeout while waiting the termination of monitor threads', flush=True)

        print('Live monitor threads:', flush=True)
        for p_info in p_info_list:
            if p_info['p_monitor'].is_alive():
                print('- %s' % p_info['pname'], flush=True)
