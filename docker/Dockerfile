# Notes:
# Volume map 
#  * ~/.ipfs/ to /root/.ipfs
# /etc/letsencrypt/bot.rememberberry/ is copied from host to image at build time
# Build with: docker build --build-arg CACHE_DATE=$(date) -t rememberberry .

FROM ubuntu:16.04
RUN apt-get -y update
RUN apt-get install -y software-properties-common python-software-properties
RUN apt-get -y install git
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt -y update && apt -y upgrade
RUN apt-get install -y python3.6 curl
RUN curl https://bootstrap.pypa.io/get-pip.py | python3.6

# Set the locale (needed for Anki)
RUN apt-get -y install locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install Anki
RUN git clone https://github.com/dae/anki.git
RUN apt install -y python3.6-dev libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools
RUN pip3.6 install -r anki/requirements.txt

# Install IPFS
RUN curl -O https://ipfs.io/ipns/dist.ipfs.io/go-ipfs/v0.4.12/go-ipfs_v0.4.12_linux-amd64.tar.gz && \
    tar -xvf go-ipfs_v0.4.12_linux-amd64.tar.gz && \
    cd go-ipfs && \
    ./install.sh

# Install fuse and prepare for ipfs/ipns mounting
RUN apt-get -y install fuse && \
    addgroup fuse && \
    chgrp fuse /etc/fuse.conf && \
    chmod g+r  /etc/fuse.conf && \
    usermod -a -G fuse root && \
    mkdir /ipfs /ipns && \
    chown root /ipfs && \
    chown root /ipns

# Install rememberberry client and server and rememberscript

# This arg will invalidate the cache for next RUN
# Build with: docker build --build-arg CACHE_DATE=$(date) ....
ARG CACHE_DATE=1
RUN git clone https://github.com/rememberberry/rememberberry-server && pip3.6 install -r rememberberry-server/requirements.txt
RUN git clone https://github.com/rememberberry/rememberscript.git && pip3.6 install -r rememberscript/requirements.txt
RUN git clone https://github.com/rememberberry/rememberberry-client.git

# Copy the certs from the host
COPY certs /etc/letsencrypt/live/bot.rememberberry.com/

# Set the cert path (need to volume map into this folder)
ENV REMEMBERBERRY_CERT_PATH /etc/letsencrypt/live/bot.rememberberry.com/

# Update python path
ENV PYTHONPATH=$PYTHONPATH:/rememberscript:/anki:/rememberberry-server

EXPOSE 80 443

# Run ipfs daemon and rememberberry server
ENTRYPOINT ["bash", "/rememberberry-server/run.sh"]
