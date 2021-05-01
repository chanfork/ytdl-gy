# -*- coding: utf-8 -*-
import os
import sys
import argparse
import subprocess  as sp
import requests
from bs4 import BeautifulSoup as bs
import urllib.request
import json

###########################################################

class CmdArgs(object):
    """
    Normal:
        args = CmdArgs().args
        args = CmdArgs().args_dict       
    Test:
        args = CmdArgs(test_data=dict(data)).args
        args = CmdArgs(test_data=dict(data)).args_dict     
    """
    def __init__(self, test_data=''):
        self.test_data = test_data
        if test_data:            
           self.args = self.init_test_args() 
        else:
           self.args = self.init_argparse().parse_args() 
                                
    def init_argparse(self):
        parser = argparse.ArgumentParser(prog='ytdl-gy' ,description='ytdl for im')
        parser.add_argument('url', type=str,
                            help='the target url')
        parser.add_argument('--dry', action='store_true',
                            dest='dry_run',
                            help='show target-info only')
        parser.add_argument('--save-meta', action='store_true',
                            help='save target-info and thumbnail to file')     
        parser.add_argument('--mode', default='current', type=str,
                            choices=['all', 'current'],
                            help='work on playlist or current url')      
        parser.add_argument('--version', action='version', version='%(prog)s 0.2.0')
        return parser
    
    @property 
    def args_dict(self):
        if self.test_data:
           return self.args._asdict()
        else:
           return vars(self.args)
   
    def init_test_args(self):
        from collections import namedtuple      
        args = namedtuple('args', self.test_data.keys())        
        test_args = args._make(self.test_data.values())      
        return test_args   

#########################################################
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0'}    

def get_bs_html(url):
    req = requests.get(url,headers=headers)
    html = bs(req.text, 'lxml')
    #print(html.prettify())
    return html

def get_m3u8_luanch_url(m3u8_url):
    if 'http' not in m3u8_url: return m3u8_url
    req = urllib.request.Request(m3u8_url,headers=headers)    
    with urllib.request.urlopen(req) as response:
       m3u8 = response.read().decode('utf8').split('\n')
       m3u8_contents_url = m3u8[2] # last line
    m3u8_domain_name = '/'.join(m3u8_url.split('/')[0:3])  
    m3u8_luanch_url = m3u8_url if m3u8_contents_url.endswith('.m3u8') or len(m3u8) > 4 else m3u8_domain_name+m3u8_contents_url    
    return m3u8_luanch_url

def get_m3u8_vresolution(m3u8_url):
    if 'http' not in m3u8_url: return '-'  
    req = urllib.request.Request(m3u8_url,headers=headers)       
    with urllib.request.urlopen(req) as response:
       m3u8 = response.read().decode('utf8').split('\n')
       m3u8_vresolution = m3u8[1].split(',')[-1].replace('RESOLUTION=','') if 'RESOLUTION=' in m3u8[1] else ''  
    return m3u8_vresolution
    
def get_dl_directory(video_data_summarize,creat=False):
    dl_directory = os.path.join(os.getcwd(),video_data_summarize['title'])
    if creat and not os.path.exists(dl_directory): os.makedirs(dl_directory)     
    return dl_directory

def call_ytdl_do_job(url, save_directory, file_name='default', ytdl_path=os.path.join(os.getcwd(),'youtube-dl.exe')):
    # see https://github.com/ytdl-org/youtube-dl#output-template
    file_name = file_name+'.%(ext)s' if file_name != 'default' else '%(title)s-%(id)s.%(ext)s' 
    file_name = file_name+'.mp4' if file_name.endswith('.aspx') else file_name      
    ytdl_path = 'youtube-dl' if sys.platform.startswith('linux') else ytdl_path        
    cmd = [ytdl_path, '--user-agent', headers['User-Agent'], '-o', file_name, url]
    sp.run(cmd, cwd=save_directory, text=True,
           stdout=sys.stdout)

def dl_img(imgurl, save_directory):
    if imgurl == '': return
    file_name = imgurl.split('/')[-1]
    file_path = os.path.join(save_directory,file_name)
    req = urllib.request.Request(imgurl,headers=headers)
    with urllib.request.urlopen(req) as response:
        img = response.read()      
        with open(file_path, 'wb') as f:
             f.write(img)     
 
###########################################################
             
class VideoData(object):
    def __init__(self, url):
        self.url = url
        if 'v.com/ep' in url:
            self.server_type = 'S1'            
        elif 'm/video/' in url:
            self.server_type = 'S2'
        else: 
            assert False, 'The url could not in the support list'            

    def go(self):
        videodata_cls = {'S1':VideoDataS1, 
                         'S2':VideoDataS2}
        return videodata_cls[self.server_type](self.url)
                 
class VideoDataS1(object):
    def __init__(self, url):
        self.url = url
        self.bs_html = get_bs_html(url)
        self.key_word_inside_script_tag = 'var player_data='
        self.url_domain_name = '/'.join(self.url.split('/')[0:3])
        self.summarize = {}
       
    def find_vsource_data(self):
        """
        Search something like :
        S1 => <script type="text/javascript">var player_data={"flag":"play","encrypt":0,"trysee":0,"points":0,"link":"\/ep-119925-1-1.html","link_next":"\/ep-119925-2-4.html","link_pre":"\/ep-119925-2-2.html","url":"https:\/\/vod2.buycar5.cn\/20201018\/5XXa6aK3\/index.m3u8","url_next":"https:\/\/vod2.buycar5.cn\/20201025\/lN3hA88b\/index.m3u8","from":"dbm3u8","server":"no","note":"","id":"119925","sid":2,"nid":3}</script>
        S2 => <script type="text/javascript"> var cms_player = {"yun":true,"url":"https:\/\/mhyunbo.com\/20200117\/LhUDYEWk\/index.m3u8","copyright":0,"name":"mhm3u8"};</script>
        """
        the_script_tag_list = self.bs_html.select('script')
        assert the_script_tag_list, 'Could not find script tag' 
        for data in the_script_tag_list: # target in idx 13
            if data.string and self.key_word_inside_script_tag in data.string: # use .string to get contents inside script tag else ''
               target = data.string.replace(self.key_word_inside_script_tag,'').replace(';','')
               break
            else:
               target = ''     
        assert target, 'Could not find <%s> inside script tag'%self.key_word_inside_script_tag 
        return json.loads(target) 
   
    def find_vmeta_data(self):
        vmeta = {}
        vmeta['title'] = self.bs_html.find('title').text.strip().split(' ')[0]
        vmeta['title_ep'] = self.bs_html.find('title').text
        vmeta['img_url'] = self.bs_html.find("meta", property="og:image")['content'] if self.bs_html.find("meta", property="og:image") else ''
        vmeta['info'] = self.bs_html.find("span",{"class":"sketch content"}).text.strip() if self.bs_html.find("span",{"class":"sketch content"}) else ''
        return vmeta
    
    @property
    def get_summarize(self): 
        vsource = self.find_vsource_data()
        self.summarize = self.find_vmeta_data()
        self.summarize['m3u8_url'] = vsource['url']
        self.summarize['m3u8_next_url'] = vsource['url_next'] 
        self.summarize['m3u8_luanch_url'] = get_m3u8_luanch_url(vsource['url'])
        self.summarize['m3u8_vresolution'] = get_m3u8_vresolution(vsource['url'])
        
        if 'http' not in vsource['url']:
            new_url = self.url_domain_name+'/player/ana.php?url='+vsource['url']
            new_bs_html = get_bs_html(new_url)
            target = new_bs_html.find("iframe", {"class":'iframeStyle'})
            target_src = target['src']
            target_m3u8 = target_src.split('&groupid=')[0].replace(self.url_domain_name+'/player/?url=','')
            # print (target_m3u8)
            self.summarize['m3u8_luanch_url'] = target_m3u8
            
        return self.summarize     
                
    @property 
    def find_playlist_urls(self):
        playlist = self.bs_html.find('div',{"class":"tab-pane fade in active clearfix"})
        assert playlist, 'Could not find playlist' 
        playlist_urls = playlist.find_all('a')
        assert playlist_urls, 'Could not find urls in this playlist'
        self.playlist_urls = [self.url_domain_name+item['href'] for item in playlist_urls]
        return self.playlist_urls

    def save_to_file(self, video_data_summarize=''):        
        if video_data_summarize == '':
           video_data_summarize = self.summarize            
        dl_directory = get_dl_directory(video_data_summarize, creat= True)
        file_path = os.path.join(dl_directory,'[ytdl-gy]info.txt') 
        with open(file_path,'w',encoding='utf8') as f:
            for key,value in video_data_summarize.items():
                f.write('# %s : \n'%key)
                f.write('  %s \n'%value)  
                             
###########################################################
                
class VideoDataS2(VideoDataS1):
    def __init__(self, url):
        super().__init__(url)
        self.key_word_inside_script_tag = 'var cms_player = '
                
    def find_vmeta_data(self):
        vmeta = {}
        vmeta['title'] = self.bs_html.find('title').text.strip().split(' ')[0]
        vmeta['title_ep'] = self.bs_html.find('title').text
        vmeta['info'] = self.bs_html.find("div",{"class":"stui-content__desc"}).text.strip() if self.bs_html.find("div",{"class":"stui-content__desc"}) else ''
        vmeta['img_url'] = self.bs_html.find("meta", property="og:image")['content'] if self.bs_html.find("meta", property="og:image") else ''
        upper_level_url = '/'.join(self.url.split('/')[:-1])+'.html'
        img_url = get_bs_html(upper_level_url).find("img", {"class":"img-responsive ff-img"})
        vmeta['img_url'] = self.url_domain_name+img_url['data-original'] if img_url else ''
        return vmeta
    
    @property
    def get_summarize(self): 
        vsource = self.find_vsource_data()
        self.summarize = self.find_vmeta_data()
        self.summarize['m3u8_url'] = vsource['url']  
        self.summarize['m3u8_next_url'] = vsource['next_url']
        self.summarize['m3u8_luanch_url'] = get_m3u8_luanch_url(vsource['url'])
        return self.summarize     
                
    @property 
    def find_playlist_urls(self): 
        playlist = self.bs_html.find_all('ul',{"class":"stui-content__playlist clearfix"})
        assert playlist, 'Could not find playlist from any source' 
        target_source = int(self.url.split('/')[-1].split('-')[0])
        assert len(playlist) >= target_source, 'Could not find source %d in playlist'%target_source       
        for i in playlist:
            try:
              i_source = int(i.find('a')['href'].split('/')[-1].split('-')[0]) 
            except:
              assert False, 'Could not find i_source in this playlist'             
            if i_source == target_source:
               playlist_urls = i.find_all('a')
               break
            else:
               playlist_urls = [] 
        assert playlist_urls, 'Could not find currect urls in this playlist'
        self.playlist_urls = [self.url_domain_name+item['href'] for item in playlist_urls]
        return self.playlist_urls

###########################################################

class MainTask(object):
    def __init__(self, args):
        self.args = args
        print ('[ytdl-gy] Run in %s of %s...'%( 'DRY' if args.dry_run else 'DL',args.mode.upper() ) )
        user_chk = input('[ytdl-gy] Do you want to continue in DL mode [y/n]?') if args.dry_run != True else 'y'   
        while user_chk != 'y' and user_chk != 'n':
           user_chk = input('[ytdl-gy] Do you want to continue in DL mode [y/n]?') 
               
        if user_chk == 'y':
           if args.mode == 'current': self.mode_current() 
           if args.mode == 'all': self.mode_all()         
        else:
           print ("[ytdl-gy] ByeBye") 
      
    def show_video_data_summarize(self):
        print ('[ytdl-gy] Show video_data_summarize : ') 
        for key,value in self.video_data_summarize.items():
            print ('[ytdl-gy]   {}  =>  {}'.format(key,value))        
        
    def mode_current(self):
        self.video_data = VideoData(self.args.url).go()
        self.video_data_summarize = self.video_data.get_summarize           
        if self.args.dry_run:                    
           self.show_video_data_summarize()
        else:
           dl_directory = get_dl_directory(self.video_data_summarize, creat= not self.args.dry_run)            
           print ('[ytdl-gy] Start to DL : ', self.video_data_summarize['title_ep'])                             
           call_ytdl_do_job(self.video_data_summarize['m3u8_luanch_url'], dl_directory, file_name=self.video_data_summarize['title_ep'])         
           print ("[ytdl-gy] DL Done !!")
        if args.save_meta:
           print ('[ytdl-gy] Saving summarize to file') 
           self.video_data.save_to_file()
           dl_img(self.video_data_summarize['img_url'], get_dl_directory(self.video_data_summarize))                   
        print ('[ytdl-gy] All Done!!')           
 
    def get_m3u8_luanch_list_and_summarize_list(self):
        print ('[ytdl-gy] Get m3u8_luanch_list : ')
        self.summarize_list = []
        self.m3u8_luanch_list = []           
        for url in self.video_data_summarize['playlist_urls']:
            video_data = VideoData(url).go()
            video_data_summarize = video_data.get_summarize  
            self.summarize_list.append(video_data_summarize)
            self.m3u8_luanch_list.append(video_data_summarize['m3u8_luanch_url'])
            print ('[ytdl-gy]   '+ video_data_summarize['m3u8_luanch_url'])        
        self.video_data_summarize['m3u8_luanch_list'] = self.m3u8_luanch_list
                    
    def mode_all(self):
        self.video_data = VideoData(self.args.url).go()
        self.video_data_summarize = self.video_data.get_summarize       
        self.video_data_summarize['playlist_urls'] = self.video_data.find_playlist_urls      
        if self.args.dry_run:           
           self.show_video_data_summarize()
           self.get_m3u8_luanch_list_and_summarize_list() 
        else:
           self.get_m3u8_luanch_list_and_summarize_list()
           dl_directory = get_dl_directory(self.video_data_summarize, creat= not self.args.dry_run)
           play_counts = len(self.m3u8_luanch_list)
           for i in range(play_counts):
               print ('[ytdl-gy] Start to DL %d of %d : '%(i+1,play_counts), self.summarize_list[i]['title_ep'])                 
               call_ytdl_do_job(self.m3u8_luanch_list[i], dl_directory, file_name=self.summarize_list[i]['title_ep'])         
           print ('[ytdl-gy] DL done!!')           
        if args.save_meta:
           print ('[ytdl-gy] Saving summarize to file') 
           self.video_data.save_to_file(self.video_data_summarize)
           dl_img(self.video_data_summarize['img_url'], get_dl_directory(self.video_data_summarize))           
        print ('[ytdl-gy] All Done!!') 
  
###########################################################

if __name__ == '__main__':  
   args = CmdArgs().args
   MainTask(args) 

#   test_data = {'url':'',
#                'dry_run':False,
#                'save_meta':False,
#                'mode':'current'}          
#   args = CmdArgs(test_data=test_data).args   
#   MainTask(args)     
    


