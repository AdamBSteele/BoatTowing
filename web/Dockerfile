FROM python:3.5

# Since this is a debug build, prolly helpful to have a text editor
RUN apt-get update && \
    apt-get install vim nano -y

# Make the app folder and switch to it
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Copy test requirements first so they're always built by cache
COPY test_requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r test_requirements.txt

# Copy full reqs
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole app & (maybe we don't need to install it)
COPY . /usr/src/app

# Install the app
RUN python /usr/src/app/setup.py install

RUN chmod +x /usr/src/app/manage.py
RUN chmod +x /usr/src/app/setup.py 
RUN chmod +x /usr/src/app/terraintracker/scripts/*
ENV PATH $PATH:/usr/src/app/terraintracker/scripts:/usr/src/app

# Copy pylint rc file over
COPY .pylintrc /etc/

WORKDIR /usr/src/app

CMD gunicorn -w 2 --reload -b :8000 gunicorn_entry:app
