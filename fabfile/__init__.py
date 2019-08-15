# based on https://realpython.com/blog/python/kickstarting-flask-on-ubuntu-setup-and-deployment/

from fabric.api import cd, env, lcd, put, sudo
from fabric.contrib.files import exists

import config


local_app_dir = './terraintracker'
local_config_dir = './fabfile/config'

remote_user_home = '/home/www'
remote_app_dir = remote_user_home + '/app'
remote_nginx_dir = '/etc/nginx/sites-enabled'
remote_supervisor_dir = '/etc/supervisor/conf.d'

env.hosts = [config.HOST]
env.user = config.USER


def install_packages():
    """ Install required packages """
    sudo('apt-get update')
    sudo('apt-get install -y python')
    sudo('apt-get install -y python-pip')
    sudo('apt-get install -y python-virtualenv')
    sudo('apt-get install -y nginx')
    sudo('apt-get install -y gunicorn')
    sudo('apt-get install -y supervisor')
    sudo('apt-get install -y git')
    # required for Pillow
    # http://askubuntu.com/questions/507459/pil-install-in-ubuntu-14-04-1-lts
    sudo('apt-get build-dep -y python-imaging')
    sudo('apt-get install -y libjpeg8 libjpeg62-dev libfreetype6 libfreetype6-dev')
    sudo('apt-get install -y python-dev libmysqlclient-dev')
    sudo('apt-get install -y mysql-client')


def install_app():
    """
    Put app files into app directory on server and install app requirements
    1. Create project directories
    2. Copy Flask files to remote host
    3. Install app requirements
    """
    if exists(remote_user_home) is False:
        sudo('mkdir ' + remote_user_home)
    if exists(remote_app_dir) is False:
        sudo('mkdir ' + remote_app_dir)
    with lcd(local_app_dir):
        with cd(remote_app_dir):
            put('*', './', use_sudo=True)
        with cd(remote_user_home):
            sudo('pip install -r app/requirements.txt')


def configure_nginx():
    """
    Configure Nginx
    1. Remove default nginx config file
    2. Create new config file
    3. Setup new symbolic link
    4. Copy local config to remote config
    5. Restart nginx
    """
    sudo('/etc/init.d/nginx start')
    if exists('/etc/nginx/sites-enabled/default'):
        sudo('rm /etc/nginx/sites-enabled/default')
    if exists('/etc/nginx/sites-enabled/app') is False:
        sudo('touch /etc/nginx/sites-available/app')
        sudo('ln -s /etc/nginx/sites-available/app' +
             '      /etc/nginx/sites-enabled/app')
    with lcd(local_config_dir):
        with cd(remote_nginx_dir):
            put('./nginx', './app', use_sudo=True)
    sudo('/etc/init.d/nginx restart')


def configure_supervisor():
    """
    Configure Supervisor
    1. Create new supervisor config file
    2. Copy local config to remote config
    3. Register new command
    """
    if exists('/etc/supervisor/conf.d/app.conf') is False:
        with lcd(local_config_dir):
            with cd(remote_supervisor_dir):
                put('./supervisor', './app.conf', use_sudo=True)
                sudo('supervisorctl reread')
                sudo('supervisorctl update')


def restart():
    sudo('supervisorctl restart app')


def status():
    """ Is app live? """
    sudo('supervisorctl status')


def create():
    """ Create app """
    install_packages()
    install_app()
    configure_nginx()
    configure_supervisor()
