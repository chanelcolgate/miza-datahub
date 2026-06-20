## Miza DataHub Library

[![Tests](https://github.com/chanelcolgate/miza_datahub/actions/workflows/miza_datahub.yml/badge.svg)](https://github.com/chanelcolgate/miza_datahub/actions/workflows/miza_datahub.yml)

[![codecov](https://codecov.io/gh/chanelcolgate/miza_datahub/branch/develop/graph/badge.svg)](https://codecov.io/gh/chanelcolgate/miza_datahub)
### How to install
- Cài pip
```bash
pip install --upgrade pip setuptools wheel
```
- Cách khác
```bash
python -m ensurepip --upgrade
```
- Cách cài đặt và chạy
```
pyproject-build
python -m pip install -e .
```
- Cách test
```
python -m pip install pytest
python -m pytest
python -m pip install mypy
python -m mypy
python -m pip install tox
tox -e typecheck 
tox -e lint
```
