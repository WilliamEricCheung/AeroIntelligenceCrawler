#!/bin/bash

# usage: echo [root-password] | sudo -S ./install-prerequisite.sh

# install browswer driver (chrome for ubuntu)
echo "
****************************
   Step 1: Install Chrome
****************************
"
if grep -q -i "debian" /etc/os-release; then
    echo "This is a Debian-based system."
    if [ ! -f google-chrome-stable_current_amd64.deb ]; then
        wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    fi
    sudo apt-get install libu2f-udev
    sudo dpkg -i google-chrome-stable_current_amd64.deb
    sudo apt-get -f install
    # default chrome path: /opt/google/chrome/
elif grep -q -i "rhel fedora" /etc/os-release; then
    echo "This is a RPM-based system."
    if [ ! -f google-chrome-stable_current_x86_64.rpm ]; then
        wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
    fi
    sudo yum install libu2f-udev
    sudo rpm -i google-chrome-stable_current_x86_64.rpm
    sudo yum -y install
else
    echo "Unsupported operating system."
fi

echo "
**************************************************
   Step 2: Install Python and Related Dependencies
**************************************************
"
## install python3
#sudo apt-get update
#sudo apt-get install python3

# install python3.10.12
wget https://www.python.org/ftp/python/3.10.12/Python-3.10.12.tgz
tar -xvf Python-3.10.12.tgz
cd Python-3.10.12

sudo yum groupinstall "Development Tools"
sudo yum install gcc openssl-devel bzip2-devel libffi-devel

./configure --enable-optimizations --with-openssl=/usr/include/openssl
make altinstall


cd AeroIntelligenceCrawler
# create virtual environment
python3 -m venv crawler
# activate virtual environment
source crawler/bin/activate
# install dependencies
sudo apt-get install libxml2-devel libxslt-devel
pip install --upgrade pip
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/


cd AeroIntelligenceCrawler
# create virtual environment
python3.10 -m venv crawler_py310
# activate virtual environment
source crawler_py310/bin/activate
# install dependencies
sudo apt-get install libxml2-devel libxslt-devel
pip install --upgrade pip
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
