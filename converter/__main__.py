import asyncio
import aiopg
import argparse
import yaml


class Config:
    def __init__(self, file: str):
        with open(file) as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
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
        defects = []
        async with aiopg.create_pool(self.config.dsn) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute('SELECT * FROM defects_new')
                    async for row in cur:
                        defects.append(row)
        return defects

    async def convert(self):
        defects = await self.load_defects()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dataset converter')
    parser.add_argument('--config', type=str, help='YAML configuration file')
    args = parser.parse_args()

    converter = Converter(config=Config(args.config))

    asyncio.run(converter.convert())
