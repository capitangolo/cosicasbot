#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import context, uploads
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Model:


    def __init__(self, logger, config, default_conversation_generator, masters = []):
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

        # Uploads
        self.uploads = uploads.UploadManager(self.cfg.uploads_folder)

        # Masters
        self.masters = masters

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


    def watermarks_for(self, product):
        watermarks = []
        for manager in self.masters:
            image_path = manager.watermark_for(product)
            if image_path:
                watermarks.append(image_path)

        return watermarks


    def zip_masters_for(self, products):
        zipfile = None
        existing_all = set()

        for manager in self.masters:
            zipfile, existing = manager.zip_masters_for(products, zipfile)
            existing_all.update(existing)

        missing = set(products).difference(existing_all)

        return zipfile, missing
