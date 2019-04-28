#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


PRODUCT_PHOTO_FOLDER = 'product'


class UploadManager:


    def __init__(self, upload_folder):
        self.upload_foler = os.path.abspath(upload_folder)


    def photos_for_product(self, catalog_id, product_id):
        path = os.path.join(self.upload_foler, PRODUCT_PHOTO_FOLDER, str(catalog_id), str(product_id))

        if not os.path.isdir(path):
            return []

        files = []
        for r, d, f in os.walk(path):
            for file in f:
                filename, file_extension = os.path.splitext(file)
                if file_extension == '.jpg':
                    files.append(os.path.join(path, file))

        files.sort()

        return files
