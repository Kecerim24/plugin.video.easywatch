import requests
import random
import json
import xbmcaddon

from typing import Dict, List, Tuple, Optional

class FedAPI:
    """
    Alternative source
    
    To get your UI token:
    1. Go to [febbox.com](https://febbox.com) and log in with Google (use a fresh account!)
    2. Open DevTools or inspect the page
    3. Go to Application tab → Cookies
    4. Copy the 'ui' cookie.
    5. Close the tab, but do NOT logout!
    
    Video tutorial: https://vimeo.com/1059834885/c3ab398d42
    """
    def __init__(self):
        self.url = "https://fed-api-europe.pstream.org"
        self.USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Mobile Safari/537.36']
        
        addon = xbmcaddon.Addon()
        ui_token = addon.getSetting("ui_token")
        if not ui_token:
            raise Exception("UI token not set in addon settings")
            
        self.headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "ui-token": ui_token.strip(),
            "Origin": "https://pstream.org"
        }

    def get_movie_streams(self, imdb_id: str) -> Dict[str, str]:
        url = f"{self.url}/movie/{imdb_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get movie streams for {imdb_id}")
        streams = response.json().get("streams", "")
        if not streams:
            raise Exception(f"No streams found for {imdb_id}")
        return streams
    
    def get_series_streams(self, imdb_id: str, season: int, episode: int) -> Dict[str, str]:
        url = f"{self.url}/tv/{imdb_id}/{season}/{episode}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get series streams for {imdb_id} {season} {episode}")
        streams = response.json().get("streams", "")
        if not streams:
            raise Exception(f"No streams found for {imdb_id} {season} {episode}")
        return streams
    
    def search_imdb(self, query: str) -> List[Tuple[str, str, str, str]]:
        query = query.strip()
        url =  f"https://sg.media-imdb.com/suggests/{query[0]}/{query}.json" # This is cursed
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to search for {query}")
        
        response_list = json.loads(response.text[response.text.find('{'):-1])['d']
        
        if len(response_list) == 0:
            raise Exception(f"No results found for {query}")
        results = []
        
        for result in response_list:
            if result['id'].startswith("tt"):
                results.append((result['id'], result['l'], str(result['y']), result.get('qid', '')))
        return results
            
if __name__ == "__main__":
    fedapi = FedAPI()
    #print(fedapi.get_movie_streams("tt15239678").get("ORG"))
    #print(fedapi.get_series_streams("tt9253284", 2, 9).get("ORG"))
    print(fedapi.search_imdb("Star Wars: Epizode 2"))