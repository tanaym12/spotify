from spot import get_playlist_tracks, get_track_dataframe, artist_with_most_tracks
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)

@app.route('/playlist', methods=['GET'])
@app.route('/playlist', methods=['GET'])
def get_playlist_info():
    playlist_id = request.args.get('playlist_id', default='6UeSakyzhiEt4NB3UAd6NQ')  # Default is Hot 100
    tracks = get_playlist_tracks(playlist_id)
    df = get_track_dataframe(tracks)

    artist, count = artist_with_most_tracks(tracks)
    
    # Return the same stats as before
    data = {
        "track_count": len(df),
        "most_popular_track": df['track_name'].iloc[df['popularity'].idxmax()],
        "most_popular_artist": artist.name,
        "most_tracks_artist": artist.name,
        "track_popularity_range": (df['popularity'].min(), df['popularity'].max()),
        "tracks": [{"track_name": t.name} for t in tracks]  # List of track names for the scrollable list
    }
    print(data)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)