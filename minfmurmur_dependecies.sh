#!/usr/bin/env bash

virtualenv mindmurmurvirtualenv
source mindmurmurvirtualenv/bin/activate

pip install numpy
sudo apt-get install build-essential libtool autoconf libpng12-dev libjpeg62-dev libxml2-dev python-dev python-numpy python-wxgtk2.8 subversion python-pyaudio install python2.7-pyside python-wxgtk3.0
