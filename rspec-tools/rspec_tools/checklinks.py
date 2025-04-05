import datetime
import json
import pathlib
import random
import socket

import requests
from bs4 import BeautifulSoup

TOLERABLE_LINK_DOWNTIME = datetime.timedelta(days=7)
LINK_PROBES_HISTORY_FILE = "./link_probes.history"
PROBING_COOLDOWN = datetime.timedelta(days=2)
PROBING_SPREAD = 60 * 24  # in minutes, 1 day
link_probes_history = {}

# These links consistently fail in CI, but work-on-my-machine
EXCEPTION_PREFIXES = [
    # It seems the server certificate was renewed on 2nd of August 2024.
    # The server is sending only its certificate, without including the
    # Intermediate certificate used to issue the server cert. Because of that
    # some application are not able to verify the complete chain of trust.
    "https://wiki.sei.cmu.edu/",
    # The CI reports 403 on drupal.org while it works locally.
    # Maybe the CI's IP is blocklisted...
    "https://www.drupal.org/",
]


def show_files(file_entries):
    for entry in file_entries:
        # Prefer showing the original .adoc file if available
        if "adoc" in entry:
            print(entry["adoc"])
        else:
            print(entry["html"])


def load_url_probing_history():
    global link_probes_history
    try:
        with open(LINK_PROBES_HISTORY_FILE, "r") as link_probes_history_stream:
            print(
                "Using the historical url-probe results from "
                + LINK_PROBES_HISTORY_FILE
            )
            link_probes_history = eval(link_probes_history_stream.read())
    except Exception as e:
        # If the history file is not present, ignore, will create one in the end.
        print(f"Failed to load historical url-probe results: {e}")


def save_url_probing_history():
    global link_probes_history
    with open(LINK_PROBES_HISTORY_FILE, "w") as link_probes_history_stream:
        link_probes_history_stream.write(str(link_probes_history))


def rejuvenate_url(url: str):
    global link_probes_history
    link_probes_history[url] = datetime.datetime.now()


def url_is_long_dead(url: str):
    global link_probes_history
    if url not in link_probes_history:
        return True
    last_time_up = link_probes_history[url]
    print(f"{url} was reached most recently on {last_time_up}")
    return TOLERABLE_LINK_DOWNTIME < (datetime.datetime.now() - last_time_up)


def url_was_reached_recently(url: str):
    global link_probes_history
    if url not in link_probes_history:
        return False
    last_time_up = link_probes_history[url]
    spread = random.randrange(PROBING_SPREAD)
    probing_cooldown = PROBING_COOLDOWN + datetime.timedelta(minutes=spread)
    return (datetime.datetime.now() - last_time_up) < probing_cooldown


def live_url(url: str, timeout=5):
    if url.startswith("#"):
        return True
    try:
        req = requests.Request(
            "GET",
            url,
            headers={
                "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90"',
                "sec-ch-ua-mobile": "?0",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 GLS/100.10.9939.100",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            },
        )
        session = requests.Session()
        prepped = session.prepare_request(req)
        settings = session.merge_environment_settings(prepped.url, {}, None, None, None)
        code = session.send(prepped, timeout=timeout, **settings).status_code
        if code / 100 >= 4:
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
        print(f"ERROR: Request timeout {t}")
        return False
    except socket.timeout as t:
        print(f"ERROR: Socket timeout {t}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def findurl_in_html(filename, urls, rules_dir=None, output_dir=None):
    with open(filename, "r", encoding="utf8") as file:
        soup = BeautifulSoup(file, features="html.parser")
        for link in soup.find_all("a"):
            key = link.get("href")

            # Track both HTML file and the original adoc file if possible
            file_entry = {"html": filename}

            # If rules_dir and output_dir are provided, calculate the original adoc file
            if rules_dir and output_dir:
                try:
                    # Make sure we have absolute paths for proper resolution
                    abs_filename = pathlib.Path(filename).absolute()
                    abs_output_dir = pathlib.Path(output_dir).absolute()
                    abs_rules_dir = pathlib.Path(rules_dir).absolute()

                    # Convert output/S123/java/rule.html -> rules/S123/java/rule.adoc
                    rel_path = abs_filename.relative_to(abs_output_dir)
                    rel_path = rel_path.with_suffix(".adoc")
                    original_file = abs_rules_dir / rel_path
                    if original_file.exists():
                        file_entry["adoc"] = str(original_file)
                except ValueError as e:
                    print(f"Path resolution error (will use HTML path): {e}")

            if key in urls:
                urls[key].append(file_entry)
            else:
                urls[key] = [file_entry]


def is_active(metadata_fname, generic_metadata_fname):
    try:
        with open(metadata_fname) as metadata_file:
            metadata = json.load(metadata_file)
            if "status" in metadata:
                return metadata["status"] == "ready"
        with open(generic_metadata_fname) as generic_metadata_file:
            generic_metdata = json.load(generic_metadata_file)
            if "status" in generic_metdata:
                return generic_metdata["status"] == "ready"
    except EnvironmentError:
        return True
    return True


def get_all_links_from_htmls(output_dir, rules_dir=None):
    print("Finding links in html files")
    urls = {}
    for rulepath in pathlib.Path(output_dir).iterdir():
        if not rulepath.is_dir():
            continue
        generic_metadata = rulepath.joinpath("metadata.json")
        for langpath in rulepath.iterdir():
            if not langpath.is_dir():
                continue
            metadata = langpath.joinpath("metadata.json")
            filepath = langpath.joinpath("rule.html")
            filename = str(filepath.absolute())
            if filepath.exists() and is_active(metadata, generic_metadata):
                findurl_in_html(filename, urls, rules_dir, output_dir)
    print("All html files crawled")
    return urls


def url_is_exception(url: str) -> bool:
    return any(url.startswith(e) for e in EXCEPTION_PREFIXES)


def collect_broken_links(urls: dict) -> tuple[list[str], dict[str, int]]:
    """
    Collect a list of broken links and cache statistics
    
    Args:
        urls: Dictionary of URLs to check, where keys are URLs and values are lists of file entries
    
    Returns:
        tuple: (list of broken URLs, dictionary of cache statistics)
    """
    errors = []
    cache_stats = {
        "link_cache_exception": 0,
        "link_cache_hit": 0,
        "link_cache_miss": 0
    }
    
    print("Testing links")
    link_count = len(urls)
    for idx, url in enumerate(urls):
        print(f"[{idx+1}/{link_count}] {url} in {len(urls[url])} files")
        if url_is_exception(url):
            cache_stats["link_cache_exception"] += 1
            print("skip as an exception")
        elif url_was_reached_recently(url):
            cache_stats["link_cache_hit"] += 1
            print("skip probing because it was reached recently")
        elif live_url(url, timeout=5):
            cache_stats["link_cache_miss"] += 1
            rejuvenate_url(url)
        elif url_is_long_dead(url):
            cache_stats["link_cache_miss"] += 1
            errors.append(url)
        else:
            cache_stats["link_cache_miss"] += 1
            
    return errors, cache_stats


def probe_links(urls: dict) -> bool:
    """
    Check all links and report any issues
    
    Args:
        urls: Dictionary of URLs to check, where keys are URLs and values are lists of file entries
    
    Returns:
        bool: True if all links are valid, False otherwise
    """
    errors, cache_stats = collect_broken_links(urls)
    confirmed_errors = confirm_errors(errors, urls)

    print(f"\n\n\n{'=' * 80}\n\n\n")
    if confirmed_errors:
        report_errors(confirmed_errors, urls)
        print(
            f"{len(confirmed_errors)}/{len(urls)} links are dead, see above ^^ the list and the related files\n\n"
        )
    
    # Extract cache statistics
    link_cache_hit = cache_stats["link_cache_hit"]
    link_cache_miss = cache_stats["link_cache_miss"]
    link_cache_exception = cache_stats["link_cache_exception"]
    
    print("Cache statistics:")
    print(f"\t{link_cache_hit=}")
    print(f"\t{link_cache_miss=}")
    if link_cache_hit + link_cache_miss > 0:
        link_cache_hit_ratio = link_cache_hit / (link_cache_hit + link_cache_miss)
        print(f"\t{link_cache_hit_ratio:03.2%} hits")
    print(f"\t{link_cache_exception=}")
    print(f"\n\n\n{'=' * 80}\n\n\n")

    success = len(confirmed_errors) == 0
    return success


def confirm_errors(presumed_errors, urls):
    confirmed_errors = []
    print(f"Retrying {len(presumed_errors)} failed probes")
    for key in presumed_errors:
        print(f"{key} in {len(urls[key])} files (previously failed)")
        if not live_url(key, timeout=15):
            confirmed_errors.append(key)
        else:
            rejuvenate_url(key)
    return confirmed_errors


def report_errors(errors, urls):
    print("There were errors")
    for key in errors:
        print(f"{key} in:")
        for file_entry in urls[key]:
            # Use the original .adoc file if available, otherwise use the HTML file
            if "adoc" in file_entry:
                print(file_entry["adoc"])
            else:
                print(file_entry["html"])


def check_html_links(output_dir, rules_dir=None):
    load_url_probing_history()
    urls = get_all_links_from_htmls(output_dir, rules_dir)
    success = probe_links(urls)
    if success:
        print(f"All {len(urls)} links are good")
    save_url_probing_history()
    exit(0 if success else 1)
