import os,io
import re
import urllib.request
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.request import urlopen,Request
from urllib.error import URLError,HTTPError
from socket import timeout
import pathlib
from http.cookiejar import CookieJar

def show_files(filenames):
  for filename in filenames:
    print(filename)

def live_url(url: str):
  if url.startswith('#'):
    return True

  code=None
  req = Request(
    url, 
    data=None, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }    
  )
  try:
    req=urllib.request.Request(url, None, {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; G518Rco3Yp0uLV40Lcc9hAzC1BOROTJADjicLjOmlr4=) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
                                           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                                           'Accept-Encoding': 'gzip, deflate, sdch',
                                           'Accept-Language': 'en-US,en;q=0.8',
                                           'Connection': 'keep-alive'})
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    code = opener.open(req, timeout=5).code
    if (code / 100 >= 4):
      print(f"ERROR: {code} Nothing there")
      return False
    else:
      return True
  except HTTPError as h:
    print(f"ERROR: {h.code} {h.reason}")
    return False
  except URLError as e:
    print(f"ERROR: {e.reason}")
    return False
  except ConnectionError as c:
    print(f"ERROR: connection error {c}")
    return False
  except timeout as t:
    print(f"ERROR: timeout ", t)
    return False
  except Exception as e:
    print(f"ERROR: ", e)
    return False

def findurl_in_html(filename,urls):    
  with open(filename, 'r', encoding="utf8") as file:
    soup = BeautifulSoup(file,features="html.parser")
    for link in soup.findAll('a'):
      key=link.get('href')
      if key in urls:
        urls[key].append(filename)
      else:
        urls[key]=[filename]

def is_active(metadata_fname, generic_metadata_fname):
  try:
    with open(metadata_fname) as metadata_file:
      metadata = json.load(metadata_file)
      if 'status' in metadata:
        return metadata['status'] == 'ready'
    with open(generic_metadata_fname) as generic_metadata_file:
      generic_metdata = json.load(generic_metadata_file)
      if 'status' in generic_metdata:
        return generic_metdata['status'] == 'ready'
  except EnvironmentError:
    return True
  return True

def check_html_links(dir):  
  urls={}
  errors=[]
  print("Finding links in html files")
  tot_files = 0
  for rulepath in pathlib.Path(dir).iterdir():
    if rulepath.is_dir():
      generic_metadata=rulepath.joinpath('metadata.json')
      for langpath in rulepath.iterdir():
        if langpath.is_dir():
          metadata=langpath.joinpath('metadata.json')
          filepath=langpath.joinpath('rule.html')
          filename=str(filepath.absolute())
          if filepath.exists() and is_active(metadata, generic_metadata):
            tot_files += 1
            findurl_in_html(filename,urls)
  print("All html files crawled")
  print("Testing links")
  for url in urls:
    print(f"{url} in {len(urls[url])} files")
    if not live_url(url):
      errors.append(url)
  if errors:
    print("There were errors")
    for key in errors:
      print(f"{key} in:") 
      show_files(urls[key])
    print(f"{len(errors)}/{len(urls)} links are dead, see the list and related files before")
    exit(1)
  else:
    print(f"All {len(urls)} links are good")

  


