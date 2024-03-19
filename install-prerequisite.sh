#!/bin/bash

# usage: echo [root-password] | sudo -S ./install-prerequisite.sh

# set work directory
# example: WORK_DIR="/mnt/d/Project/AeroIntelligenceCrawler"
WORK_DIR="$(pwd)"

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


echo "
**************************************************
   Step 3: ElasticSearch
**************************************************
"
docker pull elasticsearch:8.12.2
# create a network for elasticsearch
docker network create es-net
# create a directory to store elasticsearch data
cd $WORK_DIR
mkdir es_mnt
# start temp elasticsearch
docker run -d --name es_temp  \
-e "discovery.type=single-node" \
-e "ES_JAVA_OPTS=-Xms5120m -Xmx5120m"  \
-p 9200:9200  -p 9300:9300  elasticsearch:8.12.2
# copy data from temp elasticsearch to host
docker cp -a es_temp:/usr/share/elasticsearch/config $WORK_DIR/es_mnt
docker cp -a es_temp:/usr/share/elasticsearch/data $WORK_DIR/es_mnt
docker cp -a es_temp:/usr/share/elasticsearch/plugins $WORK_DIR/es_mnt
docker cp -a es_temp:/usr/share/elasticsearch/logs $WORK_DIR/es_mnt
# change the owner of the directory
chmod -R 777 $WORK_DIR/es_mnt
# change elastic search configuration
sed -i 's/xpack.security.enabled: true/xpack.security.enabled: false/' $WORK_DIR/es_mnt/config/elasticsearch.yml
# stop and remove temp elasticsearch
docker rm -f  es_temp
# start elasticsearch
docker run -d --name es -p 9200:9200 -p 9300:9300 \
-e "discovery.type=single-node" \
-e "ES_JAVA_OPTS=-Xms5120m -Xmx5120m" \
-v "$WORK_DIR/es_mnt/config:/usr/share/elasticsearch/config" \
-v "$WORK_DIR/es_mnt/data:/usr/share/elasticsearch/data" \
-v "$WORK_DIR/es_mnt/plugins:/usr/share/elasticsearch/plugins" \
-v "$WORK_DIR/es_mnt/logs:/usr/share/elasticsearch/logs" \
--network es-net --restart=always elasticsearch:8.12.2

echo "
**************************************************
   Step 4: Kibana for ElasticSearch
**************************************************
"
docker pull kibana:8.12.2

docker run -d --name kibana -p 5601:5601 \
-e "ELASTICSEARCH_HOSTS=http://es:9200" \
--network es-net kibana:8.12.2