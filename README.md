# ytdl-gy

![](https://github.com/chanfork/ytdl-gy/blob/2445104d501ab32fcc81397716c2ed5666893d40/demo1.png?raw=true)



## Setup

- Use `ytdl-gy.py` directly: 

  ```bash
  # requirements : python 3.7+ and ffmpeg
  git clone https://github.com/chanfork/ytdl-gy.git
  pip install -r requirements.txt
  ```

OR

- Use `Dockerfile`  :

  ```bash
  git clone https://github.com/chanfork/ytdl-gy.git
  docker build -t <the_img_name> .
  docker run --name <the_container_name> -it -v <the_local_empty_dire>:/home/ytdl-gy <the_img_name>
  # user should mount a local EMPTY directory to /home/ytdl-gy, so the source code will be installed(clone) into it.
  ```


## Usage

- Run  `python ytdl-gy.py <url> <options>` 

- The `<url>` should  contain one of the following text : 

  ```
  'v.com/ep'
  'm/video/'
  ```
  
  
