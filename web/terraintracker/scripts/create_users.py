#!/usr/local/bin/python
"""
Creates some sample users for us to play with
"""

from terraintracker.app_init import db

from terraintracker.models.user import User

DEFAULT_USERS = [
]


def run():
    print("Creating new users")

    mark = User(_id='Mark', name='Mark')
    mark.password = 'password'
    mark.phone = "8139577566"
    mark.is_android = True
    mark.update_position(38.997144, -77.12401)  # DC
    mark.role = User.Role.tower.value

    adam = User(_id='Adam', name='Adam')
    adam.password = 'password'
    adam.phone = "3475563921"
    adam.is_android = True
    adam.role = User.Role.tower.value
    adam.update_position(40.727328, -73.9876522)  # NYC

    brent = User(_id='Brent', name='Brent')
    brent.password = 'password'
    brent.phone = "5613061883"
    brent.is_android = True
    brent.role = User.Role.tower.value
    brent.update_position(30.4670643, -84.3972845)  # Tallahasse

    # rayna = User(_id='rayna', name='rayna')
    # rayna.password = 'password'
    # rayna.phone = "5613061883"
    # rayna.is_android = True
    # rayna.role = User.Role.tower.value
    # rayna.update_position(28.359309, -82.66591)  # Tampa

    db.session.merge(adam)
    db.session.merge(mark)
    db.session.merge(brent)
    # db.session.merge(rayna)
    db.session.commit()
    print("Successfully created users :)")


def delete_all_users():
    print("deleting all users")
    User.query.delete()
    db.session.commit()


if __name__ == "__main__":
    run()
