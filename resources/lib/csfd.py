import requests
import random
import json
import re
from typing import Literal, List
from bs4 import BeautifulSoup
from resources.lib.utils import Movie, Series, Season, Episode

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
        
    def get_detail(self, full_id) -> Movie | Series:
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

        # Extract original title if not Czech
        original_title = ''
        if origin_elem and 'Česko' not in origin_elem.text:
            film_names = soup.find('ul', {'class': 'film-names'})
            if film_names:
                first_name = film_names.find('li')
                if first_name:
                    original_title = first_name.text.strip()

        # Check if it's a series
        is_series = 'seriál' in soup.text or 'epizoda' in soup.text

        if is_series:
            return Series(
                title=title,
                original_title=original_title,
                year=year,
                plot=plot,
                rating=rating,
                poster=poster,
                fanart=poster
            )
        else:
            return Movie(
                title=title,
                original_title=original_title,
                year=year,
                plot=plot,
                rating=rating,
                poster=poster,
                fanart=poster
            )

    def search(self, query, type: Literal["movie", "series"] = "movie") -> List[Movie | Series]:
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
                    result = self.get_detail(full_id)
                    
                    # If it's a series, get seasons and episodes
                    if isinstance(result, Series):
                        seasons = self.get_seasons(full_id)
                        for season in seasons:
                            episodes = self.get_episodes(full_id, season.csfd_id)
                            season.episodes = episodes
                        result.seasons = seasons
                    
                    results.append(result)
                except Exception as e:
                    print(f"Failed to get details for {full_id}: {str(e)}")
                    continue
        
        return results
    
    def get_seasons(self, full_id) -> List[Season]:
        """
        Get list of seasons for a series.
        
        :param full_id: CSFD ID of the series
        :type full_id: str
        :return: List of seasons with their details
        :rtype: list[Season]
        """
        url = f"{self.base_url}/film/{full_id}/prehled"
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS)
        }
        response = requests.get(url, headers=headers)
        if 600 > response.status_code >= 400:
            raise Exception(f"Failed to get seasons for {full_id}\nStatus code: {response.status_code}\nResponse: {response.text}")
        
        soup = BeautifulSoup(response.text.encode('utf-8'), "html.parser")
        
        seasons = []
        episodes_list = soup.find('div', class_='film-episodes-list')
        
        if episodes_list:
            for season_elem in episodes_list.find_all('li'):
                # Get season title and link
                title_elem = season_elem.find('a', class_='film-title-name')
                if not title_elem:
                    continue
                    
                # Extract season number from title (e.g., "Season 1" -> 1)
                season_title = title_elem.text.strip()
                try:
                    season_number = int(season_title.split()[-1])
                except ValueError:
                    season_number = len(seasons) + 1
                
                # Get season ID from href
                href = title_elem.get('href', '')
                season_id = href.split('/')[-2] if href else None
                
                # Get year and episode count from info
                info_elem = season_elem.find('span', class_='film-title-info')
                year = None
                episode_count = None
                
                if info_elem:
                    # Extract year
                    year_match = re.search(r'\((\d{4})\)', info_elem.text)
                    if year_match:
                        year = year_match.group(1)
                    
                    # Extract episode count
                    episode_match = re.search(r'(\d+)\s+epizod', info_elem.text)
                    if episode_match:
                        episode_count = int(episode_match.group(1))
                
                seasons.append(Season(
                    csfd_id=season_id,
                    number=season_number,
                    title=season_title,
                    year=year
                ))
        
        # Sort seasons by number
        seasons.sort(key=lambda x: x.number)
        return seasons

    def get_episodes(self, full_id, season_id) -> List[Episode]:
        """
        Get list of episodes for a season.
        
        :param full_id: CSFD ID of the series
        :type full_id: str
        :param season_id: Season ID
        :type season_id: str
        :return: List of episodes with their details
        :rtype: list[Episode]
        """
        url = f"{self.base_url}/film/{full_id}/{season_id}/prehled"
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS)
        }
        response = requests.get(url, headers=headers)
        if 600 > response.status_code >= 400:
            raise Exception(f"Failed to get episodes for {full_id}/{season_id}\nStatus code: {response.status_code}\nResponse: {response.text}")
        
        soup = BeautifulSoup(response.text.encode('utf-8'), "html.parser")
        
        episodes = []
        episodes_list = soup.find('div', class_='film-episodes-list')
        
        if episodes_list:
            for episode_elem in episodes_list.find_all('li'):
                # Get episode title and link
                title_elem = episode_elem.find('a', class_='film-title-name')
                if not title_elem:
                    continue
                    
                episode_title = title_elem.text.strip()
                
                # Get episode ID from href
                href = title_elem.get('href', '')
                episode_id = href.split('/')[-2] if href else None
                
                # Get season and episode numbers from info
                info_elem = episode_elem.find('span', class_='film-title-info')
                season_number = None
                episode_number = None
                
                if info_elem:
                    # Extract season and episode numbers from format (S01E01)
                    episode_info = info_elem.find('span', class_='info')
                    if episode_info:
                        match = re.search(r'S(\d+)E(\d+)', episode_info.text)
                        if match:
                            season_number = int(match.group(1))
                            episode_number = int(match.group(2))
                
                episodes.append(Episode(
                    csfd_id=episode_id,
                    title=episode_title,
                    number=episode_number,
                    season_number=season_number
                ))
        
        # Sort episodes by number
        episodes.sort(key=lambda x: x.number)
        return episodes

if __name__ == "__main__":
    csfd = CSFD()
    print(json.dumps(csfd.search("akta x", type="movie"), indent=2, ensure_ascii=False))
