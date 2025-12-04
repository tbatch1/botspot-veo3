const fs = require('fs/promises');
const path = require('path');

const STORE_PATH = path.join(__dirname, 'generation-jobs.json');

async function loadJobs() {
  try {
    const data = await fs.readFile(STORE_PATH, 'utf-8');
    const parsed = JSON.parse(data);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    if (error.code === 'ENOENT') {
      return [];
    }
    console.warn('[JobStore] Failed to read jobs file:', error.message);
    return [];
  }
}

async function saveJobs(jobs) {
  await fs.writeFile(STORE_PATH, JSON.stringify(jobs, null, 2), 'utf-8');
}

async function createJob(job) {
  const jobs = await loadJobs();
  const filtered = jobs.filter((existing) => existing.id !== job.id);
  filtered.unshift(job);
  await saveJobs(filtered);
  return job;
}

async function updateJob(id, updates) {
  const jobs = await loadJobs();
  const index = jobs.findIndex((job) => job.id === id);
  if (index === -1) return null;
  jobs[index] = {
    ...jobs[index],
    ...updates,
    updatedAt: new Date().toISOString()
  };
  await saveJobs(jobs);
  return jobs[index];
}

async function getJob(id) {
  const jobs = await loadJobs();
  return jobs.find((job) => job.id === id) || null;
}

module.exports = {
  createJob,
  updateJob,
  getJob
};
