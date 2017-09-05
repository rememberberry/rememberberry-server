# Install Python3.6 and pip
apt update && apt upgrade
apt-get install python-software-properties
add-apt-repository ppa:fkrull/deadsnakes
apt update && apt upgrade
apt-get install python3.6
curl https://bootstrap.pypa.io/get-pip.py | sudo python3.6

# Install server requirements
pip3.6 install -r requirements.txt

# Install rememberscript and client
git clone https://github.com/rememberberry/rememberscript.git ../rememberscript
git clone https://github.com/rememberberry/rememberberry-client.git ../rememberberry-client

# Install Anki
git clone https://github.com/dae/anki.git ../anki
apt install python3.6-dev libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools
pip3.6 install -r ../anki/requirements.txt

# Update python path
echo export PYTHONPATH=$PYTHONPATH:/root/rememberscript:/root/anki >> /root/.profile
source /root/.profile

# Allocate swapfile
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon -s
