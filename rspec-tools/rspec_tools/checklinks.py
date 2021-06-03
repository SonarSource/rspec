import os,io
import re
import requests
import json
from bs4 import BeautifulSoup
from socket import timeout
from datetime import datetime, timedelta
import pathlib

TOLERABLE_LINK_DOWNTIME = timedelta(days=7)
LINK_PROBES_HISTORY_FILE = 'link_probes.history'
link_probes_history = {}

# These links consistently fail in CI, but work-on-my-machine
EXCEPTIONS = ['https://blogs.oracle.com/java-platform-group/diagnosing-tls,-ssl,-and-https',
              'https://blogs.oracle.com/oraclemagazine/oracle-10g-adds-more-to-forall',
              'https://www.fluentcpp.com/2017/09/08/make-polymorphic-copy-modern-cpp/',
              'https://www.fluentcpp.com/2016/12/08/strong-types-for-strong-interfaces/']

def show_files(filenames):
  for filename in filenames:
    print(filename)

def load_url_probing_history():
    global link_probes_history
    try:
        with open(LINK_PROBES_HISTORY_FILE, 'r') as link_probes_history_stream:
            print('Using the historical url probe results from ' + LINK_PROBES_HISTORY_FILE)
            link_probes_history = eval(link_probes_history_stream.read())
    except Exception:
        # If the history file is not present, ignore, will create one in the end.
        pass

def save_url_probing_history():
    global link_probes_history
    with open(LINK_PROBES_HISTORY_FILE, 'w') as link_probes_history_stream:
        link_probes_history_stream.write(str(link_probes_history))

def rejuvenate_url(url: str):
  global link_probes_history
  link_probes_history[url] = datetime.now()

def url_is_long_dead(url: str):
  global link_probes_history
  if url not in link_probes_history:
    return True
  last_time_up = link_probes_history[url]
  print(f"{url} was reached most recently on {last_time_up}")
  return TOLERABLE_LINK_DOWNTIME < (datetime.now() - last_time_up)

def live_url(url: str, timeout=5):
  if url.startswith('#'):
    return True
  if url in EXCEPTIONS:
    return True
  try:
    req = requests.Request('GET', url, headers = {'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90"',
                                                  'sec-ch-ua-mobile': '?0',
                                                  'Upgrade-Insecure-Requests': '1',
                                                  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
                                                  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3,q=0.9',
                                                  'Sec-Fetch-Site':'none',
                                                  'Sec-Fetch-Mode':'navigate',
                                                  'Sec-Fetch-User':'?1',
                                                  'Sec-Fetch-Dest':'document',
                                                  'Accept-Encoding': 'gzip, deflate, br',
                                                  'Accept-Language': 'en-US,en;q=0.9',
                                                  'Connection': 'keep-alive'})
    session = requests.Session()
    code = session.send(req.prepare(), timeout=timeout).status_code
    if (code / 100 >= 4):
      print(f"ERROR: {code} Nothing there")
      return False
    else:
      return True
  except requests.ConnectionError as ce:
    print(f"ERROR: Connection error {ce}")
    return False
  except requests.HTTPError as h:
    print(f"ERROR: HTTP error {h}")
    return False
  except requests.URLRequired as e:
    print(f"ERROR: Bad URL: {e}")
    return False
  except requests.TooManyRedirects as rr:
    print(f"ERROR: Too many redirects: {rr}")
    return False
  except requests.Timeout as t:
    print(f"ERROR: timeout ", t)
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
    if live_url(url, timeout=5):
      rejuvenate_url(url)
    elif url_is_long_dead(url):
      errors.append(url)
  if errors:
    confirmed_errors=[]
    print(f"Retrying {len(errors)} failed probes")
    for key in errors:
      print(f"{key} in {len(urls[key])} files (previously failed)")
      if not live_url(key, timeout=15):
        confirmed_errors.append(key)
    if confirmed_errors:
      print("There were errors")
      for key in confirmed_errors:
        print(f"{key} in:")
        show_files(urls[key])
      print(f"{len(confirmed_errors)}/{len(urls)} links are dead, see the list and related files before")
      exit(1)
  print(f"All {len(urls)} links are good")

