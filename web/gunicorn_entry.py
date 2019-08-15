#!/usr/bin/env python3
"""
Gunicorn uses this app object to spin up workers and pass stuff to them from nginx
"""
from terraintracker.app import app  # NOQA
