#!/bin/bash
docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "
apt-get update && apt-get install -y default-libmysqlclient-dev pkg-config gcc redis-server
service redis-server start
pip install tox
tox -e py312
"
