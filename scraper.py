import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

# Function to get the content of a webpage
def get_page_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to find all links on a webpage
def find_links(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    links = set()
    for anchor in soup.find_all('a', href=True):
        link = urljoin(base_url, anchor['href'])
        # Only keep links within the same domain
        if urlparse(link).netloc == urlparse(base_url).netloc:
            links.add(link)
    return links

# Function to save page content to a file
def save_page_content(url, content, output_dir):
    # Create a valid filename by replacing non-alphanumeric characters
    filename = urlparse(url).path.replace('/', '_').strip('_') + '.html'
    if not filename:
        filename = 'index.html'
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)

# Recursive function to scrape links
def scrape_links(url, base_url, visited, output_dir, depth, max_depth):
    if url in visited or depth > max_depth:
        return

    print(f"Scraping {url} at depth {depth}")
    page_content = get_page_content(url)
    if page_content is None:
        return

    save_page_content(url, page_content, output_dir)
    visited.add(url)

    links = find_links(page_content, base_url)
    for link in links:
        scrape_links(link, base_url, visited, output_dir, depth + 1, max_depth)

# Function to scrape an entire website
def scrape_website(start_url, output_dir, max_depth=2):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    visited = set()
    scrape_links(start_url, start_url, visited, output_dir, 0, max_depth)
    
    return visited

if __name__ == "__main__":
    start_url = 'PUT WEb SITE URL HERE'  # Replace with the starting URL
    output_dir = 'scraped_pages'  # Directory to save scraped content
    max_depth = 3  # Set the maximum depth to scrape
    scraped_urls = scrape_website(start_url, output_dir, max_depth)
    print(f"Scraped {len(scraped_urls)} pages")
    for url in scraped_urls:
        print(url)
