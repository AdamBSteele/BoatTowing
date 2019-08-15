#!/usr/local/bin/python
"""
Creates some sample users for us to play with
"""
from terraintracker.app_init import db

from terraintracker.models.tow_event import TowEvent


def run():
    print("Deleting tow events")
    tow_events = TowEvent.query.all()
    for event in tow_events:
        db.session.delete(event)

    db.session.commit()
    print("Successfully deleted tow events :)")


if __name__ == "__main__":
    run()
