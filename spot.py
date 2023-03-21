import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import List, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import billboard
from collections import defaultdict, Counter
from models import *

"""
NOTE: When submitting to PrairieLearn, please ensure that the function call to main() at the bottom of the file is commented out,
as well as any other places you have called the getPlaylist() or getHot100() functions. A simple CTRL/CMD + F to search will 
suffice. PrairieLearn will fail to grade your submission if the main() function is still commented in OR if a call to 
getPlaylist() or getHot100() is sill present in your code.  
"""

"""
SETUP: Must do first!
"""
#spotipy wraps the official spotify api providing simple python functions.
CLIENT_ID = "94378bbb944b4ea5aac2757e9ce0b872"
CLIENT_SECRET = "0aa97fed045348bd94f17b24e93eb43b"

#https://developer.spotify.com/dashboard/applications to get client_id and client_secret
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET))
"""
PART 1: Getting the Top 100 Data!
You must complete Part 1 before moving on down below
"""
def getPlaylist(id: str) -> List[Track]:
    '''
    Given a playlist ID, returns a list of Track objects corresponding to the songs on the playlist. See
    models.py for the definition of dataclasses Track, Artist, and AudioFeatures.
    We need the audio features of each track to populate the audiofeatures list.
    We need the genre(s) of each artist in order to populate the artists in the artist list.

    We've written parts of this function, but it's up to you to complete it!
    '''

    # fetch tracks data from spotify given a playlist id
    playlistdata = sp.playlist(id)
    tracks = playlistdata['tracks']['items']
    track_ids_list = []
    for track in tracks:
        track_ids_list.append(track['track']['id'])

    # fetch audio features based on the data stored in the playlist result
    track_ids = track_ids_list
    audio_features = sp.audio_features(track_ids)
    audio_info = {}  # Audio features list might not be in the same order as the track list
    for af in audio_features:
        audio_info[af['id']] = AudioFeatures(af['danceability'], \
                                             af['energy'], \
                                             af['key'],  \
                                             af['loudness'],  \
                                             af['mode'],  \
                                             af['speechiness'], \
                                             af['acousticness'], \
                                             af['instrumentalness'], \
                                             af['liveness'], \
                                             af['valence'], \
                                             af['tempo'], \
                                             af['duration_ms'], \
                                             af['time_signature'], \
                                             af['id'])

    # prepare artist dictionary
    artist_ids_list_temp = []
    for artists in tracks:
        for artist in artists['track']['artists']:
            artist_ids_list_temp.append(artist['id'])

    artist_ids_list = list(set(artist_ids_list_temp))
    artist_ids = artist_ids_list

    artists = {}
    for k in range(1+len(artist_ids)//50): # can only request info on 50 artists at a time!
        artists_response = sp.artists(artist_ids[k*50:min((k+1)*50,len(artist_ids))]) #what is this doing?
        for a in artists_response['artists']:
            artists[a['id']] = Artist(a['id'], \
                                      a['name'], \
                                      a['genres'])

    #populate track dataclass
    trackList = [Track(id =  t['track']['id'],
                       name= t['track']['name'],
                       artists = [artists.get(id) for id in [d.get('id') for d in t['track']['artists']]],
                       audio_features= audio_info[t['track']['id']]) for t in tracks]

    return trackList

''' this function is just a way of naming the list we're using. You can write
additional functions like "top Canadian hits!" if you want.'''
def getHot100() -> List[Track]:
    # Billboard hot 100 Playlist ID URI
    hot_100_id = "6UeSakyzhiEt4NB3UAd6NQ"
    return getPlaylist(hot_100_id)

# ---------------------------------------------------------------------

"""
Part 2: The Helper Functions
Now that we have the billboard's top 100 tracks, let's design some helper functions that will make our lives easier when creating our dataframe.
"""

def getGenres(t: Track) -> List[str]:
    '''
    Takes in a Track and produce a list of unique genres that the artists of this track belong to
    '''
    lst_of_genres = []
    for artists in t.artists:
        lst_of_genres.extend(artists.genres)
    return list(set(lst_of_genres))

def doesGenreContains(t: Track, genre: str) -> bool:
    '''
    TODO
    Checks if the genres of a track contains the key string specified
    For example, if a Track's unique genres are ['pop', 'country pop', 'dance pop']
    doesGenreContains(t, 'dance') == True
    doesGenreContains(t, 'pop') == True
    doesGenreContains(t, 'hip hop') == False
    '''
    if genre in getGenres(t):
        return True
    else:
        return False

def getTrackDataFrame(tracks: List[Track]) -> pd.DataFrame:
    '''
    This function is given.
    Prepare dataframe for a list of tracks
    audio-features: 'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
                    'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo',
                    'duration_ms', 'time_signature', 'id',
    track & artist: 'track_name', 'artist_ids', 'artist_names', 'genres',
                    'is_pop', 'is_rap', 'is_dance', 'is_country'
    '''
    # populate records
    records = []
    for t in tracks:
        to_add = asdict(t.audio_features) #converts the audio_features object to a dict
        to_add["track_name"] = t.name
        to_add["artist_ids"] = list(map(lambda a: a.id, t.artists)) # we will discuss this in class
        to_add["artist_names"] = list(map(lambda a: a.name, t.artists))
        to_add["genres"] = getGenres(t)
        to_add["is_pop"] = doesGenreContains(t, "pop")
        to_add["is_rap"] = doesGenreContains(t, "rap")
        to_add["is_dance"] = doesGenreContains(t, "dance")
        to_add["is_country"] = doesGenreContains(t, "country")

        records.append(to_add)

    # create dataframe from records
    df = pd.DataFrame.from_records(records)
    return df

# ---------------------------------------------------------------------
# The most popular artist of the week

def artist_with_most_tracks(tracks: List[Track]) -> (Artist, int):
    '''
    List of tracks -> (artist, number of tracks the artist has)
    This function finds the artist with most number of tracks on the list
    If there is a tie, you may return any of the artists
    '''

    arts = {}
    for t in tracks:
        arts[t.name] = t.artists

    count_dict = {}

    for lst in arts.values():
        for artist in lst:
            artist_str = repr(artist)
            # Check if the element is already in the count dictionary
            if artist_str in count_dict:
                count_dict[artist_str] += 1
            else:
                count_dict[artist_str] = 1

    max_value = max(count_dict.values())
    max_artists = [artist for artist, value in count_dict.items() if value == max_value]
    print(max_artists)
    max_key = max_artists[0]
    max_key = eval(max_key)

    return max_key, max_value

"""
Part 3: Visualizing the Data
"""

# 3.1 scatter plot of dancability-speechiness with markers colored by genre: is_rap

def danceability_plot(tracks:List[Track]):
    df = getTrackDataFrame(tracks)

    rap_df = df[df['is_rap']==True]
    not_rap_df = df[df['is_rap']==False]

    danceability_values_rap = rap_df['danceability'].values
    speechiness_values_rap = rap_df['speechiness'].values
    danceability_values_not_rap = not_rap_df['danceability'].values
    speechiness_values_not_rap = not_rap_df['speechiness'].values

    plt.scatter(danceability_values_rap, speechiness_values_rap, alpha=0.7, label="Rap", c="red")
    plt.scatter(danceability_values_not_rap, speechiness_values_not_rap, alpha=0.7, label="Not Rap", c="blue")
    plt.xlabel('Danceability')
    plt.ylabel('Speechiness')
    plt.title('Danceability Plot')
    plt.legend()
    plt.show()

# 3.2 scatter plot (ask your own question).
# 3.1 scatter plot of energy-dancability with markers colored by genre: is_pop
def energy_plot(tracks:List[Track]):
    df = getTrackDataFrame(tracks)

    pop_df = df[df['is_pop']==True]
    not_pop_df = df[df['is_pop']==False]

    energy_values_pop = pop_df['energy'].values
    danceability_values_pop = pop_df['danceability'].values
    energy_values_not_pop = not_pop_df['energy'].values
    danceability_values_not_pop = not_pop_df['danceability'].values

    plt.scatter(energy_values_pop, danceability_values_pop, alpha=0.7, label="Pop", c="red")
    plt.scatter(energy_values_not_pop, danceability_values_not_pop, alpha=0.7, label="Not Pop", c="blue")
    plt.ylabel('Danceability')
    plt.xlabel('Energy')
    plt.title('Energy-Danceability Plot')
    plt.legend()
    plt.show()

def main():
    top100Tracks = getHot100()
    df = getTrackDataFrame(top100Tracks)
    print(df.head())
    artist, num_track = artist_with_most_tracks(top100Tracks)
    print("%s has the most number of tracks on this week's Hot 100 at a whopping %d tracks!" % (artist.name, num_track))
    danceability_plot(top100Tracks)
    energy_plot(top100Tracks)

#main()