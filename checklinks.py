import os,io
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import URLError

error=0

def live_url(url):
  try:
    code = urlopen(url).code  
    if (code / 100 >= 4):
      print(f"Nothing there: {url}")
      error=1
    else:
      print(f"Ok: {url}")
  except URLError:
    print(f"Could not access: {url}")
    error=1

def findurl_in_html(filename):
  with io.open(filename, 'r', encoding="utf8") as file:
    soup = BeautifulSoup(file)
    for link in soup.findAll('a'):
      live_url(link.get('href'))


for directory, dirnames, filenames in os.walk("."):
  for filename in filenames:
    if filename.endswith('.html'):
      findurl_in_html(os.path.join(directory,filename))
if error == 1:
  exit(1)


