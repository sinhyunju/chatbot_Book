import json
import logging
import logging.handlers
import os
import queue
import random
import sys
import threading
import time
import traceback
import urllib.parse
import urllib.request

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

_DEFAULT_LOGGING_FORMAT = ('[%(levelname)1.1s %(asctime)s P%(process)d %(threadName)s %(module)s:%(lineno)d] '
                           '%(message)s')


class _SlackLoggerThread(threading.Thread):

    MAX_FLUSH_BACKOFF = 64  # 64 seconds

    def __init__(self, slack_url):
        super().__init__()
        self.daemon = True
        self.slack_url = slack_url
        self.queue = queue.Queue()

        self._hostname = os.getenv('DOCKER_HOSTNAME') or os.getenv('HOSTNAME')
        self._flush_cnt = 0

    def run(self):
        while True:
            if self.flush() == 0:
                self._flush_cnt = 0
            self._flush_cnt += 1

            # https://cloud.google.com/storage/docs/exponential-backoff
            backoff_time = (2 ** self._flush_cnt) + (random.randint(0, 1000) / 1000)
            time.sleep(min(backoff_time, self.MAX_FLUSH_BACKOFF))

    def flush(self):
        logs = []
        while not self.queue.empty():
            logs.append(self.queue.get())

        if not logs:
            return 0

        msg_text = '%d log messages from %s' % (
            len(logs),
            self._hostname
        )
        if 20 < len(logs):
            msg_text += '\n(only first 20 logs were attached)'
            logs = logs[:20]

        msg = {
            'payload': json.dumps({
                'text': msg_text,
                'attachments': logs
            })
        }

        urllib.request.urlopen(self.slack_url,
                               data=urllib.parse.urlencode(msg).encode('utf-8'))

        return len(logs)


class _SlackLoggerHandler(logging.handlers.QueueHandler):
    def __init__(self, product_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_name = product_name

    def prepare(self, record):
        msg_pretext = record.message.splitlines()[0]
        if 80 < len(msg_pretext):
            msg_pretext = msg_pretext[:77] + '...'

        msg_fields = [
            {
                'title': 'ProductName',
                'value': self.product_name,
                'short': True
            },
            {
                'title': 'LoggerName',
                'value': record.name,
                'short': True
            },
            {
                'title': 'When',
                'value': record.asctime,
                'short': True
            },
            {
                'title': 'Level',
                'value': record.levelname,
                'short': True
            },
            {
                'title': 'Process',
                'value': '%s (%d)' % (record.processName,
                                      record.process),
                'short': True
            },
            {
                'title': 'Thread',
                'value': '%s (%d)' % (record.threadName,
                                      record.thread),
                'short': True
            },
            {
                'title': 'Where',
                'value': '%s (line %s, in %s)' % (record.pathname,
                                                  record.lineno,
                                                  record.funcName)
            }
        ]

        msg_text = record.message
        if record.exc_info is not None:
            traceback_lines = ''.join(traceback.format_exception(*record.exc_info)).splitlines()
            if 100 < len(traceback_lines):
                traceback_lines = traceback_lines[:50] + ['...(truncated)...'] + traceback_lines[-50:]
            msg_text += '\n```%s```' % '\n'.join(traceback_lines)

        return {
            'color': '#ff7777',
            'pretext': msg_pretext,
            'text': msg_text,
            'fields': msg_fields
        }


def init_logger(product_name,
                app_logger_name,
                app_logger_level=logging.INFO,
                stdout_handler_level=logging.INFO,
                stdout_handler_format=_DEFAULT_LOGGING_FORMAT,
                slack_url=None,
                slack_handler_level=logging.ERROR,
                sentry_dsn=None,
                sentry_handler_level=logging.ERROR,
                additional_loggers=[]):
    app_logger = logging.getLogger(app_logger_name)
    app_logger.setLevel(app_logger_level)

    log_handlers = []

    # STDOUT handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(stdout_handler_level)
    stdout_handler.setFormatter(logging.Formatter(stdout_handler_format))
    log_handlers.append(stdout_handler)

    # Slack handler
    if slack_url is not None:
        slack_logger_thread = _SlackLoggerThread(slack_url)
        slack_logger_thread.start()

        slack_handler = _SlackLoggerHandler(product_name, slack_logger_thread.queue)
        slack_handler.setLevel(slack_handler_level)
        log_handlers.append(slack_handler)

    # Sentry handler
    if sentry_dsn is not None:
        # `sentry_sdk` internally uses a thread to send HTTP requests, so we do not need to care.
        sentry_sdk.init(
            sentry_dsn,
            release=product_name,
            integrations=[
                # `LoggingIntegration` is enabled by default and this is for explicit configuration
                LoggingIntegration(
                    level=app_logger_level,
                    event_level=sentry_handler_level
                )
            ]
        )

    interested_loggers = [
        app_logger,
        *additional_loggers
    ]

    for logger in interested_loggers:
        for log_hadnler in log_handlers:
            logger.addHandler(log_hadnler)

    app_logger.info('App logger is started.')

    return app_logger
