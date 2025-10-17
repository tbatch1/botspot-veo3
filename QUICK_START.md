# 🚀 Quick Start Guide

## ✅ Configuration Complete!

All ports have been standardized and the application is ready to use:
- **Backend API**: Port 3000
- **Frontend**: Port 3001

---

## 🔑 Add Your API Key

1. Open `backend/.env` in your text editor
2. Find line 9: `GEMINI_API_KEY=your_gemini_api_key_here`
3. Replace `your_gemini_api_key_here` with your actual Gemini API key
4. Save the file

**Get an API key**: https://makersuite.google.com/app/apikey

---

## ▶️ Start the Application

### Terminal 1 - Backend
```bash
cd backend
npm start
```

**Expected output**:
```
╔═══════════════════════════════════════════╗
║   Botspot Veo 3 API Server Running       ║
╠═══════════════════════════════════════════╣
║   Port: 3000                            ✅
║   Environment: development
║   API Key: ✓ Set                        ✅
╚═══════════════════════════════════════════╝
```

### Terminal 2 - Frontend
```bash
cd app
npm run dev
```

**Expected output**:
```
▲ Next.js 15.5.4
- Local:        http://localhost:3001  ✅
```

### Open Browser
Navigate to: **http://localhost:3001**

---

## 🎬 Test Video Generation

1. Browse the 12 trading templates on the left
2. Click a template to load it
3. Configure duration/resolution on the right
4. Click "Generate Video"
5. Watch the progress bar
6. Video appears when complete!

---

## 🔧 All Changes Made

✅ Backend port: 4000 → **3000**
✅ Frontend port: 3000 → **3001**
✅ API client: Updated to connect to port 3000
✅ Docker: Fixed frontend directory path
✅ API key: Secured (you add your key to .env)

---

## 📝 Configuration Files

- `backend/.env` - Add your API key here
- `backend/.env.example` - Template with all options
- `docker-compose.yml` - Fixed for Docker deployment

---

## ❓ Troubleshooting

**Backend won't start?**
- Check if MongoDB is running (optional, works without it)
- Verify your API key in `backend/.env`

**Frontend can't connect?**
- Make sure backend is running on port 3000
- Check no other app is using port 3001

**API key errors?**
- Get key from: https://makersuite.google.com/app/apikey
- Add to `backend/.env` line 9
- Restart backend

---

**That's it! Everything is configured and ready to go.** 🎉

Just add your API key and start both servers.
