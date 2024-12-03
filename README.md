# Coomer.su Scraper

A Python web scraper for downloading videos from Coomer.su.

## Features

- Scrapes popular posts from Coomer.su
- Extracts video links from posts
- Downloads videos with user confirmation
- Saves post data to JSON file
- Anti-detection measures implemented

## Requirements

- Python 3.7+
- Chrome/Chromium browser
- Required Python packages in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd [repo-name]
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:
```bash
python scraper.py
```

The script will:
1. Scrape popular posts from Coomer.su
2. Extract video links from each post
3. Show you the list of available videos
4. Ask for confirmation before downloading
5. Download videos to the `downloads` directory

## Note

This is for educational purposes only. Please respect website terms of service and robot policies.
