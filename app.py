from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import traceback
import os
from urllib.parse import urlparse, parse_qs, urlunparse
import random
from pymongo import MongoClient
import chromedriver_autoinstaller

app = Flask(__name__)


# Configure MongoDB Atlas connection using the environment variable MONGO_URI
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://HassanAli:devil14494%23D@movies-database.mqbrfms.mongodb.net/?retryWrites=true&w=majority&appName=movies-database"
)
client = MongoClient(MONGO_URI)

client = MongoClient(MONGO_URI)
db = client["stream_db"]
collection = db["streams"]

def extract_key_from_url(video_url: str) -> str:
    """
    For TV shows: key = "tv_<tmdb>_<season>_<episode>"
    For movies: key = "movie_<tmdb>"
    """
    parsed = urlparse(video_url)
    qs = parse_qs(parsed.query)
    tmdb = qs.get("tmdb", [None])[0]
    season = qs.get("season", [None])[0]
    episode = qs.get("episode", [None])[0]

    if season and episode:
        key = f"tv_{tmdb}_{season}_{episode}"
    else:
        key = f"movie_{tmdb}"
    return key

def store_streams_in_db(video_url: str, streams: list):
    key = extract_key_from_url(video_url)
    document = {
        "key": key,
        "video_url": video_url,
        "streams": streams,
    }
    print(f"Storing Streams in MONGODB: {document}")
    # Upsert document using the key
    collection.update_one({"key": key}, {"$set": document}, upsert=True)

def get_stream_urls_from_tmdb(video_url: str, max_retries: int = 2) -> list:
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    }
    session.headers.update(headers)

    def fetch_iframe_url():
        try:
            # Randomly select a domain from the list
            domains = ["vidsrc.in", "vidsrc.pm", "vidsrc.xyz", "vidsrc.net"]
            chosen_domain = random.choice(domains)

            # Parse the incoming video_url
            parsed = urlparse(video_url)
            # Replace the network location with the chosen domain
            new_netloc = chosen_domain
            # Rebuild the URL with the new domain
            main_url = urlunparse((parsed.scheme, new_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
            
            print(f"Fetching main page from randomized domain: {main_url}")
            # Using ScrapeOps proxy to bypass possible bot protections (optional)
            response = session.get(
                url='https://proxy.scrapeops.io/v1/',
                params={
                    'api_key': '1554506a-4725-4f50-a37d-6fa8624a4539',
                    'url': main_url, 
                },
                timeout=60
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            # Look for the iframe with id "player_iframe"
            iframe = soup.find('iframe', {'id': 'player_iframe'})
            if iframe:
                iframe_src = iframe.get('src')
                if iframe_src.startswith('//'):
                    iframe_src = 'https:' + iframe_src
                return iframe_src
            else:
                print("No iframe found in main page.")
            return None
        except Exception as e:
            print("Error fetching iframe URL:")
            traceback.print_exc()
            return None


    def fetch_streams(iframe_url):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")  # Bypass OS security model
        options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource issues
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        found_streams = set()
        driver = None
        try:
            print(f"Opening iframe URL in Selenium: {iframe_url}")
            driver = webdriver.Chrome(options=options)
            driver.get(iframe_url)
            driver.execute_script("window.open = function() { console.log('Blocked window.open'); };")
            body = driver.find_element(By.TAG_NAME, "body")
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(body, 100, 100).click().perform()
            print("Clicked on iframe page, waiting for requests...")
            time.sleep(20)  # Fixed wait to allow network requests to complete
            for req in driver.requests:
                if req.response and ".m3u8" in req.url:
                    print(f"Found stream URL: {req.url}")
                    found_streams.add(req.url)
            if not found_streams:
                print("No streams found in Selenium requests.")
        except Exception as e:
            print("Error while fetching streams:")
            traceback.print_exc()
        finally:
            if driver:
                driver.quit()
        return list(found_streams)

    streams = []
    attempts = 0
    while attempts < max_retries and not streams:
        try:
            print(f"Attempt {attempts + 1} to get streams...")
            iframe_url = fetch_iframe_url()
            if iframe_url:
                streams = fetch_streams(iframe_url)
            else:
                print("No iframe URL fetched.")
        except Exception as e:
            print("Error in attempt:")
            traceback.print_exc()
            streams = []
        attempts += 1

    session.close()
    print(f"Final streams found: {streams}")
    return streams

@app.route('/get_streams', methods=['GET'])
def get_streams_api():
    video_url = request.args.get('video_url')
    if not video_url:
        return jsonify({"error": "video url query parameter is required"}), 400

    try:
        key = extract_key_from_url(video_url)
        # Check if entry exists in DB
        doc = collection.find_one({"key": key})
        if doc and 'streams' in doc and doc['streams']:
            print(f"Found existing streams in DB for key {key}")
            streams = doc['streams']
        else:
            streams = get_stream_urls_from_tmdb(video_url)
            if streams:
                store_streams_in_db(video_url, streams)
        return jsonify({"video_url": video_url, "streams": streams})
    except Exception as e:
        print("Error in API call:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=False, host="0.0.0.0")
