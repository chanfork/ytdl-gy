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
    nano && \
    apt-get clean
	
COPY requirements.txt Dockerfile /var/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /var/requirements.txt 
	
#ENTRYPOINT 	
#CMD bash /home/pysaweb/init.sh	
#CMD ["/bin/bash","--login","-c","bash"]
CMD ["/bin/bash","-c","bash"]