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
    # Add search button
    search_url = get_url(action='search')
    search_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30001))
    search_item.setArt({'icon': 'DefaultAddonsSearch.png'})
    xbmcplugin.addDirectoryItem(_handle, search_url, search_item, isFolder=True)
    
    xbmcplugin.endOfDirectory(_handle)


def list_videos(category):
   pass

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


def list_search_results(search_term):
    """
    Display search results from WebshareAPI.
    
    :param search_term: The term to search for
    :type search_term: str
    """
    api = get_api()
    if not api:
        return
        
    try:
        results: dict = api.search(search_term)['response']
        
        if results['total'] == 0:
            xbmcgui.Dialog().notification(
                _addon.getAddonInfo('name'),
                _addon.getLocalizedString(30007).format(_addon.getLocalizedString(30008)),
                xbmcgui.NOTIFICATION_ERROR,
                5000
            )
            return
        # Add each result to the directory
        for result in results['file']:
            # Create a list item with the video title
            list_item = xbmcgui.ListItem(label=result['name'])
            
            # Set additional info for the list item using InfoTagVideo
            list_item.setInfo('video', {
                'title': result.get('name', search_term),
                'size': result.get('size', 0)
            })
                        
            # Set art (poster, fanart, etc.)
            list_item.setArt({
                'poster': result.get('img', ''),
                'fanart': result.get('img', '')
            })
            
            # Set the video URL
            url = get_url(action='play', video=api.get_download_link(result['ident']))
            if not url:
                continue
            
            # Set the item as playable
            list_item.setProperty('IsPlayable', 'true')
            
            # Add the item to the directory
            xbmcplugin.addDirectoryItem(_handle, url, list_item, isFolder=False)
        
        # Add a sort method for the virtual folder items
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
        
        # Set content type to videos
        xbmcplugin.setContent(_handle, 'videos')
        
        # Finish creating a virtual folder
        xbmcplugin.endOfDirectory(_handle)
    except Exception as e:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo('name'),
            _addon.getLocalizedString(30007).format(str(e)),
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )

def search():
    """
    Create a search dialog and handle the search request.
    """
    # Create a keyboard dialog
    keyboard = xbmc.Keyboard('', _addon.getLocalizedString(30001))
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        search_term = keyboard.getText()
        if search_term:
            # Show searching notification
            xbmcgui.Dialog().notification(
                _addon.getAddonInfo('name'),
                _addon.getLocalizedString(30002).format(search_term),
                xbmcgui.NOTIFICATION_INFO,
                2000
            )
            # Display search results
            list_search_results(search_term)

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        elif params['action'] == 'search':
            # Handle search request
            search()
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])