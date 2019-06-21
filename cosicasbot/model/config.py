#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
import json
import os.path
from collections import namedtuple


class Config:

    ConfigOption = namedtuple('ConfigOption', ['name', 'default', 'required'])

    CONFIG_OPTIONS = [
        ConfigOption('botname', None, True),

        ConfigOption('debug', None, True),

        ConfigOption('db_url', None, True),
        ConfigOption('templates_folder', None, True),
        ConfigOption('uploads_folder', None, True),

        ConfigOption('groups_admin_id', 1, True),
        ConfigOption('groups_allusers_id', 2, True),

        ConfigOption('telegram_botname', None, False),  # For documentation purposes, not used.
        ConfigOption('telegram_apikey', None, False),

        ConfigOption('texts_module', 'config.texts', True),

        ConfigOption('web_secret', None, False),
        ConfigOption('web_db_name', None, False),
        ConfigOption('web_db_user', None, False),
        ConfigOption('web_db_pass', None, False),
        ConfigOption('web_db_host', None, False),
        ConfigOption('web_db_port', None, False),
    ]


    def __init__(self, config_file, logger, version):
        self.version = version
        with open(config_file) as json_data_file:
            config = json.load(json_data_file)

            for option in self.CONFIG_OPTIONS:
                value = None
                defined = False
                if option.name in config:
                    value = config[option.name]
                    defined = True
                elif option.default:
                    value = option.default
                    defined = True

                if defined:
                    setattr(self, option.name, value)
                elif option.required:
                    error = 'Error parsing configuration. Missing required paramenter: {}'.format(option.name)
                    logger.error(error)
                    raise(ConfigError(error))
        self.t = importlib.import_module(self.texts_module)


class ConfigError(Exception):

    def __init__(self, value):
        self.value = value


    def __str__(self):
        return repr(self.value)
