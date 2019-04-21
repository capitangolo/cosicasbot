#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os.path
from collections import namedtuple


class Config:

    ConfigOption = namedtuple('ConfigOption', ['name', 'default', 'required'])

    CONFIG_OPTIONS = [
        ConfigOption('botname', None, True),

        ConfigOption('db_url', None, True),
        ConfigOption('templates_folder', None, True),

        ConfigOption('groups_admin_id', 1, True),
        ConfigOption('groups_allusers_id', 2, True),

        ConfigOption('telegram_botname', None, False),  # For documentation purposes, not used.
        ConfigOption('telegram_apikey', None, False),

        # Action texts
        ConfigOption('action_cancel', 'cancel', False)
    ]


    def __init__(self, config_file, logger):
        with open(config_file) as json_data_file:
            config = json.load(json_data_file)
            for option in self.CONFIG_OPTIONS:
                value = None
                if option.name in config:
                    value = config[option.name]
                elif option.default:
                    value = option.default

                if value:
                    setattr(self, option.name, value)
                elif option.required:
                    error = 'Error parsing configuration. Missing required paramenter: {}'.format(option.name)
                    logger.error(error)
                    raise(ConfigError(error))


class ConfigError(Exception):

    def __init__(self, value):
        self.value = value


    def __str__(self):
        return repr(self.value)
