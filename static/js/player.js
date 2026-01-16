class AudioPlayer {
  constructor() {
    this.audio = new Audio();
    this.currentTrackId = null;
    this.isPlaying = false;

    // Event Connectors
    this.onTimeUpdate = null;
    this.onTrackEnded = null;
    this.onPlayStateChange = null;
    this.onError = null;

    this._initListeners();
  }

  _initListeners() {
    this.audio.addEventListener("timeupdate", () => {
      if (this.onTimeUpdate) {
        this.onTimeUpdate(this.audio.currentTime, this.audio.duration);
      }
    });

    this.audio.addEventListener("ended", () => {
      if (this.onTrackEnded) {
        this.onTrackEnded();
      }
    });

    this.audio.addEventListener("error", (e) => {
      console.error("Audio Error:", e);
      if (this.onError) {
        this.onError("Error reproducing audio");
      }
    });

    this.audio.addEventListener("play", () => {
      this.isPlaying = true;
      if (this.onPlayStateChange) this.onPlayStateChange(true);
    });

    this.audio.addEventListener("pause", () => {
      this.isPlaying = false;
      if (this.onPlayStateChange) this.onPlayStateChange(false);
    });
  }

  async loadTrack(track) {
    if (!track || !track.id) return;

    this.currentTrackId = track.id;
    // Use the API stream endpoint
    this.audio.src = `/api/audio/stream/${track.id}`;
    this.audio.load();

    try {
      await this.play();
    } catch (e) {
      console.warn("Auto-play blocked or failed:", e);
    }
  }

  async play() {
    try {
      await this.audio.play();
    } catch (error) {
      console.error("Play failed:", error);
      throw error;
    }
  }

  pause() {
    this.audio.pause();
  }

  togglePlay() {
    if (this.audio.paused) {
      this.play();
    } else {
      this.pause();
    }
  }

  seek(time) {
    if (isFinite(time)) {
      this.audio.currentTime = time;
    }
  }

  setVolume(value) {
    // value between 0 and 1
    this.audio.volume = Math.max(0, Math.min(1, value));
  }

  getDuration() {
    return this.audio.duration;
  }

  getCurrentTime() {
    return this.audio.currentTime;
  }
}
