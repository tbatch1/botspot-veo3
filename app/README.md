# Botspot Veo3 - AI Trading Bot Demo Videos

Create stunning demo videos for your trading strategies in seconds, powered by Google Veo 3 AI.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- MongoDB (for backend)
- Google Gemini API Key (for real video generation)

### Frontend Setup

1. **Install dependencies:**
```bash
cd app
npm install
```

2. **Run the development server:**
```bash
npm run dev
```

3. **Open your browser:**
Navigate to [http://localhost:3002](http://localhost:3002) (port may vary)

### Backend Setup

1. **Navigate to backend:**
```bash
cd ../backend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Configure environment variables:**
Create a `.env` file in the `backend/` directory:

```env
PORT=3000
NODE_ENV=development
GEMINI_API_KEY=your_gemini_api_key_here
MONGO_URI=mongodb://localhost:27017/botspot-veo3
CORS_ORIGIN=*
```

4. **Get your Google Gemini API Key:**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the API key
   - Add it to `backend/.env` as `GEMINI_API_KEY=your_key_here`

5. **Start MongoDB** (if not already running):
```bash
mongod
```

6. **Start the backend server:**
```bash
npm start
```

The backend will start on [http://localhost:3000](http://localhost:3000)

## 🔑 API Key Configuration

### Where to Add Your API Key

**Location:** `backend/.env`

**Example:**
```env
GEMINI_API_KEY=AIzaSyAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq
```

### How to Get Your Gemini API Key

1. Go to [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"** or **"Get API Key"**
4. Copy the generated key (starts with `AIza...`)
5. Paste it into `backend/.env` file

### Verifying API Key Setup

After adding your API key:

1. **Restart the backend server** (Ctrl+C and `npm start`)
2. Check the server startup output:
   ```
   ╔═══════════════════════════════════════════╗
   ║   Botspot Veo 3 API Server Running       ║
   ╠═══════════════════════════════════════════╣
   ║   Port: 3000
   ║   Environment: development
   ║   API Key: ✓ Set                         ← Should show ✓ Set
   ╚═══════════════════════════════════════════╝
   ```

3. **Test the health endpoint:**
   ```bash
   curl http://localhost:3000/api/health
   ```

4. **Check the frontend:**
   - You should NOT see a warning toast about missing API key
   - Video generation will work with real Google Veo 3

### Without API Key (Demo Mode)

If you don't add an API key:
- App will show a warning toast on load
- Video generation will still work but uses demo/mock responses
- Stats will default to zeros or mock data

## 📁 Project Structure

```
app/
├── components/          # React components
│   ├── Hero.tsx        # Hero section with stats
│   ├── Studio/         # 3-panel video studio
│   └── Gallery.tsx     # Video gallery with filters
├── lib/                # Utilities
│   ├── api-client.ts   # Backend API client
│   ├── logger.ts       # Logging utilities
│   └── utils.ts        # Helper functions
└── data/
    └── templates.ts    # Video prompt templates

backend/
├── server.js           # Express API server
├── models.js          # MongoDB schemas
├── veo3-service.js    # Google Veo 3 integration
└── .env               # Environment variables (create this)
```

## 🧪 Testing

```bash
# Run unit tests
npm test

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

## 🎨 Features

- **AI Video Generation** - Create trading bot demo videos with Google Veo 3
- **Real-time Stats** - Platform-wide statistics from backend API
- **Template Library** - 12 pre-built trading scenario templates
- **3-Panel Studio** - Prompt builder, live preview, and configuration
- **Video Gallery** - Browse, filter, search, and share videos
- **Comprehensive Logging** - All actions logged for debugging
- **Error Handling** - Graceful error handling with toast notifications

## 🔧 Troubleshooting

### Port Conflicts
If port 3000 or 3002 is already in use, Next.js will automatically find the next available port. Check the terminal output for the actual port.

### Backend Connection Issues
- Ensure backend is running on port 3000
- Check CORS settings in `backend/server.js`
- Verify MongoDB is running
- Check browser console for errors

### API Key Issues
- Verify the key starts with `AIza`
- No spaces or quotes around the key in `.env`
- Restart backend after adding/changing key
- Check API key quota at [Google Cloud Console](https://console.cloud.google.com/)

### Stats Not Loading
- Ensure backend `/api/stats` endpoint is accessible
- Check MongoDB connection
- Review browser console logs (look for `[INFO]` and `[ERROR]` messages)

## 📚 API Endpoints

### Frontend → Backend

- `GET /api/health` - Health check and API key status
- `GET /api/stats` - Platform statistics (videos, users, revenue)
- `POST /api/videos/generate` - Generate video
- `POST /api/videos/estimate-cost` - Cost estimation
- `GET /api/models` - Available Veo 3 models
- `GET /api/templates` - Prompt templates

## 🚢 Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) for production deployment instructions.

## 🛠️ Built With

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Axios** - HTTP client
- **Sonner** - Toast notifications
- **Express.js** - Backend API
- **MongoDB** - Database
- **Google Veo 3** - AI video generation

## 📄 License

MIT
