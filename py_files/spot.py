import os
import pandas as pd
from typing import List, Tuple
import matplotlib.pyplot as plt
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from models import *

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Initialize Spotipy with OAuth. Adjust redirect_uri as needed.
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri="http://localhost:8888/callback",
    scope="playlist-read-private"
))

def get_playlist_tracks(playlist_id: str = "6UeSakyzhiEt4NB3UAd6NQ") -> List[Track]:
    """
    Fetches a Spotify playlist by its ID and returns a list of Track objects.
    For each track, it retrieves basic details (ID, name, popularity, duration) 
    and associated artist information (including genres).
    """
    playlist_data = sp.playlist(playlist_id)
    items = playlist_data['tracks']['items']
    
    # Gather artist IDs from all tracks
    artist_ids_set = set()
    for item in items:
        track_obj = item.get('track')
        if track_obj:
            for artist in track_obj['artists']:
                artist_ids_set.add(artist['id'])
    artist_ids = list(artist_ids_set)
    
    # Fetch artist details in batches (max 50 per request)
    artists_dict = {}
    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i+50]
        response = sp.artists(batch)
        for a in response['artists']:
            artists_dict[a['id']] = Artist(
                id=a['id'],
                name=a['name'],
                genres=a['genres']
            )
    
    # Build Track objects using available track metadata
    track_list = []
    for item in items:
        track_obj = item.get('track')
        if not track_obj:
            continue
        track_artists = []
        for art in track_obj['artists']:
            artist_obj = artists_dict.get(art['id'])
            if artist_obj:
                track_artists.append(artist_obj)
        track = Track(
            id=track_obj['id'],
            name=track_obj['name'],
            artists=track_artists,
            popularity=track_obj.get('popularity', 0),
            duration_ms=track_obj.get('duration_ms', 0)
        )
        track_list.append(track)
    
    return track_list

def get_hot_100_tracks() -> List[Track]:
    """
    Fetches the Billboard Hot 100 playlist.
    (Replace the playlist ID if needed.)
    """
    hot_100_playlist_id = "6UeSakyzhiEt4NB3UAd6NQ"
    return get_playlist_tracks(hot_100_playlist_id)

def get_genres(track: Track) -> List[str]:
    """
    Returns a list of unique genres for all artists on the track.
    """
    genres = []
    for artist in track.artists:
        genres.extend(artist.genres)
    return list(set(genres))

def does_genre_contain(track: Track, keyword: str) -> bool:
    """
    Checks (case-insensitively) if any of the track's genres contain the keyword.
    """
    keyword = keyword.lower()
    return any(keyword in genre.lower() for genre in get_genres(track))

def get_track_dataframe(tracks: List[Track]) -> pd.DataFrame:
    """
    Constructs a Pandas DataFrame from a list of tracks.
    The DataFrame includes:
      - track_id, track_name, artist_ids, artist_names, genres
      - popularity, duration_ms, and boolean flags for specific genres.
    """
    records = []
    for t in tracks:
        record = {
            "track_id": t.id,
            "track_name": t.name,
            "artist_ids": [artist.id for artist in t.artists],
            "artist_names": [artist.name for artist in t.artists],
            "genres": get_genres(t),
            "popularity": t.popularity,
            "duration_ms": t.duration_ms,
            "is_pop": does_genre_contain(t, "pop"),
            "is_rap": does_genre_contain(t, "rap"),
            "is_dance": does_genre_contain(t, "dance"),
            "is_country": does_genre_contain(t, "country")
        }
        records.append(record)
    return pd.DataFrame.from_records(records)

def visualize_data(tracks: List[Track]):
    """
    Example visualization: Scatter plot of track popularity vs. duration (in minutes).
    """
    df = get_track_dataframe(tracks)
    # Convert duration from milliseconds to minutes
    df['duration_min'] = df['duration_ms'] / 60000.0
    plt.figure(figsize=(10, 6))
    plt.scatter(df['duration_min'], df['popularity'], alpha=0.7, color='blue')
    plt.xlabel("Duration (minutes)")
    plt.ylabel("Popularity")
    plt.title("Track Popularity vs Duration")
    plt.grid(True)
    plt.show()

def artist_with_most_tracks(tracks: List[Track]) -> Tuple[Artist, int]:
    """
    Determines which artist appears on the most tracks in the playlist.
    """
    artist_count = {}
    for track in tracks:
        for artist in track.artists:
            artist_count[artist.id] = artist_count.get(artist.id, 0) + 1
    max_artist_id = max(artist_count, key=artist_count.get)
    max_count = artist_count[max_artist_id]
    for track in tracks:
        for artist in track.artists:
            if artist.id == max_artist_id:
                return artist, max_count
    return None, 0

def main():
    tracks = get_hot_100_tracks()
    df = get_track_dataframe(tracks)
    print("Sample DataFrame:")
    print(df.head())
    artist, count = artist_with_most_tracks(tracks)
    print(f"{artist.name} appears on {count} tracks in the Hot 100 playlist.")
    visualize_data(tracks)

if __name__ == "__main__":
    main()