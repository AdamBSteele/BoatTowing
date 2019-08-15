#! /usr/local/bin/python
"""
Allows us to install the app as a module
Makes debugging from interpreter very easy (you can just import everything)
"""

import os
from setuptools import setup, find_packages

setup(
    # Required
    name='terraintracker',
    version='0.1',
    url='https://github.com/mr813/terraintracker',

    # Not Required
    description="API Backend for Drift",
    packages=find_packages(include=['terraintracker', 'terraintracker.*']),
    test_suite='terraintracker.tests',
    zip_safe=True,

    # Scripts get added to $PATH
    scripts=[os.path.join(dp, f) for dp, dn, fn in os.walk('terraintracker/scripts')
             for f in fn if f.endswith('.py') and f not in '__init__.py'] + ['run_api.py', ],
)
