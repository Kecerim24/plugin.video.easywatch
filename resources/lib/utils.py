import xbmcgui
import xbmcplugin
from typing import Union, List

class Video:
    def __init__(self, title: str, path: str = '', poster: str = '', fanart: str = '', size: int = 0, webshare_id: str = ''):
        self.title = title
        self.path = path
        self.poster = poster
        self.fanart = fanart
        self.size = size
        self.webshare_id = webshare_id

    def get_path(self, webshare_api) -> str:
        if self.path:
            return self.path
        elif self.webshare_id:
            self.path = webshare_api.get_download_link(self.webshare_id)
            return self.path
        else:
            raise ValueError("Path or Webshare ID is not set")

class VideoList:
    def __init__(self):
        self.videos = []

    def is_empty(self) -> bool:
        return len(self.videos) == 0

    def add_video(self, video: Video):
        self.videos.append(video)
    
    def list_videos(self, get_url, handle, webshare_api) -> None:
        """
        :param get_url: function to get the URL for the video
        :param handle: handle of the plugin
        :param webshare_api: webshare API
        """
        for video in self.videos:
            list_item = xbmcgui.ListItem(video.title)
            
            list_item.setInfo('video', {
                'title': video.title,
                'size': video.size
            })
                        
            list_item.setArt({
                'poster': video.poster,
                'fanart': video.fanart
            })
            
            # Set the video URL
            url = get_url(action='play', video=video.get_path(webshare_api))
            if not url:
                continue
        
            list_item.setProperty('IsPlayable', 'true')    

            xbmcplugin.addDirectoryItem(handle, url, list_item, isFolder=False)

        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setContent(handle, 'videos')
        xbmcplugin.endOfDirectory(handle)

class Movie:
    def __init__(self, csfd_id: str, title: str, original_title: str = '', year: str = '', plot: str = '', rating: str = '', poster: str = '', fanart: str = ''):
        self.csfd_id = csfd_id
        self.title = title
        self.original_title = original_title
        self.year = year
        self.plot = plot
        self.rating = rating
        self.poster = poster
        self.fanart = fanart

class Series:
    def __init__(self, csfd_id: str, title: str, original_title: str = '', year: str = '', plot: str = '', rating: str = '', poster: str = '', fanart: str = ''):
        self.csfd_id = csfd_id
        self.title = title
        self.original_title = original_title
        self.year = year
        self.plot = plot
        self.rating = rating
        self.poster = poster
        self.fanart = fanart

class Season:
    def __init__(self, csfd_id: str, series_id: str, number: str, title: str = 'Season', year: str = '', plot: str = '', rating: str = '', poster: str = '', fanart: str = ''):
        self.csfd_id = csfd_id
        self.series_id = series_id
        self.title = title
        self.number = number
        self.year = year
        self.plot = plot
        self.rating = rating
        self.poster = poster
        self.fanart = fanart

class Episode:
    def __init__(self, csfd_id: str, series_title: str, title: str, series_original_title: str = '', original_title: str = '', number: str = '', season_number: str = '', year: str = '', plot: str = '', rating: str = '', poster: str = '', fanart: str = ''):
        self.csfd_id = csfd_id
        self.series_title = series_title
        self.series_original_title = series_original_title
        self.title = title
        self.original_title = original_title
        self.number = number
        self.season_number = season_number
        self.year = year
        self.plot = plot
        self.rating = rating
        self.poster = poster
        self.fanart = fanart


class Listing:
    def __init__(self, items: List[Union[Movie, Series, Season, Episode]]):
        self.items = items

    def list(self, get_url, handle) -> None:
        for item in self.items:
            # Create a list item with the video title

            if isinstance(item, Movie) or isinstance(item, Series):
                list_item = xbmcgui.ListItem(label=f"{item.title} ({item.year})")
            elif isinstance(item, Season):
                list_item = xbmcgui.ListItem(label=f"{item.title} {item.number}")
            elif isinstance(item, Episode):
                list_item = xbmcgui.ListItem(label=f"{item.number}. {item.title}")
                
            # Set additional info for the list item
            list_item.setInfo('video', {
                'title': item.title,
                'year': item.year,
                'plot': item.plot,
                'rating': item.rating
            })
            
            # Set art
            list_item.setArt({
                'poster': item.poster,
                'fanart': item.fanart
            })
            
            # Create URL with appropriate action based on item type
            if isinstance(item, Movie):
                url = get_url(action='search_movie_webshare', query=f"{item.title} {item.year}", query_original=f"{item.original_title} {item.year}")
            elif isinstance(item, Series):
                url = get_url(action='list_seasons', series_id=item.csfd_id)
            elif isinstance(item, Season):
                url = get_url(action='list_episodes', series_id=item.series_id, season_id=item.csfd_id)
            elif isinstance(item, Episode):
                url = get_url(action='search_episode_webshare', query=f"{item.series_title} S{item.season_number}E{item.number}", query_original=f"{item.series_original_title} S{item.season_number}E{item.number}")
            
            # Add the item to the directory
            xbmcplugin.addDirectoryItem(handle, url, list_item, isFolder=True)
        
        xbmcplugin.endOfDirectory(handle)

    def add_item(self, item: Union[Movie, Series, Season, Episode]) -> None:
        self.items.append(item)

    def add_items(self, items: List[Union[Movie, Series, Season, Episode]]) -> None:
        self.items.extend(items)