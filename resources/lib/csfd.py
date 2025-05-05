import requests
import random
import json
import re
from typing import Literal, Dict, List
from bs4 import BeautifulSoup

class CSFD:
    """
    Scraper for csfd.cz
    """
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Mobile Safari/537.36'
    ]
    def __init__(self):
        self.base_url = "https://www.csfd.cz/"
        
    def get_detail(self, full_id):
        url = f"{self.base_url}/film/{full_id}/prehled"
        headers = {
            "User-Agent":random.choice(self.USER_AGENTS)
        }
        response = requests.get(url, headers=headers)
        if 600 > response.status_code >= 400:
            raise Exception(f"Failed to get detail for {full_id}\nStatus code: {response.status_code}\nResponse: {response.text}")
        
        soup = BeautifulSoup(response.text.encode('utf-8'), "html.parser")
        
        # Extract poster URL
        poster_elem = soup.find('img', {'class': 'prev-img'})
        poster = None
        if poster_elem and 'src' in poster_elem.attrs:
            poster = poster_elem['src']
            if poster.startswith('//'):
                poster = 'https:' + poster

        # Extract plot
        plot = None
        plot_elem = soup.find('div', {'class': 'plot-full'})
        if plot_elem:
            plot = plot_elem.get_text().strip().split('\n')[0]
        
        # Extract title
        title = None
        title_elem = soup.find('h1')
        if title_elem:
            title = title_elem.text.strip()

        # Extract year
        year = None
        origin_elem = soup.find('div', {'class': 'origin'})
        if origin_elem:
            year_match = re.search(r'(\d{4})', origin_elem.text)
            if year_match:
                year = year_match.group(1)

        # Extract rating
        rating = None
        rating_elem = soup.find('div', {'class': 'film-rating-average'})
        if rating_elem:
            rating = rating_elem.text.strip()

        # Extract genres
        genres = []
        genres_elem = soup.find('div', {'class': 'genres'})
        if genres_elem:
            genre_links = genres_elem.find_all('a')
            genres = [g.text.strip() for g in genre_links]

        return {
            'title': title,
            'year': year,
            'rating': rating,
            'genres': genres,
            'plot': plot,
            'poster': poster
        }

    def search(self, query, type: Literal["movie", "series"] = "movie") -> List[Dict]:
        url = f"{self.base_url}/hledat/?q={query}"
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS)
        }
        response = requests.get(url, headers=headers)
        if 600 > response.status_code >= 400:
            raise Exception(f"Failed to search for {query}\nStatus code: {response.status_code}\nResponse: {response.text}")
        
        soup = BeautifulSoup(response.text.encode('utf-8'), "html.parser")
        
        results = []
        articles = soup.find_all('article', class_='article-poster-50')
        
        for article in articles:
            # Check if it's a series or movie
            is_series = 'seriál' in article.text or 'epizoda' in article.text
            
            # Skip if type doesn't match
            if (type == "movie" and is_series) or (type == "series" and not is_series):
                continue

            # Skip if it contains (série) or (epizoda) in film-title-info
            title_info = article.find('span', class_='film-title-info')
            if title_info and ('(série)' in title_info.text or '(epizoda)' in title_info.text):
                continue
                
            # Extract ID from href
            title_elem = article.find('a', class_='film-title-name')
            if not title_elem:
                continue
                
            href = title_elem.get('href', '')
            full_id = href.split('/')[-2] if href else None
            
            if full_id:
                try:
                    # Get full details for each result
                    details = self.get_detail(full_id)
                    details['id'] = full_id
                    details['type'] = type
                    results.append(details)
                except Exception as e:
                    print(f"Failed to get details for {full_id}: {str(e)}")
                    continue
        
        return results
    
    def get_seasons(self, full_id):
        url = f"{self.base_url}/film/{full_id}/prehled"
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS)
        }
        # TODO: Implement

    def get_episodes(self, full_id, season_id):
        url = f"{self.base_url}/film/{full_id}/{season_id}/prehled"
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS)
        }
        # TODO: Implement

if __name__ == "__main__":
    csfd = CSFD()
    print(json.dumps(csfd.search("akta x", type="movie"), indent=2, ensure_ascii=False))
