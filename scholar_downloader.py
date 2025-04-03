from scholarly import scholarly, ProxyGenerator
import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import arxiv
import re
from urllib.parse import urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_proxy():
    """Set up a proxy to avoid Google Scholar blocking"""
    try:
        pg = ProxyGenerator()
        success = pg.FreeProxies()
        scholarly.use_proxy(pg)
        logger.info("Successfully set up proxy")
    except Exception as e:
        logger.warning(f"Failed to set up proxy: {str(e)}")
        logger.info("Continuing without proxy...")

def extract_doi_from_url(url):
    """Extract DOI from URL if present"""
    doi_pattern = r'10\.\d{4,9}/[-._;()/:\w]+'
    match = re.search(doi_pattern, url)
    return match.group(0) if match else None

def try_download_paper(paper):
    """Attempt to download the full paper using various methods"""
    try:
        # Try to get the paper's URL
        url = paper.get('pub_url', '')
        if not url:
            return None

        # Try to get the paper's PDF URL
        paper_filled = scholarly.fill(paper)
        pdf_url = paper_filled.get('eprint_url', '')
        
        if pdf_url:
            # Try to download PDF
            response = requests.get(pdf_url, stream=True)
            if response.status_code == 200:
                return response.content
                
        # If no direct PDF URL, try to find it in the page
        if url:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for PDF links
                pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
                if pdf_links:
                    pdf_url = pdf_links[0]['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = urlparse(url).scheme + '://' + urlparse(url).netloc + pdf_url
                    response = requests.get(pdf_url, stream=True)
                    if response.status_code == 200:
                        return response.content

        return None
    except Exception as e:
        logger.error(f"Error downloading paper: {str(e)}")
        return None

def search_and_save_papers(search_query, num_papers=10):
    """
    Search Google Scholar and save paper information
    """
    # Create directories for the papers
    papers_dir = "addiction_texts"
    pdfs_dir = os.path.join(papers_dir, "pdfs")
    for directory in [papers_dir, pdfs_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    try:
        # Search for papers
        search_query = scholarly.search_pubs(search_query)
        
        # Process papers
        for i in range(num_papers):
            try:
                paper = next(search_query)
                paper_filled = scholarly.fill(paper)
                
                # Create a filename from the title
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', paper.get('bib', {}).get('title', 'No title'))
                base_filename = f"paper_{i+1}_{datetime.now().strftime('%Y%m%d')}"
                
                # Save metadata
                metadata_file = os.path.join(papers_dir, f"{base_filename}_metadata.txt")
                content = f"""Title: {paper.get('bib', {}).get('title', 'No title')}
Authors: {', '.join(paper.get('bib', {}).get('author', ['Unknown']))}
Year: {paper.get('bib', {}).get('pub_year', 'Unknown')}
Abstract: {paper.get('bib', {}).get('abstract', 'No abstract available')}
URL: {paper.get('pub_url', 'No URL available')}
Citations: {paper.get('num_citations', 0)}
DOI: {paper_filled.get('doi', 'No DOI available')}
"""
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Try to download the full paper
                pdf_content = try_download_paper(paper)
                if pdf_content:
                    pdf_file = os.path.join(pdfs_dir, f"{base_filename}.pdf")
                    with open(pdf_file, 'wb') as f:
                        f.write(pdf_content)
                    logger.info(f"Successfully downloaded PDF for paper {i+1}")
                
                print(f"Saved paper {i+1}: {paper.get('bib', {}).get('title', 'No title')}")
                
                # Sleep to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing paper {i+1}: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Error in search_and_save_papers: {str(e)}")

def main():
    try:
        # Set up proxy
        setup_proxy()
        
        # Define search queries
        search_queries = [
            "addiction treatment methods",
            "substance abuse recovery",
            "addiction neuroscience",
            "addiction therapy approaches"
        ]
        
        # Process each search query
        for query in search_queries:
            print(f"\nSearching for: {query}")
            search_and_save_papers(query, num_papers=5)
            time.sleep(5)  # Wait between queries
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main() 