import asyncio
import aiopg
import argparse
import yaml
import os
import shutil
import uuid
from PIL import Image
import json
from datasetconverter.template import template
from datasetconverter.tmp import test


class Config:
    def __init__(self, file: str):
        with open(file) as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
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

    async def load_defects(self):
        defects = {}
        async with aiopg.create_pool(self.config.dsn) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute('SELECT cyrillic_name, name FROM defects_new')
                    async for row in cur:
                        defects.update({row[0]: f'{row[0]}/{row[1]}'})
        return defects

    async def convert(self):
        template['_via_settings']['project']['name'] = self.config.project
        template['_via_attributes']['region']['defect']['options'] = await self.load_defects()

        tmp_dir = os.path.join(os.getcwd(), 'tmp')

        # if os.path.exists(tmp_dir):
        #     shutil.rmtree(tmp_dir)
        # os.mkdir(tmp_dir)
        #
        # via_img_metadata = {}
        #
        # for cur_dir in os.listdir(self.config.source_dir):
        #     cur_dir = os.path.join(self.config.source_dir, cur_dir)
        #     if self.config.exclude_good_img:
        #         images = []
        #         with open(os.path.join(cur_dir, 'data.json')) as f:
        #             for item in json.load(f)['photos']:
        #                 for imgs in item['LED']:
        #                     for img, data in imgs.items():
        #                         if data['evaluations'][0]['defects'] in [{"47": 3}, {"47": 2}, {"47": 1}]:
        #                             continue
        #                         images.append(os.path.join(cur_dir, img))
        #     else:
        #         images = [os.path.join(cur_dir, n) for n in os.listdir(cur_dir) if n.endswith('.jpg')]
        #
        #     for image in images:
        #         image_name = f'{str(uuid.uuid4())}.png'
        #
        #         im = Image.open(image)
        #         im.save(os.path.join(tmp_dir, image_name))
        #
        #         via_img_metadata.update({image_name: {
        #             'filename': image_name,
        #             'size': os.path.getsize(os.path.join(tmp_dir, image_name)),
        #             'regions': [],
        #             'file_attributes': []
        #         }})

        via_img_metadata = test
        print(via_img_metadata)

        result = {}

        if os.path.exists(self.config.target_dir):
            shutil.rmtree(self.config.target_dir)
        os.mkdir(self.config.target_dir)

        for expert in range(1, self.config.experts + 1):
            print(expert)





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dataset datasetconverter')
    parser.add_argument('--config', type=str, help='YAML configuration file')
    args = parser.parse_args()

    converter = Converter(config=Config(args.config))

    asyncio.run(converter.convert())
