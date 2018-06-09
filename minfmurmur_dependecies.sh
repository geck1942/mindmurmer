#!/usr/bin/env bash

# General dependencies
#=====================
bash fr0st-master/install-dependencies.sh
virtualenv mindmurmurvirtualenv
source mindmurmurvirtualenv/bin/activate
pip install numpy

sudo apt-get install python-pyaudio
sudo apt-get install python2.7-pyside
sudo apt-get install python-wxgtk3.0

# Compiling libflam.so
#=====================
git clone https://github.com/flame/libflame.git
sudo apt-get install f2c gfortran libblas-dev liblapack-dev

cd libflame
./configure
./make
./make install