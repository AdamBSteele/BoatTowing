#!/usr/local/bin/python
"""
Creates some sample users for us to play with
"""
from datetime import datetime

from terraintracker.app_init import db
from terraintracker.models.live_configuration import LiveConfiguration


def run():
    initialLiveConf = LiveConfiguration(very_first_config_ever=True)
    initialLiveConf.modification_time = datetime.now()
    #  10 miles
    initialLiveConf._tow_radius = 1609300  # noqa pylint: disable=protected-access
    db.session.add(initialLiveConf)
    db.session.commit()
    db.session.close_all()
    print("Successfully initialized.")


if __name__ == "__main__":
    run()
