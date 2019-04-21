#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import unicodedata
import json
import os.path
from jinja2 import Environment, FileSystemLoader
from cosicasbot.model import config

templates_folder = './config/templates'
config_files = [
    {'template': 'alembic.ini', 'output': 'alembic.ini'}
]


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config_file'
        , help="Config file to read bot config."
    )
    return parser.parse_args()


def generate_config_file(config, templates, template_name, output_file):
    logger.info('Processing {} into {}'.format(template_name, output_file))

    template = templates.get_template(template_name)
    file_content = template.render(cfg = config)

    with open(output_file, 'w') as out:
        out.writelines(file_content)


def main():
    args = parse_args()

    logger.info('Reading config')
    cfg = config.Config(args.config_file, logger)

    logger.info('Generating config files')
    templates_env = Environment(
        loader=FileSystemLoader(templates_folder)
    )
    for config_file in config_files:
        generate_config_file(cfg, templates_env, config_file['template'], config_file['output'])

    logger.info('Done')


if __name__ == '__main__':
    main()

