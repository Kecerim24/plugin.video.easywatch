import requests
import hashlib
import xmltodict
from xml.etree import ElementTree
import json

from md5crypt import md5crypt
from utils import *

class WebshareAPI:
    """
    Webshare API class
    https://webshare.cz/apidoc/
    """
    
    def __init__(self):
        self._base_url = "https://webshare.cz/api/"
        self._headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        self._token = ""

    def login(self, user_name, password):
        """Logs {user_name} in Webshare API"""
        salt = self.get_salt(user_name)
        url = self._base_url + 'login/'
        password = self.hash_password(password, salt)
        data = {
                'username_or_email' : user_name,
                'password' : password,
                'keep_logged_in' : 1
                }
        response = requests.post(url, data=data, headers=self._headers)
        assert(response.status_code == 200)
        root = ElementTree.fromstring(response.content)
        assert root.find('status').text == 'OK', 'Return code was not OK, debug info: status: {}, code: {}, message: {}'.format(
                    root.find('status').text,
                    root.find('code').text,
                    root.find('message').text)
        self._token = root.find('token').text

    def hash_password(self, password, salt):
        """Creates password hash used by Webshare API"""
        return hashlib.sha1(md5crypt(password, salt).encode('utf-8')).hexdigest()

    def get_salt(self, user_name):
        """Retrieves salt for password hash from webshare.cz"""
        url = self._base_url + 'salt/'
        data = {'username_or_email' : user_name}
        response = requests.post(url, data=data, headers=self._headers)
        assert(response.status_code == 200)
        root = ElementTree.fromstring(response.content)
        assert root.find('status').text == 'OK', 'Return code was not OK, debug info: status: {}, code: {}, message: {}'.format(
                    root.find('status').text, 
                    root.find('code').text, 
                    root.find('message').text)
        return root.find('salt').text

    def get_download_link(self, file_id) -> str:
        """Query actual download link from {file_id}, returning empty string if no link is found"""
        url = self._base_url + 'file_link/'
        data = {'ident' : file_id, 'wst' : self._token}
        response = requests.post(url, data=data, headers=self._headers)
        root = ElementTree.fromstring(response.content)
        return root.find('link').text if root.find('link') is not None else ''
    
    def search(self, query: str, limit: int = 7, offset: int = 0, sort: str = 'largest', category: str = 'video') -> VideoList:
        """Search for videos on webshare.cz
        query: str - search query
        limit: int - number of results to return
        offset: int - number of results to skip
        sort: str - sort order (recent, rating, largest, smallest)
        category: str - category (video, images, audio, docs, archives)
        """
        url = self._base_url + 'search/'
        data = {'what' : query.encode('utf-8') ,'sort' : sort, 'limit' : limit, 'offset' : offset, 'category' : category}
        response = requests.post(url, data=data, headers=self._headers)
        
        if response.status_code != 200:
            raise Exception(f"Search request failed with status code: {response.status_code}")
            
        try:
            json_response = xmltodict.parse(response.content)
            if not json_response or 'response' not in json_response:
                raise Exception("Invalid response format from server")
        except Exception as e:
            raise Exception(f"Failed to parse search response: {str(e)}")
        
        video_list = VideoList()
        
        for file in json_response['response']['file']:
            video = Video(file['name'], '', file['img'],file['img'], file['size'], file['ident'])
            video_list.add_video(video)
        return video_list
         
if __name__ == "__main__":
    # For testing purposes
    webshare = WebshareAPI()
    webshare.login("test", "test")
    webshare.search("Cars", 5)