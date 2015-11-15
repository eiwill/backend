#!/bin/sh

install_virtualenv=1
if [ -f ./env/bin/python ]; then
  install_virtualenv=0
fi

if [ $install_virtualenv -eq 1 ]; then
  wget https://bootstrap.pypa.io/get-pip.py
  sudo python get-pip.py
  sudo pip install virtualenv
  virtualenv env
  rm get-pip.py
fi
