# Data set converter

#### Installation

```bash
git clone https://github.com/SergeyMokeyev/datasetconverter.git
cd datasetconverter/
python3 setup.py install
```

#### Usage

```bash
# copy end edit config-example.yaml
cp config-example.yaml config.yaml
nano config.yaml

# run converter
python -m datasetconverter --config config.yaml 
```