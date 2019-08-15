#!/usr/local/bin/python

python /usr/src/app/setup.py install
sleep 40
python /usr/src/app/manage.py db upgrade
python /usr/src/app/setup.py test
python /usr/src/app/setup.py --quiet lint
