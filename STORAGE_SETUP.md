# Google Cloud Storage Setup Guide

**Status**: ✅ Code Complete - Ready for GCS Configuration
**Last Updated**: 2025-10-16

---

## 📋 Overview

This guide walks you through setting up Google Cloud Storage (GCS) for the Botspot Veo3 video sequencer. GCS is used to store:

- **Extracted last frames** (for Veo 3.1 continuity between scenes)
- **Combined videos** (final exported sequences)
- **Thumbnails** (for timeline preview - future feature)

**Cost**: ~$1-5/month (uses your $300 free credits)

---

## 🎯 What's Already Done

✅ **Backend code complete**:
- [StorageService](backend/storage-service.js) - Full GCS integration (~450 lines)
- [VideoSequenceService](backend/video-sequence-service.js) - Integrated with GCS uploads
- [@google-cloud/storage](backend/package.json) - Dependency installed
- [.env.example](backend/.env.example) - Configuration template

---

## 🚀 Setup Steps

### Step 1: Create GCS Bucket (5 minutes)

1. **Go to Google Cloud Console**
   - Open: https://console.cloud.google.com/storage
   - Make sure you're in your project: `project-b81c0335-9c6e-43aa-8be`

2. **Create Bucket**
   - Click **"CREATE BUCKET"**
   - Bucket name: `botspot-veo3` (or your preferred name)
   - Location type: **Region** → **us-central1** (or closest to you)
   - Storage class: **Standard**
   - Access control: **Uniform** (recommended)
   - Click **CREATE**

3. **Make Bucket Public** (for Veo API access)
   ```bash
   # Option A: Make all objects public by default
   # In bucket → Permissions → Add Principal:
   # - Principal: allUsers
   # - Role: Storage Object Viewer

   # Option B: Files are made public on upload (current implementation)
   # No action needed - StorageService handles this automatically
   ```

---

### Step 2: Setup Authentication (Choose One Method)

#### **Option A: Application Default Credentials** (Easiest - Recommended)

1. **Install gcloud CLI** (if not installed)
   - Windows: https://cloud.google.com/sdk/docs/install#windows
   - Mac: `brew install google-cloud-sdk`
   - Linux: https://cloud.google.com/sdk/docs/install#linux

2. **Authenticate**
   ```bash
   gcloud auth application-default login
   ```

3. **Set Project**
   ```bash
   gcloud config set project project-b81c0335-9c6e-43aa-8be
   ```

4. **Update `.env` file**
   ```bash
   # Copy .env.example to .env
   cp backend/.env.example backend/.env

   # Edit .env - add these lines:
   GCS_PROJECT_ID=project-b81c0335-9c6e-43aa-8be
   GCS_BUCKET_NAME=botspot-veo3
   # GCS_KEY_FILE is not needed with application default credentials
   ```

**✅ Done! Skip to Step 3.**

---

#### **Option B: Service Account Key File** (More secure for production)

1. **Create Service Account**
   - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Click **"CREATE SERVICE ACCOUNT"**
   - Name: `botspot-veo3-storage`
   - Role: **Storage Admin** (or **Storage Object Admin** for less permissions)
   - Click **DONE**

2. **Create Key**
   - Click on the service account you just created
   - Go to **KEYS** tab
   - Click **ADD KEY** → **Create new key**
   - Type: **JSON**
   - Click **CREATE**
   - Save the downloaded JSON file securely (e.g., `backend/gcs-key.json`)

3. **Update `.env` file**
   ```bash
   # Copy .env.example to .env
   cp backend/.env.example backend/.env

   # Edit .env - add these lines:
   GCS_PROJECT_ID=project-b81c0335-9c6e-43aa-8be
   GCS_BUCKET_NAME=botspot-veo3
   GCS_KEY_FILE=backend/gcs-key.json
   ```

4. **Add to .gitignore** (IMPORTANT!)
   ```bash
   echo "backend/gcs-key.json" >> .gitignore
   echo "backend/.env" >> .gitignore
   ```

**✅ Done! Continue to Step 3.**

---

### Step 3: Test GCS Integration (2 minutes)

1. **Start the server**
   ```bash
   cd backend
   npm start
   ```

2. **Check logs for GCS initialization**
   ```
   [StorageService] ✅ Initialized
   [StorageService] Project: project-b81c0335-9c6e-43aa-8be
   [StorageService] Bucket: botspot-veo3
   ```

3. **Test with curl** (optional)
   ```bash
   # Create a test sequence
   curl -X POST http://localhost:4000/api/sequences \
     -H "Content-Type: application/json" \
     -d '{"userId":"test","title":"GCS Test Sequence"}'

   # Response will include sequenceId
   ```

---

## 📁 GCS Bucket Structure

After generating sequences, your bucket will look like this:

```
gs://botspot-veo3/
├── frames/
│   ├── seq_abc123_scene1_lastframe.jpg
│   ├── seq_abc123_scene2_lastframe.jpg
│   └── seq_def456_scene1_lastframe.jpg
├── videos/
│   ├── combined_seq_abc123.mp4
│   └── combined_seq_def456.mp4
└── thumbnails/  (future feature)
    ├── seq_abc123_scene1_thumbnail.jpg
    └── seq_abc123_scene2_thumbnail.jpg
```

---

## 🔐 Security Best Practices

### ✅ DO:
- Use Application Default Credentials for local development
- Use Service Account keys for production deployment
- Add service account key files to `.gitignore`
- Use least-privilege IAM roles (Storage Object Admin, not Owner)
- Set up billing alerts in Google Cloud Console
- Rotate service account keys regularly

### ❌ DON'T:
- Commit service account keys to git
- Share service account keys publicly
- Use Owner/Editor roles when Object Admin is sufficient
- Leave unused buckets with public access

---

## 💰 Cost Management

### Current Usage Estimate:
- **Storage**: 100 frames @ 1MB each = 100MB = $0.002/month
- **Storage**: 10 videos @ 50MB each = 500MB = $0.01/month
- **Bandwidth**: 50GB downloads = $6/month (only if videos downloaded externally)

**Total**: ~$1-5/month for moderate usage

### Monitor Costs:
1. Go to: https://console.cloud.google.com/billing
2. Set up budget alerts:
   - Budget name: "Botspot Veo3"
   - Amount: $50/month
   - Alert threshold: 50%, 90%, 100%

---

## 🧪 Testing GCS Integration

### Test 1: Upload Last Frame

```javascript
// In backend/test-storage.js
const { StorageService } = require('./storage-service');

async function test() {
  const storage = new StorageService();

  // Test upload
  const result = await storage.uploadLastFrame(
    'path/to/test-image.jpg',
    'seq_test123',
    1
  );

  console.log('✅ Upload successful!');
  console.log('Public URL:', result.publicUrl);
}

test();
```

Run:
```bash
node backend/test-storage.js
```

### Test 2: Full Sequence Workflow

```bash
# 1. Create sequence
curl -X POST http://localhost:4000/api/sequences \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test",
    "title": "GCS Test",
    "description": "Testing GCS integration"
  }'

# 2. Add scenes
curl -X POST http://localhost:4000/api/sequences/SEQ_ID/scenes \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test scene 1",
    "duration": 8
  }'

# 3. Generate (mock mode for testing)
VEO3_MOCK=true npm start
curl -X POST http://localhost:4000/api/sequences/SEQ_ID/generate

# 4. Check GCS bucket
# Go to https://console.cloud.google.com/storage/browser/botspot-veo3
# You should see frames/ directory with uploaded frames
```

---

## 🐛 Troubleshooting

### Error: "Could not load the default credentials"

**Solution**:
```bash
# Run application default login
gcloud auth application-default login

# Or specify key file in .env
GCS_KEY_FILE=path/to/key.json
```

### Error: "Bucket not found"

**Solution**:
1. Check bucket exists: https://console.cloud.google.com/storage
2. Verify bucket name in `.env` matches exactly
3. Ensure you have permissions to access the bucket

### Error: "Permission denied"

**Solution**:
1. Check IAM permissions for service account
2. Ensure service account has **Storage Object Admin** role
3. Verify project ID is correct

### Error: "The caller does not have permission"

**Solution**:
```bash
# Grant permissions to service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectAdmin"
```

---

## 📚 Additional Resources

- **Google Cloud Storage Docs**: https://cloud.google.com/storage/docs
- **Pricing Calculator**: https://cloud.google.com/products/calculator
- **IAM Roles**: https://cloud.google.com/storage/docs/access-control/iam-roles
- **Node.js Client Library**: https://googleapis.dev/nodejs/storage/latest

---

## ✅ Verification Checklist

Before considering setup complete, verify:

- [ ] GCS bucket created and accessible
- [ ] Authentication configured (gcloud or service account)
- [ ] `.env` file updated with correct values
- [ ] Server starts without GCS errors
- [ ] Test sequence creates successfully
- [ ] Can view bucket contents in GCS console
- [ ] Files are publicly accessible (if needed)
- [ ] Billing alerts configured

---

## 🎉 You're Done!

GCS is now integrated! The system will automatically:
- ✅ Extract last frame after each scene generation
- ✅ Upload frame to GCS (`gs://botspot-veo3/frames/...`)
- ✅ Return public HTTPS URL for Veo API
- ✅ Upload combined video after export
- ✅ Clean up local files after upload

**Next Steps**:
- Run backend tests to verify everything works
- Start building the frontend VideoSequencer UI
- Deploy to production with proper security

---

**Questions or issues?** Check the troubleshooting section or review the [StorageService code](backend/storage-service.js) for implementation details.
