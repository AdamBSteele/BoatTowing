FROM tutum/nginx
RUN rm /etc/nginx/sites-enabled/default
ADD sites-enabled/ /etc/nginx/sites-enabled
ADD ssl/ /etc/nginx/ssl
ARG RUNNING_IN_PROD

# If we aren't in prod, remove ssl_routes from nginx sites-enabled
RUN if [ "$RUNNING_IN_PROD" ] ; then echo 'Running in prod'; else echo ''>/etc/nginx/sites-enabled/ssl_routes; fi
