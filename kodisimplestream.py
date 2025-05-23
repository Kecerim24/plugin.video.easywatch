# -*- coding: utf-8 -*-
# Module: kodisimplestream
# Author: Kecerim24
# Created on: 28.04.2025
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib.parse import urlencode
from urllib.parse import parse_qsl

import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc

from resources.lib.webshare import WebshareAPI
from resources.lib.csfd import CSFD
from resources.lib.utils import Movie, Series, Season, Episode, Listing

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_api = None

# Core/Utility Functions
def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

# API and Authentication
def get_api():
    """
    Get or initialize the WebshareAPI instance with stored credentials.
    Returns None if login fails.
    """
    global _api
    
    if _api is not None:
        return _api
        
    # Get credentials from addon settings
    username = _addon.getSetting('username')
    password = _addon.getSetting('password')
    
    if username and password:
        try:
            _api = WebshareAPI()
            _api.login(username, password)
            return _api
        except AssertionError as e:
            xbmcgui.Dialog().notification(
                _addon.getAddonInfo('name'),
                _addon.getLocalizedString(30009),
                xbmcgui.NOTIFICATION_ERROR,
                5000
            )
    else:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo('name'),
            _addon.getLocalizedString(30006).format(str(e)),
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )
    return None

# Listing/Display Functions
def list_categories():
    """
    Create the list of categories in the Kodi interface.
    """
    # Add direct Webshare search button
    search_url = get_url(action='search_webshare')
    search_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30011))  # "Search Webshare"
    search_item.setArt({'icon': 'DefaultAddonsSearch.png'})
    xbmcplugin.addDirectoryItem(_handle, search_url, search_item, isFolder=True)
    
    # Add CSFD movie search button
    search_url = get_url(action='search_movie_csfd')
    search_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30012))  # "Search CSFD Movies"
    search_item.setArt({'icon': 'DefaultAddonsSearch.png'})
    xbmcplugin.addDirectoryItem(_handle, search_url, search_item, isFolder=True)
    
    # Add CSFD series search button
    search_url = get_url(action='search_series_csfd')
    search_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30013))  # "Search CSFD Series"
    search_item.setArt({'icon': 'DefaultAddonsSearch.png'})
    xbmcplugin.addDirectoryItem(_handle, search_url, search_item, isFolder=True)
    
    xbmcplugin.endOfDirectory(_handle)

# Search Functions
def search_webshare():
    """
    Create a search dialog for direct Webshare search.
    """
    keyboard = xbmc.Keyboard('', _addon.getLocalizedString(30001))
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        search_term = keyboard.getText()
        if search_term:
            xbmcgui.Dialog().notification(
                _addon.getAddonInfo('name'),
                _addon.getLocalizedString(30002).format(search_term),
                xbmcgui.NOTIFICATION_INFO,
                2000
            )
            list_search_results([search_term])

def list_search_results(search_terms: list[str]):
    """
    Display search results from WebshareAPI.
    
    :param search_term: The term to search for
    :type search_term: str
    """
    api = get_api()
    if not api:
        return
        
    try:
        for search_term in search_terms:
            results = api.search(search_term)
            
            if results.is_empty():
                xbmcgui.Dialog().notification(
                    _addon.getAddonInfo('name'),
                    _addon.getLocalizedString(30007).format(_addon.getLocalizedString(30008)),
                    xbmcgui.NOTIFICATION_ERROR,
                    5000
                )
                continue
            
            results.list_videos(get_url, _handle, api)
            
    except Exception as e:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo('name'),
            _addon.getLocalizedString(30007).format(str(e)),
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )

def search_movie_csfd():
    """
    Create a search dialog for CSFD movie search.
    """
    keyboard = xbmc.Keyboard('', _addon.getLocalizedString(30014))  # "Search CSFD Movies"
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        search_term = keyboard.getText()
        if search_term:
            xbmcgui.Dialog().notification(
                _addon.getAddonInfo('name'),
                _addon.getLocalizedString(30002).format(search_term),
                xbmcgui.NOTIFICATION_INFO,
                2000
            )
            csfd = CSFD()
            results = csfd.search(search_term, type="movie")
            
            list_movies(results)

def search_movie_webshare(query, query_original):
    """
    Create a search dialog for Webshare movie search.
    """
    search_terms = []
    search_terms.append(query)
    if query_original and query_original != query:
        search_terms.append(query_original)
    list_search_results(search_terms)
    

def search_series_csfd():
    """
    Create a search dialog for CSFD series search.
    """
    keyboard = xbmc.Keyboard('', _addon.getLocalizedString(30015))  # "Search CSFD Series"
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        search_term = keyboard.getText()
        if search_term:
            xbmcgui.Dialog().notification(
                _addon.getAddonInfo('name'),
                _addon.getLocalizedString(30002).format(search_term),
                xbmcgui.NOTIFICATION_INFO,
                2000
            )
            csfd = CSFD()
            results = csfd.search(search_term, type="series")
            
            list_series(results)

def list_movies(items):
    """
    Display list of movies from CSFD search results.
    
    :param items: Movie items from CSFD search
    :type items: list
    """
    listing = Listing(items)
    listing.list(get_url, _handle)

def list_series(items):
    """
    Display list of series from CSFD search results.
    
    :param items: Series items from CSFD search
    :type items: list
    """
    listing = Listing(items)
    listing.list(get_url, _handle)

def list_seasons(series_id):
    """
    Display list of seasons for a series.
    
    :param series_id: Series ID
    :type series_id: str
    """
    csfd = CSFD()
    seasons = csfd.get_seasons(series_id)

    listing = Listing(seasons)
    listing.list(get_url, _handle)

def list_episodes(series_id, season_id):
    """
    Display list of episodes for a season.
    
    :param season_id: Season ID
    :type season_id: str
    """
    csfd = CSFD()
    episodes = csfd.get_episodes(series_id, season_id)
    
    listing = Listing(episodes)
    listing.list(get_url, _handle)


def search_episode_webshare(query, query_original):
    """
    Search for an episode on Webshare using both query and query_original.
    
    :param query: Search query in local language (e.g. "Show Name S01E02")
    :type query: str
    :param query_original: Search query in original language (e.g. "Original Show Name S01E02") 
    :type query_original: str
    """
    search_terms = []
    search_terms.append(query)
    if query_original and query_original != query:
        search_terms.append(query_original)
    list_search_results(search_terms)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

# Router and Main Entry Point
def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    params = dict(parse_qsl(paramstring))
    
    if params:
        if params['action'] == 'play':
            play_video(params['video'])
        elif params['action'] == 'search_webshare':
            search_webshare()
        elif params['action'] == 'search_movie_csfd':
            search_movie_csfd()
        elif params['action'] == 'search_series_csfd':
            search_series_csfd()   
        elif params['action'] == 'search_movie_webshare':
            search_movie_webshare(params['query'], params['query_original'])         
        elif params['action'] == 'list_seasons':
            list_seasons(params['series_id'])
        elif params['action'] == 'list_episodes':
            list_episodes(params['series_id'], params['season_id'])
        elif params['action'] == 'search_episode':
            search_episode_webshare(params['query'], params['query_original'])
        
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_categories()

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])