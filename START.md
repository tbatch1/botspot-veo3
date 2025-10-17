# 🚀 Quick Start Guide

## Your project is ready! Here's how to run it:

### Step 1: Get Your API Key
1. Go to https://makersuite.google.com/app/apikey
2. Create a Gemini API key
3. Copy it

### Step 2: Configure Backend
1. Open `backend/.env` in a text editor
2. Replace `your_gemini_api_key_here` with your actual API key:
   ```
   GEMINI_API_KEY=your_actual_key_here
   ```

### Step 3: Start MongoDB (Choose one option)

**Option A: Docker (Easiest)**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:7.0
```

**Option B: Local Install**
- macOS: `brew services start mongodb-community`
- Linux: `sudo systemctl start mongod`
- Windows: Start MongoDB service from Services

### Step 4: Start Backend
Open a terminal in the project folder:
```bash
cd backend
npm start
```

You should see:
```
╔═══════════════════════════════════════════╗
║   Botspot Veo 3 API Server Running       ║
╠═══════════════════════════════════════════╣
║   Port: 3000
║   Environment: development
║   API Key: ✓ Set
╚═══════════════════════════════════════════╝
```

### Step 5: Start Frontend
Open a NEW terminal in the project folder:
```bash
cd frontend
npm start
```

The app will open at http://localhost:3000

## 🎉 You're Done!

The frontend will open automatically in your browser. You can now:
- Enter a video prompt
- Choose a model (Fast or Standard)
- Set duration (4-8 seconds)
- Click "Generate Video"
- Watch the progress bar
- Download your video when complete!

## 🧪 Test the API

In a new terminal, test the backend directly:
```bash
# Health check
curl http://localhost:3000/api/health

# Estimate cost
curl -X POST http://localhost:3000/api/videos/estimate-cost \
  -H "Content-Type: application/json" \
  -d '{"duration": 8, "model": "veo-3-fast-generate-001"}'
```

## 📝 Environment Files

### backend/.env
```env
PORT=3000
NODE_ENV=development
GEMINI_API_KEY=your_actual_key_here
MONGO_URI=mongodb://localhost:27017/botspot-veo3
CORS_ORIGIN=*
```

### frontend/.env
```env
REACT_APP_API_URL=http://localhost:3000
```

## 🐛 Troubleshooting

**"Cannot connect to MongoDB"**
- Make sure MongoDB is running (Step 3)
- Check if port 27017 is available

**"API key not set"**
- Check backend/.env file
- Make sure GEMINI_API_KEY is set correctly
- Restart the backend server

**Frontend shows error connecting to backend**
- Make sure backend is running on port 3000
- Check backend/.env has CORS_ORIGIN=*
- Restart both servers

## 💡 Tips

- Backend runs on port 3000
- Frontend runs on port 3000 (React dev server will auto-assign if 3000 is taken)
- Videos cost $0.40-$0.50 per second depending on model
- Keep prompts between 10-2000 characters
- Generation takes 30-60 seconds typically

## 🎬 Example Prompts

Try these to get started:
- "A serene ocean sunset with gentle waves"
- "Dramatic reveal of trading charts rising"
- "Professional office setting with keyboard typing"
- "Fast-paced montage of stock market indicators"

---

**Need more help?** Check the main [README.md](README.md) for full documentation!
