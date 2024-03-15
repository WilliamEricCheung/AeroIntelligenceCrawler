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
