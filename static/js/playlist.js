class PlaylistManager {
  constructor() {
    this.tracks = [];
    this.currentTrack = null;
    this.stats = { total_tracks: 0, total_duration: 0 };

    // Callbacks
    this.onPlaylistUpdated = null;
    this.onTrackChange = null;
  }

  async fetchPlaylist() {
    try {
      const response = await fetch("/api/playlist");
      const data = await response.json();

      if (data.success) {
        this.tracks = data.tracks;
        this.stats = data.stats;

        // If there's a cached current track
        if (data.current_track) {
          this.currentTrack = data.current_track;
          if (this.onTrackChange) this.onTrackChange(this.currentTrack);
        }

        if (this.onPlaylistUpdated)
          this.onPlaylistUpdated(this.tracks, this.stats);
        return true;
      }
    } catch (error) {
      console.error("Error fetching playlist:", error);
      return false;
    }
  }

  async addUrl(url) {
    try {
      const response = await fetch("/api/playlist/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();
      if (data.success) {
        await this.fetchPlaylist();
        return { success: true, message: data.message };
      } else {
        return { success: false, error: data.error };
      }
    } catch (error) {
      console.error("Error adding URL:", error);
      return { success: false, error: "Network error" };
    }
  }

  async removeTrack(trackId) {
    try {
      const response = await fetch(`/api/playlist/remove/${trackId}`, {
        method: "DELETE",
      });

      const data = await response.json();
      if (data.success) {
        await this.fetchPlaylist();
        return true;
      }
    } catch (error) {
      console.error("Error removing track:", error);
    }
    return false;
  }

  async nextTrack() {
    try {
      const response = await fetch("/api/playlist/next", { method: "POST" });
      const data = await response.json();

      if (data.success && data.track) {
        this.currentTrack = data.track;
        if (this.onTrackChange) this.onTrackChange(data.track);
        await this.fetchPlaylist(); // Update active state UI
        return data.track;
      }
    } catch (error) {
      console.error("Error next track:", error);
    }
    return null;
  }

  async previousTrack() {
    try {
      const response = await fetch("/api/playlist/previous", {
        method: "POST",
      });
      const data = await response.json();

      if (data.success && data.track) {
        this.currentTrack = data.track;
        if (this.onTrackChange) this.onTrackChange(data.track);
        await this.fetchPlaylist();
        return data.track;
      }
    } catch (error) {
      console.error("Error prev track:", error);
    }
    return null;
  }

  async shuffle() {
    try {
      const response = await fetch("/api/playlist/shuffle", { method: "POST" });
      const data = await response.json();
      if (data.success) {
        await this.fetchPlaylist();
        return true;
      }
    } catch (error) {
      console.error("Error shuffling:", error);
    }
    return false;
  }

  async clear() {
    try {
      const response = await fetch("/api/playlist/clear", { method: "DELETE" });
      const data = await response.json();
      if (data.success) {
        this.tracks = [];
        this.currentTrack = null;
        await this.fetchPlaylist();
        return true;
      }
    } catch (error) {
      console.error("Error clearing playlist:", error);
    }
    return false;
  }

  async setTrack(trackId) {
    try {
      const response = await fetch("/api/playlist/current", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ track_id: trackId }),
      });

      const data = await response.json();
      if (data.success) {
        this.currentTrack = data.track;
        if (this.onTrackChange) this.onTrackChange(data.track);
        await this.fetchPlaylist(); // Update active highlights
        return data.track;
      }
    } catch (error) {
      console.error("Error setting track:", error);
    }
    return null;
  }
}
