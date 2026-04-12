#!/bin/bash
echo "BUILD START"
python3 -m pip install -r requirements.txt --break-system-packages
python3 BanglaCERT/manage.py collectstatic --noinput --clear
echo "BUILD END"
