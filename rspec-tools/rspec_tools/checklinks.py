import os,io
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.request import urlopen,Request
from urllib.error import URLError,HTTPError

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

def findurl_in_html(filename):
  error=0
  with open(filename, 'r', encoding="utf8") as file:
    soup = BeautifulSoup(file,features="html.parser")
    for link in soup.findAll('a'):
      if not live_url(filename,link.get('href')):
        error=1
  exit(error)

def check_html_links(dir):
  print(f"Checking {dir}")
  for directory, dirnames, filenames in os.walk(dir):
    for filename in filenames:
      if filename.endswith('.html'):
        findurl_in_html(os.path.join(directory,filename))

  


