import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up a file handler for failed downloads
failed_download_file = 'faileddownload.txt'
file_handler = logging.FileHandler(failed_download_file)
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(file_handler)

def get_page_content(url, retries=3, delay=1):
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(delay)
    logger.error(f"Failed to fetch {url} after {retries} attempts")
    return None

def find_links(page_content, base_url, exclusions):
    soup = BeautifulSoup(page_content, 'html.parser')
    links = set()
    for anchor in soup.find_all('a', href=True):
        link = urljoin(base_url, anchor['href'])
        if urlparse(link).netloc == urlparse(base_url).netloc and not any(excl in link for excl in exclusions):
            links.add(link)
    return links

def make_filename(url):
    filename = urlparse(url).path.replace('/', '_').strip('_') + '.html'
    if not filename:
        filename = 'index.html'
    return filename

def save_page_content(url, content, output_dir):
    filename = make_filename(url)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)

def update_links(page_content, base_url, visited):
    soup = BeautifulSoup(page_content, 'html.parser')
    for anchor in soup.find_all('a', href=True):
        original_url = urljoin(base_url, anchor['href'])
        if original_url in visited:
            anchor['href'] = make_filename(original_url)
    return str(soup)

def scrape_links(url, base_url, visited, output_dir, depth, max_depth, exclusions):
    if url in visited or depth > max_depth:
        return

    logger.info(f"Scraping {url} at depth {depth}")
    page_content = get_page_content(url)
    if page_content is None:
        logger.error(f"Skipping {url} due to repeated failures")
        return

    updated_content = update_links(page_content, base_url, visited)
    save_page_content(url, updated_content, output_dir)
    visited.add(url)

    links = find_links(updated_content, base_url, exclusions)
    for link in links:
        scrape_links(link, base_url, visited, output_dir, depth + 1, max_depth, exclusions)

def scrape_website(start_urls, output_dir, max_depth=2, exclusions=None):
    if exclusions is None:
        exclusions = []

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    visited = set()
    for start_url in start_urls:
        scrape_links(start_url, start_url, visited, output_dir, 0, max_depth, exclusions)
    
    return visited

def load_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            start_urls = config.get('start_urls', [])
            exclusions = config.get('exclusions', [])
            max_depth = config.get('max_depth', 2)
            return start_urls, exclusions, max_depth
    except Exception as e:
        logger.error(f"Error loading configuration from {file_path}: {e}")
        return [], [], 2

if __name__ == "__main__":
    config_file = 'config.yaml'  # Replace with your config file path
    start_urls, exclusions, max_depth = load_config(config_file)
    output_dir = 'scraped_pages'  # Directory to save scraped content
    scraped_urls = scrape_website(start_urls, output_dir, max_depth, exclusions)
    logger.info(f"Scraped {len(scraped_urls)} pages")
    for url in scraped_urls:
        logger.info(url)
