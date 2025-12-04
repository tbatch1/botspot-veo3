const fs = require('fs/promises');
const path = require('path');

const STORE_PATH = path.join(__dirname, 'generated-videos.json');
const MAX_VIDEOS = 100;

async function loadVideos() {
  try {
    const data = await fs.readFile(STORE_PATH, 'utf-8');
    const parsed = JSON.parse(data);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    if (error.code === 'ENOENT') {
      return [];
    }
    console.warn('[VideoStore] Failed to read generated videos file:', error.message);
    return [];
  }
}

async function saveVideos(videos) {
  await fs.writeFile(STORE_PATH, JSON.stringify(videos, null, 2), 'utf-8');
}

async function addVideo(entry) {
  const videos = await loadVideos();
  const filtered = videos.filter((video) => video.id !== entry.id);
  filtered.unshift(entry);

  while (filtered.length > MAX_VIDEOS) {
    filtered.pop();
  }

  await saveVideos(filtered);
  return entry;
}

async function getVideoById(id) {
  const videos = await loadVideos();
  return videos.find((video) => video.id === id) || null;
}

module.exports = {
  loadVideos,
  addVideo,
  getVideoById
};
