BBW API
=======

### Overview

The project consists of 4 Docker containers:

 - web: API wrapped in gunicorn
   - 99% of dev time is spent in the Bash prompt in this container
 - postgres: DB container
 - data: Shared valume so postgres data persists
 - nginx: NGINX layer. Connects Gunicorn to localhost:80

Use [Anaconda for Sublime Text](https://github.com/DamnWidget/anaconda) for auto-complete

Open the project in Sublime using the terraintracker.sublime-project file

##### Dependencies
- Docker

##### Full API Docs
Full documentation of methods and classes [here](https://mr813.github.io/driftboat/)

### Running the web server locally

Use ```docker-compose kill; docker-compose build; docker-compose up;``` to start Docker containers.

Use ```docker exec -it $(docker ps | grep terraintracker_web | cut -d' ' -f1) /bin/bash ``` to run bash in your active web container.
 - this is just a shortcut for `docker exec -it <web_container_id> /bin/bash`

**All commands in this README are executed from `/bin/bash` prompt in the `web` container unless otherwise noted.**

The Docker container is directly linked to your code, so all changes in Sublime will be instantly available seen in the `web` container

### Initial DB Setup
```
# This creates postgis extension inside of the postgres database container
docker exec -it <postgres_container_id> psql -h postgres -U postgres -d terraintracker -c 'CREATE EXTENSION postgis'


# Create db tables (back in web container)
docker exec -it <web_container_id> /bin/bash
python manage.py db upgrade
python manage.py initialize
```


## Development Process - running and testing the application

**All commands in this README are executed from `/bin/bash` prompt in the `web` container unless otherwise noted.**

##### Open interactive Python interpreter with all models imported

```
# Open a Python shell with all the stuff imported so you can interact with the
# app using the Python interpreter.
drop_into_shell_with_everything_imported.py
>>> print(User.query.all())
```


##### Testing

```
# Run all unit tests (test coverage reported in htmlcov/index.html)
python setup.py develop # you only have to run this once ever
py.test -c tox.ini

# Run single test file
py.test -c tox.ini -s terraintracker/tests/<test_file>

# Run single test
py.test -c tox.ini -s terraintracker/tests/<test_file> -k <name_of_test_function>

# Lint (config stored in pylintrc file)
python setup.py lint

# Looking at test coverage
In your internet browser, open the file <project>/htmlcov/index.html
```

## Development Process - building things

##### Adding/modifying an endpoint
1) make the changes in the `resources` folder.
2) add your new endpoint to app.py (if necessary)
3) Make sure the docstrings are written [in rst format like this](http://kartowicz.com/dryobates/2016-10/sphinx-rest-api/)
4) Let Adam know so he can push the API doc updates throug Sphinx

##### Changing the db [(Alembic migrations)](https://realpython.com/blog/python/flask-by-example-part-2-postgres-sqlalchemy-and-alembic/)

First, make the changes in the `models` folder. Then auto-generate a new migration file with
```
python manage.py db migrate
```
Now, edit the new Python file in web/migrations/versions so that it makes sense.
If you see a table/index in the migration file Alembic provided and you think
Alembic should ignore it forever, add it to [alembic:exclude] in alembic.ini


Then, run you migration file with:
```
python manage.py db upgrade
```

##### Adding columns to live db config
```
See: live_configuration.py for instructions.
```


##### Running psql on postgres container
```
# This opens the psql prompt in the Postgres container. I don't use it alot
docker exec -it <postgres_container>  psql -h postgres -U postgres -d terraintracker
```

##### BURN IT DOWN - when things go really wrong

This initializes a clean application. Destroys all Docker containers on your system. Removes all data.

```
# Kill and restart all containers, including volumes holding DB tables - CAUTION: YOU WILL LOSE DATA
docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q) && docker volume rm $(docker volume ls -q) && docker-compose build && docker-compose up

# Now go through the Initial DB Setup steps
```


#### Configuring the application
Application configuration happens through the terraintracker.<env>.ini files.
On your machine, you'll want to copy terraintracker.default.ini to terraintracker.local.ini and
add our "secret" values that we don't want to commit to Github (API keys and such). You find those in Slack for now.
Configuration also happens in the DB in the "live_configuration" table.

### Deployment
[Docker Cloud UI](https://cloud.docker.com/app/gobulls1026/stack/list/1?page_size=10) -> Stacks -> Drift2 -> Redeploy

##### [SSHing into Docker Cloud prod](https://docs.docker.com/docker-cloud/infrastructure/ssh-into-a-node/) 

```
1) Add your ssh key to the authorizedkeys stack and deploy it
2) ssh into [the AWS node](https://cloud.docker.com/app/gobulls1026/node/list/1?page_size=10) with:
   ssh -i <your_keyfile> root@54.67.29.174
3) use `docker ps` to find the container you want to ssh into 
4) docker exec -it <CONTAINER_ID>
```


#### Updating documentation through Sphinx

In `web` docker container, run:
```
sphinx-build -b html terraintracker/docs/source terraintracker/docs/build -a -E
```
Then use the files you generated in `terraintracker/docs/build` to update the `gh-branches` branch of this repo
