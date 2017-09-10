FROM ubuntu:16.04
RUN apt-get update
RUN apt-get install -y software-properties-common python-software-properties
RUN apt-get -y install git
RUN add-apt-repository ppa:fkrull/deadsnakes
RUN apt update && apt upgrade
RUN apt-get install -y python3.6 curl
RUN curl https://bootstrap.pypa.io/get-pip.py | python3.6

RUN git clone https://github.com/rememberberry/rememberberry-server

# Install server requirements
RUN pip3.6 install -r rememberberry-server/requirements.txt

# Install rememberscript and client
RUN git clone https://github.com/rememberberry/rememberscript.git
RUN pip3.6 install -r rememberscript/requirements.txt
RUN git clone https://github.com/rememberberry/rememberberry-client.git

# Install Anki
RUN git clone https://github.com/dae/anki.git
RUN apt install -y python3.6-dev libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg libav-tools
RUN pip3.6 install -r anki/requirements.txt

# Update python path
ENV PYTHONPATH=$PYTHONPATH:/rememberscript:/anki:/rememberberry-server

# Set the locale (needed for Anki)
RUN apt-get -y install locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Set the cert path (need to volume map into this folder)
ENV REMEMBERBERRY_CERT_PATH /certs/

CMD ["python3.6", "-m", "rememberberry.server"]
