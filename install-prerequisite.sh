#!/bin/bash

# usage: echo [root-password] | sudo -S ./install-prerequisite.sh

# set work directory
# example: WORK_DIR="/mnt/d/Project/AeroIntelligenceCrawler"
WORK_DIR="$(pwd)"

echo "
**************************************************
   Step 1: Install Docker
**************************************************
"

# https://docs.docker.com/engine/install/ubuntu/
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

cat /etc/docker/daemon.json << EOF
{
    "registry-mirrors": [
        "https://hub-mirror.c.163.com",
        "https://mirror.baidubce.com",
    ]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker

# install browswer driver (chrome for ubuntu)
echo "
****************************
   Step 2: Install Chrome
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
   Step 3: Install Python and Related Dependencies
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
   Step 4: ElasticSearch
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

# enter the es container and install analyzer-ik
docker exec -it es /bin/bash
cd /usr/share/elasticsearch/bin
elasticsearch-plugin install analysis-smartcn
# 自动安装不行，手动拷贝到/usr/share/elasticsearch/plugins创建ik目录，解压缩到ik
echo y | elasticsearch-plugin install https://github.com/infinilabs/analysis-ik/releases/download/v8.12.2/elasticsearch-analysis-ik-8.12.2.zip
exit
docker restart es

echo "
**************************************************
   Step 5: Kibana for ElasticSearch
**************************************************
"
docker pull kibana:8.12.2
# start temp kibana
docker run --name kibana_temp -d -p 5601:5601 kibana:8.12.2
# copy kibana configuration from temp kibana to host
docker cp kibana_temp:/usr/share/kibana/config $WORK_DIR/kibana/
chmod -R 777 $WORK_DIR/kibana
docker rm -f  kibana_temp
# change kibana configuration
sed -i 's/http:\/\/elasticsearch:9200/http:\/\/es:9200/g' $WORK_DIR/kibana/config/kibana.yml

docker run -d --name kibana -p 5601:5601 \
-v $WORK_DIR/kibana/config/kibana.yml:/usr/share/kibana/config/kibana.yml \
--network es-net --restart=always kibana:8.12.2