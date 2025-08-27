# 🎬 Stream URL Scraper API

A **Flask-based API** that scrapes streaming URLs (e.g. `.m3u8` links) for movies and TV shows from multiple **vidsrc domains**.  
It supports **MongoDB Atlas caching**, so once a stream is found, it won’t need to be scraped again.

---

## 🚀 Features
- Scrape playable `.m3u8` links from `vidsrc` domains.
- Supports **movies** and **TV shows**:
  - Movies → `movie_<tmdb>`  
  - TV Shows → `tv_<tmdb>_<season>_<episode>`
- Stores results in **MongoDB Atlas** for fast reuse.
- Randomized domain selection for reliability.
- Retry logic with up to 2 attempts.
- Proxy support via [ScrapeOps](https://scrapeops.io/).
- Uses **Selenium Wire** to capture network requests.

---

## 🛠️ Tech Stack
- **Backend**: [Flask](https://flask.palletsprojects.com/)  
- **Scraping**: [Requests](https://requests.readthedocs.io/), [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/), [Selenium Wire](https://github.com/wkeeling/selenium-wire)  
- **Database**: [MongoDB Atlas](https://www.mongodb.com/atlas)  
- **Proxy**: [ScrapeOps Proxy API](https://scrapeops.io/)  

---

## 📂 Project Structure
stream-scraper/
│── app.py # Main Flask app
│── requirements.txt # Python dependencies
│── .env.example # Example environment file
│── .gitignore # Ignored files
│── README.md # Documentation

---

## ⚙️ Setup & Installation

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/Movies-Stream-URL-Scrapper.git
cd Movies-Stream-URL-Scrapper
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
Create a .env file in the project root
MONGO_URL=YOUR MONGO URI
PROXY_API= Your ProxyScape API Key
```

### 4. Run the server
```bash
python app.py
```

---

Server will start on: http://0.0.0.0:5000

## 🔥 API Usage

### Endpoint /get_streams

### Method GET

### Query Parameters
| Name       | Type   | Required | Description                          |
|------------|--------|----------|--------------------------------------|
| video_url  | string | ✅        | The `vidsrc` video embed URL (movie or TV show) |

---

### Example Request
```bash
curl "http://localhost:5000/get_streams?video_url=https://vidsrc.to/embed/movie?tmdb=12345"
```
### Example Response
{
  "video_url": "https://vidsrc.to/embed/movie?tmdb=12345",
  "streams": [
    "https://stream-cdn123.example.com/hls/movie12345/index.m3u8",
    "https://backup-stream.example.net/hls/movie12345/index.m3u8"
  ]
}

✔️ If the streams are already cached in MongoDB, they are returned instantly.
✔️ If not, the scraper fetches fresh ones, stores them in MongoDB, and then returns them.

