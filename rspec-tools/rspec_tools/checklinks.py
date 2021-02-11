import os,io
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.request import urlopen,Request
from urllib.error import URLError,HTTPError
import pathlib

def show_files(filenames):
  for filename in filenames:
    print(filename)

def live_url(filenames,url):
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
      show_files(filenames)
      return False
    else:
      return True  
  except HTTPError as h:
    print(f"ERROR: {h.code} {h.reason}")
    show_files(filenames)
    return False
  except URLError as e:
    print(f"ERROR: {e.reason}")
    show_files(filenames)
    return False
  except ConnectionError as c:
    print(f"ERROR: connection error {c}")
    show_files(filenames)
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
  ok=True
  urls={}
  print("Finding links in html files")
  for filepath in pathlib.Path(dir).glob('**/*.html'):
    filename=str(filepath.absolute())
    findurl_in_html(filename,urls):
  print("All html files crawled")
  print("Testing links")
  for key in urls:
    print(f"{key} in {len(urls[key])} files")
    ok=ok and live_url(urls[key],key)
  if not ok:
    print("There were errors")
    exit(error_code)
  else:
    print("All links are good")

  


