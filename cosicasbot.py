#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from cosicasbot.bot import Bot
from cosicasbot.conversations import *
from cosicasbot.interfaces import *
from cosicasbot.model import config, model, masters
import logging
import unicodedata

from cosicasbot.model import context


VERSION = '1.0.17'


INTERFACES = [
    telegram.Telegram
]

CONVERSATIONS = [
    start,
    admin,

    signup,

    catalog,
    cart,
    orders
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


def load_masters(cfg):
    managers = []
    uploads_path = cfg.uploads_folder

    # 38mm Badges
    managers.append(masters.BadgeMasterManager(uploads_path, 'badge_38mm', 520, 450, 'watermark.png'))
    # 50mm Badges
    managers.append(masters.BadgeMasterManager(uploads_path, 'badge_59mm', 709, 610, 'watermark.png'))

    return managers


def main():
    args = parse_args()

    logger.info('Reading configuration settings')
    cfg = config.Config(args.config_file, logger, VERSION)

    logger.info('Starting cosicasbot v{} for {}'.format(VERSION, cfg.botname))

    logger.info('Loading model')
    masters = load_masters(cfg)
    m = model.Model(logger, cfg, start.start_conversation, masters)

    logger.info('Loading bot')
    bot = Bot(m, start.start)
    bot.load_interfaces(INTERFACES)
    bot.load_conversations(CONVERSATIONS)
    bot.start()

    logger.info('Bot started')


if __name__ == '__main__':
    main()
