document.addEventListener("DOMContentLoaded", () => {
  // Initialize Managers
  const player = new AudioPlayer();
  const playlistManager = new PlaylistManager();

  // DOM Elements
  const elements = {
    playBtn: document.getElementById("play-btn"),
    prevBtn: document.getElementById("prev-btn"),
    nextBtn: document.getElementById("next-btn"),
    shuffleBtn: document.getElementById("shuffle-btn"),
    progressBar: document.getElementById("progress-bar"),
    currentTime: document.getElementById("current-time"),
    totalTime: document.getElementById("total-time"),
    volumeSlider: document.getElementById("volume-slider"),
    playlistContainer: document.getElementById("playlist-items"),
    totalTracks: document.getElementById("total-tracks"),
    currentTitle: document.getElementById("current-title"),
    currentArtist: document.getElementById("current-artist"),
    addBtn: document.getElementById("add-url-btn"),
    modalOverlay: document.getElementById("add-modal"),
    closeModalBtn: document.getElementById("close-modal"),
    confirmAddBtn: document.getElementById("confirm-add"),
    urlInput: document.getElementById("url-input"),
    modalMessage: document.getElementById("modal-message"),
  };

  // --- Player Events ---

  // Update play button icon
  player.onPlayStateChange = (isPlaying) => {
    elements.playBtn.innerHTML = isPlaying
      ? '<i class="fas fa-pause"></i>'
      : '<i class="fas fa-play"></i>';
  };

  // Update progress bar
  player.onTimeUpdate = (current, total) => {
    if (isFinite(total) && total > 0) {
      const percent = (current / total) * 100;
      elements.progressBar.value = percent;

      // Update time text
      elements.currentTime.textContent = formatTime(current);
      elements.totalTime.textContent = formatTime(total);

      // Update slider aesthetic background
      elements.progressBar.style.background = `linear-gradient(to right, var(--primary) ${percent}%, rgba(255,255,255,0.1) ${percent}%)`;
    }
  };

  // Auto-next
  player.onTrackEnded = async () => {
    const nextTrack = await playlistManager.nextTrack();
    if (nextTrack) {
      player.loadTrack(nextTrack);
    }
  };

  // --- Playlist Manager Events ---

  // Update Playlist UI
  playlistManager.onPlaylistUpdated = (tracks, stats) => {
    renderPlaylist(tracks);
    elements.totalTracks.textContent = `${stats.total_tracks} tracks`;
  };

  // Update Current Track Info
  playlistManager.onTrackChange = (track) => {
    if (track) {
      elements.currentTitle.textContent = track.title;
      elements.currentArtist.textContent = track.uploader || "Unknown Artist";
      document.title = `${track.title} - AudioLab`;
    }
  };

  // --- Helpers ---

  function formatTime(seconds) {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  }

  function renderPlaylist(tracks) {
    elements.playlistContainer.innerHTML = "";

    if (tracks.length === 0) {
      elements.playlistContainer.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    <i class="fas fa-music" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <p>Playlist Empty. Add a URL!</p>
                </div>
            `;
      return;
    }

    tracks.forEach((track, index) => {
      const isActive =
        playlistManager.currentTrack &&
        playlistManager.currentTrack.id === track.id;

      const div = document.createElement("div");
      div.className = `track-item ${isActive ? "active" : ""}`;
      div.innerHTML = `
                <div class="track-index">
                    ${
                      isActive
                        ? '<i class="fas fa-volume-up" style="color: var(--primary)"></i>'
                        : index + 1
                    }
                </div>
                <div class="track-info">
                    <div class="track-title">${track.title}</div>
                    <div class="track-meta">
                        <span>${track.uploader || "Unknown"}</span>
                    </div>
                </div>
                <div class="track-duration">${formatTime(track.duration)}</div>
                <div class="track-actions">
                    <button class="action-btn delete-btn" data-id="${track.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;

      // Play on Click (excluding actions)
      div.addEventListener("click", async (e) => {
        if (!e.target.closest(".action-btn")) {
          const loadedTrack = await playlistManager.setTrack(track.id);
          if (loadedTrack) player.loadTrack(loadedTrack);
        }
      });

      // Delete Action
      const deleteBtn = div.querySelector(".delete-btn");
      deleteBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        if (confirm("Delete this track?")) {
          await playlistManager.removeTrack(track.id);
        }
      });

      elements.playlistContainer.appendChild(div);
    });
  }

  // --- UI Interactions ---

  // Play/Pause
  elements.playBtn.addEventListener("click", () => {
    if (!player.currentTrackId && playlistManager.tracks.length > 0) {
      // First play
      const track = playlistManager.tracks[0];
      playlistManager.setTrack(track.id).then((t) => player.loadTrack(t));
    } else {
      player.togglePlay();
    }
  });

  // Next/Prev
  elements.nextBtn.addEventListener("click", async () => {
    const t = await playlistManager.nextTrack();
    if (t) player.loadTrack(t);
  });

  elements.prevBtn.addEventListener("click", async () => {
    const t = await playlistManager.previousTrack();
    if (t) player.loadTrack(t);
  });

  // Shuffle
  elements.shuffleBtn.addEventListener("click", async () => {
    await playlistManager.shuffle();
  });

  // Seek
  elements.progressBar.addEventListener("input", (e) => {
    const percent = e.target.value;
    const time = (percent / 100) * player.getDuration();
    player.seek(time);
    elements.progressBar.style.background = `linear-gradient(to right, var(--primary) ${percent}%, rgba(255,255,255,0.1) ${percent}%)`;
  });

  // Volume
  elements.volumeSlider.addEventListener("input", (e) => {
    const val = e.target.value;
    player.setVolume(val);
  });

  // --- Modal Logic ---
  const showModal = () => {
    elements.modalOverlay.classList.add("show");
    elements.urlInput.focus();
  };

  const hideModal = () => {
    elements.modalOverlay.classList.remove("show");
    elements.urlInput.value = "";
    elements.modalMessage.textContent = "";
    elements.modalMessage.className = "";
  };

  elements.addBtn.addEventListener("click", showModal);
  elements.closeModalBtn.addEventListener("click", hideModal);

  // Add URL
  elements.confirmAddBtn.addEventListener("click", async () => {
    const url = elements.urlInput.value.trim();
    if (!url) return;

    const btn = elements.confirmAddBtn;
    const originalText = btn.innerHTML;
    btn.innerHTML =
      '<span class="loader" style="width: 15px; height: 15px;"></span> Adding...';
    btn.disabled = true;

    const result = await playlistManager.addUrl(url);

    if (result.success) {
      btn.innerHTML = '<i class="fas fa-check"></i> Added!';
      setTimeout(() => {
        hideModal();
        btn.innerHTML = originalText;
        btn.disabled = false;
      }, 1000);
    } else {
      elements.modalMessage.textContent = result.error || "Error adding URL";
      elements.modalMessage.style.color = "var(--error)";
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  });

  // Initial Load
  playlistManager.fetchPlaylist();
});
