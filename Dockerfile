FROM python:3.8.8
MAINTAINER chanfork
LABEL description="ytdl-gy"

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
	git \
	ssh \
	supervisor \
	ffmpeg \
	tmux \
	rsync \
	libxml2-dev \
	libxslt1-dev \
    nano && \
    apt-get clean

COPY requirements.txt /var/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /var/requirements.txt 
	
#ENTRYPOINT

CMD ["/bin/bash","-c","cd /home/ytdl-gy && test -f ytdl-gy.py && bash || { git clone https://github.com/chanfork/ytdl-gy.git /tmp/ytdl-gy; cp /tmp/ytdl-gy/ytdl-gy.py /home/ytdl-gy/; rm -r /tmp/ytdl-gy; bash; }"]
