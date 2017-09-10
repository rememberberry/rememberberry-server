FROM ubuntu:16.04
RUN apt-get update
RUN apt-get install -y software-properties-common python-software-properties
RUN apt-get -y install git
RUN add-apt-repository ppa:fkrull/deadsnakes
RUN apt update && apt upgrade
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

# Install rememberberry client and server and rememberscript

# This arg will invalidate the cache for next RUN
# Build with: docker build --build-arg CACHE_DATE=$(date) ....
ARG CACHE_DATE=1
RUN git clone https://github.com/rememberberry/rememberberry-server && pip3.6 install -r rememberberry-server/requirements.txt
RUN git clone https://github.com/rememberberry/rememberscript.git && pip3.6 install -r rememberscript/requirements.txt
RUN git clone https://github.com/rememberberry/rememberberry-client.git

# Set the cert path (need to volume map into this folder)
ENV REMEMBERBERRY_CERT_PATH /etc/letsencrypt/live/bot.rememberberry.com/

# Update python path
ENV PYTHONPATH=$PYTHONPATH:/rememberscript:/anki:/rememberberry-server

EXPOSE 443

CMD ["python3.6", "-m", "rememberberry.server"]