#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
from PIL import Image, ImageDraw
from unidecode import unidecode
import zipfile

class BadgeMasterManager:

    def __init__(self, upload_folder, masters_folder, masters_size, badge_size, watermark_file):
        self.upload_foler = os.path.abspath(upload_folder)
        self.masters_folder = masters_folder
        self.masters_size = masters_size
        self.badge_size = badge_size
        self.watermark_file = watermark_file


    def master_path_for(self, product):
        return os.path.join(self.upload_foler, self.masters_folder, str(product.catalog_ref), str(product.id), str(product.model) + '.jpg')


    def watermark_path_for(self, product):
        return os.path.join(self.upload_foler, self.masters_folder, str(product.catalog_ref), self.watermark_file)


    def cached_watermark_path_for(self, product):
        filename = self.filename_for(product)
        return os.path.join(self.upload_foler, self.masters_folder, 'cached', str(product.catalog_ref), filename)


    def has_master_for(self, product):
        master_path = self.master_path_for(product)
        return os.path.isfile(master_path)


    def watermark_for(self, product):
        cached_path = self.cached_watermark_path_for(product)

        if os.path.isfile(cached_path):
            return cached_path

        master_path = self.master_path_for(product)
        watermark_path = self.watermark_path_for(product)

        if not os.path.isfile(master_path):
            return None

        if not os.path.isfile(watermark_path):
            return None

        master = Image.open(master_path)
        watermark = Image.open(watermark_path)

        watermarked = self.apply_watermark(master, watermark)

        directory = os.path.dirname(cached_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        watermarked.save(cached_path)

        return cached_path


    def master_for(self, product):
        master_path = self.master_path_for(product)

        if not os.path.isfile(master_path):
            return None

        return master_path


    def filename_for(self, product):
        filename = "{}_{}_{}_{}.png".format(
                product.catalog_ref,
                product.id,
                product.model,
                product.name,
            )

        return unidecode(filename)


    def apply_watermark(self, input_image, watermark_image):
        # Set the input image to the proper size and type.
        master_size = (self.masters_size, self.masters_size)
        badge_size = (self.badge_size, self.badge_size)
        input_image = input_image.resize(master_size, Image.ANTIALIAS)
        # We'll need transparent pixels
        input_image = input_image.convert('RGBA')

        # Set watermark image to the proper size.
        watermark_image = watermark_image.resize(master_size, Image.ANTIALIAS)

        # Apply watermark
        watermarked_image = Image.alpha_composite(input_image, watermark_image)

        # Draw a circle in 4x resolution, then scale it down.
        supersampling_size = (self.masters_size * 4, self.masters_size * 4)
        superbadge_size = (self.badge_size * 4, self.badge_size * 4)

        mask = Image.new('L', supersampling_size, 0)
        draw = ImageDraw.Draw(mask)
        circle_origin = (supersampling_size[0] - superbadge_size[0]) / 2
        box = [circle_origin, circle_origin, circle_origin + superbadge_size[0], circle_origin + superbadge_size[1]]
        draw.ellipse(box, fill=255)
        mask = mask.resize(master_size, Image.ANTIALIAS)

        # Mask input image
        masked_image = Image.new('RGBA', master_size)
        masked_image.paste(watermarked_image, mask = mask)

        # Crop image to just the badge size
        badge_origin = (self.masters_size - self.badge_size) / 2
        badge_end = badge_origin + self.badge_size
        crop_box = (badge_origin, badge_origin, badge_end, badge_end)

        cropped_image = masked_image.crop(crop_box)

        return cropped_image


    def zip_masters_for(self, products, masterszip = None):
        if not masterszip:
            masterszip = io.BytesIO()

        zipfile_ob = zipfile.ZipFile(masterszip, 'w', compression=zipfile.ZIP_DEFLATED)

        existing = []

        for product in products:
            master_path = self.master_for(product)

            if not master_path:
                continue

            existing.append(product)

            filename = os.path.join('masters', self.masters_folder, self.filename_for(product))

            zipfile_ob.write(master_path, arcname=filename)
        zipfile_ob.close()

        return masterszip, existing
