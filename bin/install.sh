#!/bin/bash

echo "deb http://download.opensuse.org/repositories/network:/messaging:/zeromq:/release-stable/Debian_9.0/ ./" >> /etc/apt/sources.list
wget https://download.opensuse.org/repositories/network:/messaging:/zeromq:/release-stable/Debian_9.0/Release.key -O- | sudo apt-key add
sudo apt install -y git libpugixml-dev libboost-all-dev cmake libzmq3-dev python3-venv

cd ~/Downloads
wget www.accellera.org/images/downloads/standards/systemc/systemc-2.3.3.gz
tar -xzf systemc-2.3.3.gz
cd systemc-2.3.3.gz
sudo mkdir -p /usr/local/systemc-2.3.3
mkdir objdir
cd objdir
../configure --prefix=/usr/local/systemc-2.3.3
make -j 3
sudo make install

cd ~
git clone https://github.com/jmjos/ratatoskr.git
cd ratatoskr/simulator
build.sh
