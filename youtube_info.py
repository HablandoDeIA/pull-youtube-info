"""Fetches upload data from a YouTube channel."""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
import argparse

API_URL_CHANNELS = "https://www.googleapis.com/youtube/v3/channels"
API_URL_PLAYLIST_ITEMS = "https://www.googleapis.com/youtube/v3/playlistItems"


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


def get_channel_uploads_playlist(api_key: str, channel_username: str) -> str:
    params = {
        "part": "contentDetails",
        "forUsername": channel_username,
        "key": api_key,
    }
    response = requests.get(API_URL_CHANNELS, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()
    return payload["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_videos_from_playlist(api_key: str, playlist_id: str) -> List[Dict[str, str]]:
    videos: List[Dict[str, str]] = []
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": api_key,
    }

    while True:
        response = requests.get(API_URL_PLAYLIST_ITEMS, params=params, timeout=10)
        response.raise_for_status()
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


def main() -> None:
    args = parse_args()
    config = load_configuration(channel_override=args.channel)
    playlist_id = get_channel_uploads_playlist(
        config["api_key"], config["channel_username"]
    )
    videos = get_videos_from_playlist(config["api_key"], playlist_id)
    print(json.dumps(videos, indent=2))


if __name__ == "__main__":
    main()
