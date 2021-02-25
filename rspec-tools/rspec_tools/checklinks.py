import os,io
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.request import urlopen,Request
from urllib.error import URLError,HTTPError
from socket import timeout
import pathlib

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
    code = urlopen(req,timeout=5).code  
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

def check_html_links(dir):  
  urls={}
  errors=[]
  print("Finding links in html files")
  for filepath in pathlib.Path(dir).glob('**/*.html'):
    filename=str(filepath.absolute())
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

  


