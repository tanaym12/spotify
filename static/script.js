document.getElementById('load-playlist').addEventListener('click', () => {
    const playlistId = document.getElementById('playlist-id').value.trim();
    const url = `http://127.0.0.1:5000/playlist?playlist_id=${playlistId}`;
    console.log(url)
  
    // Fetch playlist data from the backend
    fetch(url)
      .then(response => response.json())
      .then(data => {
        // Update stats
        document.getElementById('track-count').innerText = data.track_count;
        document.getElementById('most-popular-track').innerText = data.most_popular_track;
        document.getElementById('most-popular-artist').innerText = data.most_popular_artist;
        document.getElementById('most-tracks-artist').innerText = data.most_tracks_artist;
        document.getElementById('popularity-range').innerText = `${data.track_popularity_range[0]} - ${data.track_popularity_range[1]}`;
  
        // Populate the track list
        const trackListContainer = document.getElementById('track-list-container');
        trackListContainer.innerHTML = '';
        data.tracks.forEach(track => {
          const li = document.createElement('li');
          li.innerText = track.track_name;
          trackListContainer.appendChild(li);
        });
      })
      .catch(error => console.error('Error fetching playlist data:', error));
  });
  