#!/bin/bash

# usage: echo [root-password] | sudo -S ./install-prerequisite.sh

# install browswer driver (chrome for ubuntu)
echo "
****************************
   Step 1: Install Chrome
****************************
"

if [ ! -f google-chrome-stable_current_amd64.deb ]; then
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
fi
sudo apt-get install libu2f-udev
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get -f install
# default chrome path: /opt/google/chrome/

# install python3
sudo apt-get update
sudo apt-get install python3

sudo apt-get install libxml2-devel libxslt-devel

cd AeroIntelligenceCrawler
# create virtual environment
python3 -m venv crawler
# activate virtual environment
source crawler/bin/activate
# install dependencies
pip install --upgrade pip
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/