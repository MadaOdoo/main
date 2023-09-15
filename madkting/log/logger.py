# -*- coding: utf-8 -*-
# File:           logger.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-03-20
from logging import getLogger


logger = getLogger('madkting')

def logs(data, config=None):
    if config and config.log_enabled:
        logger.info(data)
    else:
        logger.debug(data)

class CustomLog:
    def __init__(self, config=None):
        self.config = config

    def log(self, msg):
        if self.config and self.config.log_enabled:
            logger.info(msg)
        else:
            logger.debug(msg)
