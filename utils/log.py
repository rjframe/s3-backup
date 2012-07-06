# log.py - Class to log system / error messages

# Copyright 2012 Ryan Frame

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import logging.config

from config import log_file
from config import company
from config import log_raise_errs

# TODO: log handler to email on all failed backups (CRITICAL)

LOGGING = {
    'version': 1,
    'formatters': {
        'withtime': {
            'format': '%(asctime)s: %(name)-12s (%(lineno)-3d)- %(message)s'
        },
        'notime': {
            'format': '%(name)-12s: %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'tofile': {
            'level': 'DEBUG', # 'WARN',
            'class': 'logging.FileHandler',
            'formatter': 'withtime',
            'filename': log_file
        },
        'toconsole': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'notime'
        }
    },
    'loggers': {
        company : {
            'handlers': ['tofile', 'toconsole'],
            'level': 'DEBUG'
        }
    }
}

logging.config.dictConfig(LOGGING)

logging.raiseExceptions = log_raise_errs

# Optimize
# logging._srcfile = None
logging.logThreads = 0
logging.logProcesses = 0

def get_logger(name):
    '''Returns a logger. Messages propogate to the root handler.'''
    logger = logging.getLogger(company + '.' + name)

    return logger


if __name__ == '__main__':
    print(log_file)
