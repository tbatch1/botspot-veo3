const fs = require('fs');
const path = require('path');
const ffmpegPath = require('ffmpeg-static');
const ffmpeg = require('fluent-ffmpeg');
ffmpeg.setFfmpegPath(ffmpegPath);
const storePath = path.resolve(__dirname, '..', 'generated-videos.json');
const videos = JSON.parse(fs.readFileSync(storePath, 'utf-8').replace(/^\uFEFF/, ''));
const publicVideosDir = path.resolve(__dirname, '..', '..', 'app', 'public', 'videos');
const thumbnailsDir = path.resolve(__dirname, '..', '..', 'app', 'public', 'thumbnails');
if (!fs.existsSync(thumbnailsDir)) fs.mkdirSync(thumbnailsDir, { recursive: true });
let changed = false;
function processVideo(video) {
  return new Promise((resolve) => {
    const local = video.localPath ? video.localPath : path.join(publicVideosDir, video.id + '.mp4');
    if (!fs.existsSync(local)) return resolve();
    const targetThumb = path.join(thumbnailsDir, video.id + '.jpg');
    ffmpeg(local)
      .frames(1)
      .output(targetThumb)
      .on('end', () => {
        video.thumbnailPath = '/thumbnails/' + video.id + '.jpg';
        video.thumbnail = video.thumbnailPath;
        changed = true;
        resolve();
      })
      .on('error', (err) => {
        console.error('Thumbnail generation failed for', video.id, err.message);
        resolve();
      })
      .run();
  });
}
(async () => {
  for (const video of videos) {
    await processVideo(video);
  }
  if (changed) {
    fs.writeFileSync(storePath, JSON.stringify(videos, null, 2));
  }
})();
