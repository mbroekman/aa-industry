#!/bin/bash
docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "
apt-get update && apt-get install -y gettext
pip install django
django-admin compilemessages -l nl -i .tox -i .venv
"
