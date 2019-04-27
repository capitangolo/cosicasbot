#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import context
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Model:


    def __init__(self, logger, config, default_conversation_generator):
        # Logger
        self.log = logger

        # Config
        self.cfg = config

        # Database
        self.db_engine = create_engine(config.db_url)
        self.db_sessionmaker = sessionmaker(bind=self.db_engine)

        # Templates
        self.templates = Environment(
            loader=FileSystemLoader(self.cfg.templates_folder),
            line_statement_prefix='#',
            autoescape=False
        )

        # User Sessions
        self.default_conversation_generator = default_conversation_generator
        self.user_sessions = context.UserContexts(user_id_property = 'user_id', start = self.default_conversation_generator)
        self.visitor_sessions = {}

    def db(self):
        return self.db_sessionmaker()


    def render(self, template_name, output_format, **kwargs):
        template = self.templates.get_template('{}.{}'.format(template_name, output_format))
        return template.render(kwargs)


    def ctxt(self, user_id):
        return self.user_sessions.context_for(user_id)


    def visitor_ctxt(self, interface, user_id):
        if interface not in self.visitor_sessions:
            self.visitor_sessions[interface] = context.UserContexts(user_id_property = 'visitor_id', start = self.default_conversation_generator)
        return self.visitor_sessions[interface].context_for(user_id)
