import os,io
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.request import urlopen,Request
from urllib.error import URLError,HTTPError
import pathlib


def live_url(filename,url):
  code=None
  req = Request(
    url, 
    data=None, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }
  )
  try:
    code = urlopen(req).code  
    if (code / 100 >= 4):
      print(f"Ko: {filename} {code} Nothing there: {url}")
      return False
    else:
      print(f"Ok: {url}")
      return True  
  except HTTPError as h:
    print(f"Ko: {filename} {h.code} {h.reason} {url}")
    return False
  except URLError as e:
    print(f"Ko: {filename} {e.reason} {url}")
    return False
  except ConnectionError as c:
    print(f"Ko: {filename} {url} connection error {c}")
    return False

def findurl_in_html(filename):    
  ok=True
  with open(filename, 'r', encoding="utf8") as file:
    soup = BeautifulSoup(file,features="html.parser")
    for link in soup.findAll('a'):
      ok=ok and live_url(filename,link.get('href'))
  return ok
  

def check_html_links(dir):  
  error_code=0
  for filepath in pathlib.Path(dir).glob('**/*.html'):
    filename=str(filepath.absolute())
    if not findurl_in_html(filename):
      error_code=1
  exit(error_code)

  


