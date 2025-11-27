"""Fetches upload data from a YouTube channel."""
from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

API_URL_CHANNELS = "https://www.googleapis.com/youtube/v3/channels"
API_URL_PLAYLIST_ITEMS = "https://www.googleapis.com/youtube/v3/playlistItems"
API_URL_SEARCH = "https://www.googleapis.com/youtube/v3/search"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch upload metadata for a YouTube channel."
    )
    parser.add_argument(
        "--channel",
        help="Channel username or ID to inspect (overrides CHANNEL_USERNAME env var).",
    )
    return parser.parse_args()


def load_configuration(channel_override: Optional[str] = None) -> Dict[str, str]:
    """Load API key and channel username from the environment."""
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    channel_username = channel_override or os.getenv("CHANNEL_USERNAME")

    if not api_key:
        raise RuntimeError("Missing YOUTUBE_API_KEY in environment")
    if not channel_username:
        raise RuntimeError(
            "Missing CHANNEL_USERNAME in environment or --channel was not provided"
        )

    return {"api_key": api_key, "channel_username": channel_username}


def _raise_api_error(response: requests.Response, context: str) -> None:
    try:
        detail = response.json().get("error", {}).get("message", "")
    except ValueError:
        detail = response.text
    message = f"{context} failed with status {response.status_code}"
    if detail:
        message = f"{message}: {detail}"
    raise RuntimeError(message)


def get_channel_id_by_search(api_key: str, channel_name: str) -> str:
    """Search for a channel by name and return its ID."""
    params = {
        "part": "snippet",
        "q": channel_name,
        "type": "channel",
        "maxResults": 5,
        "key": api_key,
    }
    response = requests.get(API_URL_SEARCH, params=params, timeout=10)
    if not response.ok:
        _raise_api_error(response, "Searching for channel")
    payload = response.json()

    items = payload.get("items", [])
    if not items:
        raise RuntimeError(f"No channels found matching '{channel_name}'")

    # Return the first matching channel ID
    return items[0]["snippet"]["channelId"]


def get_channel_uploads_playlist(api_key: str, channel_identifier: str) -> Tuple[str, str]:
    # If it's clearly a channel ID, use it directly
    if channel_identifier.startswith(("UC", "HC")):
        channel_id = channel_identifier
    else:
        # Use search API to find channel by name/handle
        channel_id = get_channel_id_by_search(api_key, channel_identifier)

    # Now get the channel details using the channel ID
    params = {
        "part": "contentDetails",
        "id": channel_id,
        "key": api_key,
    }

    response = requests.get(API_URL_CHANNELS, params=params, timeout=10)
    if not response.ok:
        _raise_api_error(response, "Fetching channel details")
    payload = response.json()

    items = payload.get("items")
    if not items:
        raise RuntimeError(f"Channel with ID '{channel_id}' not found.")

    upload_playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    channel_id = items[0]["id"]
    return upload_playlist, channel_id


def get_videos_from_playlist(
    api_key: str, playlist_id: str, channel_id: str
) -> List[Dict[str, str]]:
    videos: List[Dict[str, str]] = []
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": api_key,
    }

    while True:
        response = requests.get(API_URL_PLAYLIST_ITEMS, params=params, timeout=10)
        if not response.ok:
            if response.status_code == 404:
                # Some channels disable public access to their uploads playlist. Fallback to search.
                return get_videos_from_search(api_key, channel_id)
            _raise_api_error(response, "Fetching playlist items")
        payload = response.json()

        for item in payload.get("items", []):
            snippet = item["snippet"]
            videos.append(
                {
                    "title": snippet["title"],
                    "description": snippet.get("description", ""),
                    "link": f"https://www.youtube.com/watch?v={snippet['resourceId']['videoId']}",
                    "publishedAt": snippet["publishedAt"],
                }
            )

        next_page_token = payload.get("nextPageToken")
        if not next_page_token:
            break
        params["pageToken"] = next_page_token

    return videos


def get_videos_from_search(api_key: str, channel_id: str) -> List[Dict[str, str]]:
    """Fallback to channel search when the uploads playlist is unavailable."""
    videos: List[Dict[str, str]] = []
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": 50,
        "order": "date",
        "type": "video",
        "key": api_key,
    }

    while True:
        response = requests.get(API_URL_SEARCH, params=params, timeout=10)
        if not response.ok:
            _raise_api_error(response, "Searching for channel videos")
        payload = response.json()

        for item in payload.get("items", []):
            snippet = item["snippet"]
            videos.append(
                {
                    "title": snippet["title"],
                    "description": snippet.get("description", ""),
                    "link": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "publishedAt": snippet["publishedAt"],
                }
            )

        next_page_token = payload.get("nextPageToken")
        if not next_page_token:
            break
        params["pageToken"] = next_page_token

    return videos


def main() -> None:
    args = parse_args()
    config = load_configuration(channel_override=args.channel)
    playlist_id, channel_id = get_channel_uploads_playlist(
        config["api_key"], config["channel_username"]
    )
    videos = get_videos_from_playlist(config["api_key"], playlist_id, channel_id)
    print(json.dumps(videos, indent=2))


if __name__ == "__main__":
    main()
