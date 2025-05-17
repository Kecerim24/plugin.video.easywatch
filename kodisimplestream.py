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

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

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
    search_url = get_url(action='search_csfd_movie')
    search_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30012))  # "Search CSFD Movies"
    search_item.setArt({'icon': 'DefaultAddonsSearch.png'})
    xbmcplugin.addDirectoryItem(_handle, search_url, search_item, isFolder=True)
    
    # Add CSFD series search button
    search_url = get_url(action='search_csfd_series')
    search_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30013))  # "Search CSFD Series"
    search_item.setArt({'icon': 'DefaultAddonsSearch.png'})
    xbmcplugin.addDirectoryItem(_handle, search_url, search_item, isFolder=True)
    
    xbmcplugin.endOfDirectory(_handle)

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

def handle_csfd_selection(csfd_id, search_type):
    """
    Handle selection of a CSFD result and perform appropriate Webshare search.
    
    :param csfd_id: CSFD ID of selected item
    :type csfd_id: str
    :param search_type: Type of search ('movie' or 'series')
    :type search_type: str
    """
    csfd = CSFD()
    details = csfd.get_detail(csfd_id)
    
    if search_type == 'movie':
        search_terms = []
        # For movies, search Webshare with title and year
        search_terms.append(f"{details['title']} {details['year']}")
        if details['original_title'] and details['original_title'] != details['title']:
            search_terms.append(details['original_title'])
        list_search_results(search_terms)
    else:
        # For series, show seasons
        seasons = csfd.get_seasons(csfd_id)
        list_seasons(seasons, details['title'], details['original_title'], csfd_id)

def list_seasons(seasons, series_title, original_title, csfd_id):
    """
    Display list of seasons for a series.
    
    :param seasons: List of seasons
    :type seasons: list
    :param series_title: Title of the series
    :type series_title: str
    :param csfd_id: CSFD ID of the series
    :type csfd_id: str
    """
    listing = Listing()
    
    for season in seasons:
        season_obj = Season(
            number=season['number'],
            title=season['title'],
            year=season['year']
        )
        listing.add_item(season_obj)
    
    listing.list(get_url, _handle)

def list_episodes(csfd_id, season_id, series_title, original_title):
    """
    Display list of episodes for a season.
    
    :param csfd_id: CSFD ID of the series
    :type csfd_id: str
    :param season_id: Season ID
    :type season_id: str
    :param series_title: Title of the series
    :type series_title: str
    :param original_title: Original title of the series
    :type original_title: str
    """
    csfd = CSFD()
    episodes = csfd.get_episodes(csfd_id, season_id)
    
    listing = Listing()
    
    for episode in episodes:
        episode_obj = Episode(
            title=episode['title'],
            number=episode['number'],
            season=episode['season']
        )
        listing.add_item(episode_obj)
    
    listing.list(get_url, _handle)

def search_csfd_movie():
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
            
            listing = Listing()
            for result in results:
                movie = Movie(
                    title=result['title'],
                    year=result['year'],
                    plot=result['plot'],
                    rating=result['rating'],
                    poster=result['poster'],
                    fanart=result['poster']
                )
                listing.add_item(movie)
            
            listing.list(get_url, _handle)

def search_csfd_series():
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
            
            listing = Listing()
            for result in results:
                series = Series(
                    title=result['title'],
                    year=result['year'],
                    plot=result['plot'],
                    rating=result['rating'],
                    poster=result['poster'],
                    fanart=result['poster']
                )
                listing.add_item(series)
            
            listing.list(get_url, _handle)

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
        elif params['action'] == 'search_csfd_movie':
            search_csfd_movie()
        elif params['action'] == 'search_csfd_series':
            search_csfd_series()
        elif params['action'] == 'select_csfd':
            handle_csfd_selection(params['csfd_id'], params['search_type'])
        elif params['action'] == 'list_episodes':
            list_episodes(params['csfd_id'], params['season_id'], params['series_title'], params['original_title'])
        elif params['action'] == 'list_search_results':
            list_search_results(params['query'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_categories()

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])