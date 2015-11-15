# Set the base image to Ubuntu
FROM ubuntu

ADD . /srv/base
WORKDIR /srv/base

RUN apt-get update && apt-get install -y make wget python-dev && make main-deps