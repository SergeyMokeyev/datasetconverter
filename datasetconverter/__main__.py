import asyncio
import aiopg
import argparse
import yaml
import os
import shutil
import uuid
from PIL import Image
import json
import collections
import itertools
from datasetconverter.template import template


class Config:
    def __init__(self, file: str):
        with open(file) as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        self.product_id = data.get('product_id', 1)
        self.project = data.get('project', 'datasetconverter')
        self.source_dir = data.get('source_dir', './source')
        self.target_dir = data.get('target_dir', './target')
        self.experts = data.get('experts', 1)
        self.exclude_good_img = data.get('exclude_good_img', True)
        self.repeat_img_step = data.get('repeat_img_step', 1)
        self.dsn = ' '.join([f'{k}={v}' for k, v in data.get('defects_db', {}).items()])


class Converter:
    def __init__(self, config: Config):
        self.config = config

    @staticmethod
    def make_directory(directory):
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.mkdir(directory)

    def get_via_img_metadata(self):
        via_img_metadata = {}
        for cur_dir in os.listdir(self.config.source_dir):
            if cur_dir.startswith('.'):
                continue
            cur_dir = os.path.join(self.config.source_dir, cur_dir)

            images = []
            with open(os.path.join(cur_dir, 'data.json')) as f:
                for item in json.load(f)['photos']:
                    for imgs in [{k: v} for k, v in item['LED'].items() if v['type'] != 'FULL']:
                        for img, data in imgs.items():
                            if (self.config.exclude_good_img and data['evaluations'][0]['defects']
                                    in [{"47": 3}, {"47": 2}, {"47": 1}]):
                                continue
                            images.append(os.path.join(cur_dir, img))

            for image in images:
                image_name = f'{str(uuid.uuid4())}.png'

                im = Image.open(image)
                im.save(os.path.join(self.config.target_dir, image_name))

                via_img_metadata.update({image_name: {
                    'filename': image_name,
                    'size': os.path.getsize(os.path.join(self.config.target_dir, image_name)),
                    'regions': [],
                    'file_attributes': []
                }})

        return via_img_metadata

    async def load_defects(self):
        defects = {}
        async with aiopg.create_pool(self.config.dsn) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute('''
                    SELECT dn.cyrillic_name, dn.name FROM defects_new dn
                        LEFT JOIN defect_groups_new dgn on dn.defect_group_id = dgn.id
                    WHERE product_id = %s
                    ''', (self.config.product_id,))
                    async for row in cur:
                        defects.update({row[0]: f'{row[0]}/{row[1]}'})
        return defects

    async def convert(self):
        template['_via_settings']['project']['name'] = self.config.project
        template['_via_attributes']['region']['defect']['options'] = await self.load_defects()

        self.make_directory(self.config.target_dir)
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'via.html'), self.config.target_dir)

        via_img_metadata = self.get_via_img_metadata()

        experts = [f'expert_{i}' for i in range(1, self.config.experts + 1)]
        experts_cycle = itertools.cycle(experts)
        experts_images = collections.defaultdict(dict)
        count = 0
        for image, data in via_img_metadata.items():
            count += 1
            if count == self.config.repeat_img_step:
                count = 0
                for expert in experts:
                    experts_images[expert].update({image: data})
            else:
                expert = next(experts_cycle)
                experts_images[expert].update({image: data})

        for expert, data in experts_images.items():
            template['_via_img_metadata'] = data
            with open(os.path.join(self.config.target_dir, f'{expert}.json'), 'w') as f:
                json.dump(template, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dataset datasetconverter')
    parser.add_argument('--config', type=str, help='YAML configuration file')
    args = parser.parse_args()

    converter = Converter(config=Config(args.config))

    asyncio.run(converter.convert())
