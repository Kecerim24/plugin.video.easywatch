# -*- coding: utf-8 -*-
# Module: kodisimplestream
# Author: Kecerim24
# Created on: 28.04.2025
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import annotations  # Enables forward references in older Python versions

# Kodi plugin boilerplate and plugin-specific modules
import ast
import sys
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.webshare import WebshareAPI
from resources.lib.csfd import CSFD
from resources.lib.fedapi import FedAPI
# ----------------------------------------------------------------------------
# Global variables – provided by Kodi during plugin initialization
# ----------------------------------------------------------------------------
_url: str = sys.argv[0]
_handle: int = int(sys.argv[1])
_addon: xbmcaddon.Addon = xbmcaddon.Addon()
_api: Optional[WebshareAPI] = None

# ----------------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------------

def get_url(**kwargs: Any) -> str:
    """Returns a plugin URL with encoded parameters for recursive calls."""
    return f"{_url}?{urlencode(kwargs)}"

def get_api() -> Optional[WebshareAPI]:
    """
    Returns an authenticated instance of WebshareAPI.
    Shows error notification on failure.
    """
    global _api

    if _api is not None:
        return _api

    username: str = _addon.getSetting("username")
    password: str = _addon.getSetting("password")

    if not (username and password):
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo("name"),
            _addon.getLocalizedString(30006),  # "Please enter username and password…"
            xbmcgui.NOTIFICATION_ERROR,
            5000,
        )
        return None

    try:
        _api = WebshareAPI()
        _api.login(username, password)
        if not getattr(_api, "_token", ""):
            raise RuntimeError("Webshare returned an empty token – check credentials.")
        return _api
    except Exception as exc:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo("name"),
            _addon.getLocalizedString(30009).format(str(exc)),  # "Login failed…"
            xbmcgui.NOTIFICATION_ERROR,
            5000,
        )
        return None

# ----------------------------------------------------------------------------
# Root menu
# ----------------------------------------------------------------------------

def list_categories() -> None:
    """Creates items for the plugin's main menu."""
    for action, label_id in (
        ("search_webshare", 30011),
        ("search_csfd_movie", 30012),
        ("search_csfd_series", 30013),
        ("search_imdb_fedapi", 30016),
    ):
        item = xbmcgui.ListItem(label=_addon.getLocalizedString(label_id))
        item.setArt({"icon": "DefaultAddonsSearch.png"})
        xbmcplugin.addDirectoryItem(_handle, get_url(action=action), item, isFolder=True)

    xbmcplugin.endOfDirectory(_handle)

# ----------------------------------------------------------------------------
# Playback
# ----------------------------------------------------------------------------

def play_video(path: str) -> None:
    """Passes the video URL to Kodi’s internal player."""
    xbmcplugin.setResolvedUrl(_handle, True, xbmcgui.ListItem(path=path))

# ----------------------------------------------------------------------------
# Webshare: search & listing
# ----------------------------------------------------------------------------

def list_search_results(search_terms: List[str]) -> None:
    """
    Displays search results for a list of search terms using WebshareAPI.
    Adds each result as a playable item.
    """
    api = get_api()
    if not api:
        return

    try:
        for term in search_terms:
            response = api.search(term)["response"]
            if int(response.get("total", 0)) == 0:
                xbmcgui.Dialog().notification(
                    _addon.getAddonInfo("name"),
                    _addon.getLocalizedString(30007).format(_addon.getLocalizedString(30008)),
                    xbmcgui.NOTIFICATION_ERROR,
                    5000,
                )
                continue

            for file_info in response["file"]:
                item = xbmcgui.ListItem(label=file_info["name"])
                item.setInfo("video", {
                    "title": file_info.get("name", term),
                    "size": int(file_info.get("size", 0)),
                })
                item.setArt({"poster": file_info.get("img", ""), "fanart": file_info.get("img", "")})

                video_url = api.get_download_link(file_info["ident"])
                if not video_url:
                    continue

                item.setProperty("IsPlayable", "true")
                xbmcplugin.addDirectoryItem(_handle, get_url(action="play", video=video_url), item, isFolder=False)

        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setContent(_handle, "videos")
        xbmcplugin.endOfDirectory(_handle)
    except Exception as exc:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo("name"),
            _addon.getLocalizedString(30007).format(str(exc)),
            xbmcgui.NOTIFICATION_ERROR,
            5000,
        )

# ----------------------------------------------------------------------------
# Generic input dialog for searching
# ----------------------------------------------------------------------------

def _keyboard_search(label_id: int) -> Optional[str]:
    """Displays Kodi’s virtual keyboard and returns input text if confirmed."""
    keyboard = xbmc.Keyboard("", _addon.getLocalizedString(label_id))
    keyboard.doModal()
    return keyboard.getText() if keyboard.isConfirmed() else None

# ----------------------------------------------------------------------------
# Webshare – search dialog entry point
# ----------------------------------------------------------------------------

def search_webshare() -> None:
    """Handles interactive Webshare search via on-screen keyboard."""
    term = _keyboard_search(30001)
    if term:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo("name"),
            _addon.getLocalizedString(30002).format(term),
            xbmcgui.NOTIFICATION_INFO,
            2000,
        )
        list_search_results([term])

# ----------------------------------------------------------------------------
# CSFD – search results
# ----------------------------------------------------------------------------

def list_csfd_results(results: List[Dict[str, Any]], search_type: str) -> None:
    """Displays CSFD search results as Kodi menu items."""
    for result in results:
        title = result["title"]
        year = result.get("year")
        label = f"{title} ({year})" if year else title

        item = xbmcgui.ListItem(label=label)
        item.setInfo("video", {
            "title": title,
            "year": year,
            "plot": result.get("plot"),
            "rating": result.get("rating"),
        })
        item.setArt({"poster": result.get("poster", ""), "fanart": result.get("poster", "")})

        url = get_url(action="select_csfd", csfd_id=result["id"], search_type=search_type)
        xbmcplugin.addDirectoryItem(_handle, url, item, isFolder=True)

    xbmcplugin.endOfDirectory(_handle)

# ----------------------------------------------------------------------------
# CSFD – selection and detailed episode listing
# ----------------------------------------------------------------------------

def handle_csfd_selection(csfd_id: str, search_type: str) -> None:
    """Handles selection from CSFD and delegates search or episode listing."""
    csfd = CSFD()
    details = csfd.get_detail(csfd_id)

    if search_type == "movie":
        queries: List[str] = [f"{details['title']} {details['year']}"]
        if details.get("original_title") and details["original_title"] != details["title"]:
            queries.append(details["original_title"])
        list_search_results(queries)
        return

    # Series → show list of seasons
    seasons = csfd.get_seasons(csfd_id)
    list_seasons(seasons, details["title"], details.get("original_title"), csfd_id)

# ----------------------------------------------------------------------------
# CSFD – episode navigation
# ----------------------------------------------------------------------------

def list_seasons(
    seasons: List[Dict[str, Any]],
    series_title: str,
    original_title: Optional[str],
    csfd_id: str,
) -> None:
    """Displays list of seasons for a series."""
    for season in seasons:
        label = season["title"] if season["title"] != "Season" else f"Season {season['number']}"
        url = get_url(
            action="list_episodes",
            csfd_id=csfd_id,
            season_id=season["id"],
            series_title=series_title,
            original_title=original_title or "",
        )
        xbmcplugin.addDirectoryItem(_handle, url, xbmcgui.ListItem(label=label), isFolder=True)

    xbmcplugin.endOfDirectory(_handle)

def list_episodes(
    csfd_id: str,
    season_id: str,
    series_title: str,
    original_title: str,
) -> None:
    """Displays episode list for a given season."""
    csfd = CSFD()
    episodes = csfd.get_episodes(csfd_id, season_id)

    for ep in episodes:
        season_no = ep.get("season") or 0
        ep_no = ep.get("number") or 0
        label = f"{ep_no}. {ep['title']}"

        queries: List[str] = [f"{series_title} S{season_no:02d}E{ep_no:02d}"]
        if original_title and original_title != series_title:
            queries.append(f"{original_title} S{season_no:02d}E{ep_no:02d}")

        url = get_url(action="list_search_results", query=str(queries))
        xbmcplugin.addDirectoryItem(_handle, url, xbmcgui.ListItem(label=label), isFolder=True)

    xbmcplugin.endOfDirectory(_handle)

# ----------------------------------------------------------------------------
# CSFD – search entry points
# ----------------------------------------------------------------------------

def search_csfd_movie() -> None:
    """Search dialog for CSFD movie titles."""
    term = _keyboard_search(30014)
    if term:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo("name"),
            _addon.getLocalizedString(30002).format(term),
            xbmcgui.NOTIFICATION_INFO,
            2000,
        )
        results = CSFD().search(term, type="movie")
        list_csfd_results(results, "movie")

def search_csfd_series() -> None:
    """Search dialog for CSFD TV series titles."""
    term = _keyboard_search(30015)
    if term:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo("name"),
            _addon.getLocalizedString(30002).format(term),
            xbmcgui.NOTIFICATION_INFO,
            2000,
        )
        results = CSFD().search(term, type="series")
        list_csfd_results(results, "series")
        
# ----------------------------------------------------------------------------
# IMDB – search entry point
# ----------------------------------------------------------------------------

def search_imdb_fedapi() -> None:
    """Search dialog for IMDB titles."""
    term = _keyboard_search(30017)
    if term:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo("name"),
            _addon.getLocalizedString(30002).format(term),
            xbmcgui.NOTIFICATION_INFO,
            2000,
        )
        results = FedAPI().search_imdb(term)
        list_imdb_results(results)
        
# ----------------------------------------------------------------------------
# IMDB – results listing and navigation
# ----------------------------------------------------------------------------

def list_imdb_results(results: List[Tuple[str, str, str, str]]) -> None:
    """Displays IMDB search results as Kodi menu items."""
    for result in results:
        imdb_id, title, year, type_ = result
        label = f"{title} ({year}) | {type_}" if year else f"{title} | {type_}"
        
        item = xbmcgui.ListItem(label=label)
        item.setInfo("video", {
            "title": title,
            "year": year,
        })
        
        # Store the type in the item's properties
        item.setProperty("type", type_)
                
        url = get_url(action="select_imdb", imdb_id=imdb_id, type=type_)
        xbmcplugin.addDirectoryItem(_handle, url, item, isFolder=True)
        
    xbmcplugin.endOfDirectory(_handle)

def handle_imdb_selection(imdb_id: str, type_: str) -> None:
    """Handles selection of an IMDB result and shows appropriate stream options."""
    try:
        fedapi = FedAPI()
        
        if type_ == "movie":
            streams = fedapi.get_movie_streams(imdb_id)
            show_stream_selection(streams)
        else:  # TV series
            # Show season/episode selection dialog
            season = xbmcgui.Dialog().numeric(0, _addon.getLocalizedString(30018), "1")  # "Enter season number"
            if not season:
                return
                
            episode = xbmcgui.Dialog().numeric(0, _addon.getLocalizedString(30019), "1")  # "Enter episode number"
            if not episode:
                return
                
            streams = fedapi.get_series_streams(imdb_id, int(season), int(episode))
            show_stream_selection(streams)
            
    except Exception as exc:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo("name"),
            str(exc),
            xbmcgui.NOTIFICATION_ERROR,
            5000,
        )

def show_stream_selection(streams: Dict[str, str]) -> None:
    """Shows a dialog with available stream options."""
    if not streams:
        xbmcgui.Dialog().notification(
            _addon.getAddonInfo("name"),
            _addon.getLocalizedString(30020),  # "No streams available"
            xbmcgui.NOTIFICATION_ERROR,
            5000,
        )
        return
        
    # Create list of stream options
    options = []
    for quality, url in streams.items():
        options.append(quality)
        
    # Show selection dialog
    selected = xbmcgui.Dialog().select(_addon.getLocalizedString(30021), options)  # "Select stream quality"
    if selected >= 0:
        quality = options[selected]
        url = streams[quality]
        xbmc.log(f"Selected stream: {quality} | {url}", xbmc.LOGINFO)
        play_video(url)

# ----------------------------------------------------------------------------
# Placeholder for unimplemented features
# ----------------------------------------------------------------------------

def list_videos(category: str) -> None:
    """Stub for future content browsing by category."""
    xbmcgui.Dialog().notification(
        _addon.getAddonInfo("name"),
        _addon.getLocalizedString(30016),  # "This function is not implemented yet."
        xbmcgui.NOTIFICATION_INFO,
        3000,
    )

# ----------------------------------------------------------------------------
# Routing
# ----------------------------------------------------------------------------

def router(paramstring: str) -> None:
    """Dispatches actions based on plugin paramstring."""
    params = dict(parse_qsl(paramstring))
    action = params.get("action")

    if action is None:
        list_categories()
        return

    if action == "listing":
        list_videos(params["category"])
    elif action == "play":
        play_video(params["video"])
    elif action == "search_webshare":
        search_webshare()
    elif action == "search_csfd_movie":
        search_csfd_movie()
    elif action == "search_csfd_series":
        search_csfd_series()
    elif action == "select_csfd":
        handle_csfd_selection(params["csfd_id"], params["search_type"])
    elif action == "list_episodes":
        list_episodes(
            params["csfd_id"],
            params["season_id"],
            params["series_title"],
            params.get("original_title", ""),
        )
    elif action == "list_search_results":
        raw_query = params["query"]
        try:
            query_list = ast.literal_eval(raw_query)
            if not isinstance(query_list, list):
                query_list = [raw_query]
        except (ValueError, SyntaxError):
            query_list = [raw_query]
        list_search_results([str(q) for q in query_list])
    elif action == "search_imdb_fedapi":
        search_imdb_fedapi()
    elif action == "select_imdb":
        handle_imdb_selection(params["imdb_id"], params["type"])
    else:
        raise ValueError(f"Invalid paramstring: {paramstring}!")

# ----------------------------------------------------------------------------
if __name__ == "__main__":
    # Kodi passes plugin parameters in `sys.argv[2]`, including the leading '?'
    # This may be missing during CLI testing – handle gracefully.
    router(sys.argv[2][1:] if len(sys.argv) > 2 and sys.argv[2].startswith("?") else "")