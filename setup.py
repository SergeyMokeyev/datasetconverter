import setuptools


setuptools.setup(
    name='datasetconverter',
    version='0.0.1',
    author='Sergey Mokeyev',
    author_email='sergey.mokeyev@gmail.com',
    description='Data set converter',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/SergeyMokeyev/datasetconverter',
    data_files=[
        ('README.md', ['README.md'])
    ],
    packages=[
        'datasetconverter'
    ],
    install_requires=[
        'aiopg',
        'pyyaml',
        'Pillow'
    ]
)
