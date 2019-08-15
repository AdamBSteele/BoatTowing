from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from terraintracker.app import app
from terraintracker.app_init import db
from terraintracker.scripts import create_users, initial_live_config

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def create(obj_name):
    if obj_name == 'users' or obj_name == 'user':
        create_users.run()
    else:
        print("usage: python manage.up create users")


@manager.command
def initialize():
    """Runs create_users and initial_live_config"""
    # delete_users.run()
    # delete_tow_events.run()
    # create_users.run()
    initial_live_config.run()


#@manager.command
#def print_users():
#get_all_users.print_users()

if __name__ == '__main__':
    manager.run()
