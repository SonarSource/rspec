import os,io
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import URLError

error=0

def live_url(url):
  code=None
  try:
    code = urlopen(url).code  
    if (code / 100 >= 4):
      print(f"Ko: {code} Nothing there: {url}")
      return False
    else:
      print(f"Ok: {url}")
      return True
  except URLError:
    print(f"Ko: {code} Could not access: {url}")
    return False

def findurl_in_html(filename, pr: bool=False):
  with io.open(filename, 'r', encoding="utf8") as file:
    soup = BeautifulSoup(file,features="html.parser")
    for link in soup.findAll('a'):
      if not live_url(link.get('href')) and pr:
        exit(1)


for directory, dirnames, filenames in os.walk("."):
  for filename in filenames:
    if filename.endswith('.html'):
      findurl_in_html(os.path.join(directory,filename))

  


