# coding=utf-8
import os
from twisted.python import log, logfile

from .logger import PrintingObserver, WampLogObserver, block_on

# Add global observer for daily logs
if os.getenv('_LIE_GLOBAL_LOG', 0) == '1':
    observer = PrintingObserver(logfile.DailyLogFile('daily.log', os.getenv('_LIE_GLOBAL_LOG_DIR', './data/logs')))
    log.addObserver(observer)
