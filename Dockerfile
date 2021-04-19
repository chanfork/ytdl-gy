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
    nano && \
    apt-get clean

COPY requirements.txt /var/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /var/requirements.txt 
	
#ENTRYPOINT 	

CMD ["/bin/bash","-c","git clone https://github.com/chanfork/ytdl-gy.git /home/ytdl-gy && cd /home/ytdl-gy && bash"]
