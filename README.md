# 🎬 Botspot Veo 3.1 - AI Trading Bot Demo Video Platform

**Professional video generation platform for trading bot demonstrations, powered by Google Veo 3.1 AI**

![Status](https://img.shields.io/badge/status-production--ready-green)
![Tests](https://img.shields.io/badge/tests-41%2F42%20passing-brightgreen)
![Next.js](https://img.shields.io/badge/Next.js-15.5.4-black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)

---

## 🚀 Quick Start

```bash
# Start backend (Terminal 1)
cd backend && npm start

# Start frontend (Terminal 2)
cd app && npm run dev

# Open http://localhost:3001
```

---

## ✨ Features

### Core Platform
- **Modern Consensus-Inspired UI** - Professional glassmorphism design
- **3-Panel Video Studio** - Prompt builder, canvas, and configuration
- **12 Trading Templates** - Pre-built scenarios with Veo 3.1 optimized prompts
- **Real-time Cost Calculator** - Instant pricing ($0.40-$0.50/sec)
- **Video Gallery** - Filterable grid with search
- **Fully Responsive** - Desktop, tablet, mobile optimized
- **Toast Notifications** - Real-time user feedback
- **Comprehensive Testing** - 41/42 tests passing
- **Complete Logging** - Winston logger integration

### Veo 3.1 AI Features
- **Enhanced Prompt Adherence** - Better understanding of narrative structure and cinematic styles
- **Native Audio & Dialogue** - Synchronized sound with multi-person conversations
- **Video Extension** - Extend existing videos by up to 7 additional seconds
- **Reference Images** - Use up to 3 images for consistent character/style across shots
- **First/Last Frame** - Seamless transitions with interpolation
- **Improved Image-to-Video** - Better quality when converting images to video
- **Cinematic Camera Work** - Support for dolly, crane, tracking, POV shots
- **SynthID Watermarking** - Digital watermarks on all outputs

---

## 🛠️ Tech Stack

**Frontend**: Next.js 15.5, TypeScript, Tailwind CSS 4, Framer Motion
**Backend**: Express.js, MongoDB, Google Veo 3.1 API (backward compatible with Veo 3.0)
**Testing**: Jest, React Testing Library, Playwright, MSW
**AI Models**: Veo 3.1 Preview (Standard & Fast), Veo 3.0 (Legacy Support)  

---

## 📦 Installation

### Prerequisites
- Node.js 20+
- MongoDB
- Google Gemini API key (optional)

### Setup

```bash
# Install dependencies
cd backend && npm install
cd ../app && npm install

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your GEMINI_API_KEY
# Get key from: https://makersuite.google.com/app/apikey

# Start services
cd backend && npm start       # Port 3000
cd app && npm run dev          # Port 3001
```

> **🔐 Important**: See [API_KEY_SECURITY.md](API_KEY_SECURITY.md) for API key setup and security best practices

---

## 🎯 Usage

1. **Browse Templates** - 12 trading-specific video scenarios with Veo 3.1 optimized prompts
2. **Configure** - Select model (Veo 3.1 Fast/Standard or legacy 3.0), duration (4-8s), resolution
3. **Generate** - Watch real-time progress and preview with native audio
4. **Gallery** - Browse, filter, and share videos

### Veo 3.1 Prompting Formula

For best results with Veo 3.1, structure your prompts as:
```
[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]
```

**Example:**
```
Smooth camera push in on trading screen. Automated trading bot executing
perfect breakout strategy. Green candlesticks rapidly ascending through
resistance levels while bot enters positions. Modern tech office with blue
ambient lighting. Cinematic style with electronic trade confirmation sounds.
```

**Cinematography techniques:**
- Camera movements: dolly, tracking, crane, aerial, pan, POV
- Composition: wide shot, close-up, extreme close-up
- Lens effects: shallow depth of field, wide-angle, macro

**Audio direction:**
- Use quotation marks for dialogue: "Buy signal detected!"
- Specify sound effects: SFX: thunder cracks, keyboard typing
- Define ambient soundscape: electronic beats, office ambiance

---

## 🧪 Testing

```bash
cd app
npm test              # Watch mode
npm run test:ci       # CI mode
npm run e2e           # Playwright E2E
```

**Results**: 41/42 tests passing ✅

---

## 📚 API Endpoints

- `GET /api/health` - Health check
- `POST /api/videos/generate` - Generate video (Veo 3.1 & 3.0)
- `POST /api/videos/estimate-cost` - Cost estimate
- `GET /api/models` - Available models (4 models: Veo 3.1 Standard/Fast, Veo 3.0 Standard/Fast)
- `GET /api/templates` - Video templates (12 templates with Veo 3.1 optimized prompts)
- `GET /api/videos` - Get user's generated videos
- `POST /api/videos/batch` - Batch generate multiple videos

---

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

Services:
- MongoDB: 27017
- Backend API: 3000
- Frontend (Nginx): 80

---

## 📂 Project Structure

```
botspot-veo3/
├── app/                    # Next.js frontend
│   ├── components/        # UI components
│   ├── lib/              # Utils & API client
│   └── data/             # Templates
├── backend/               # Express API
│   ├── server.js         # Main server
│   ├── veo3-service.js   # Veo 3 integration
│   └── models.js         # MongoDB schemas
└── docker-compose.yml    # Docker config
```

---

## 🎨 Design System

- **Colors**: Blue (#0066FF) + Purple (#6B46FF) gradients
- **Typography**: Poppins (headings), Inter (body)
- **Components**: Glassmorphism cards, rounded corners (16px)
- **Animations**: Framer Motion with smooth transitions

---

## 📈 Performance

- Lighthouse Score: 90+
- Bundle Size: <300KB gzipped
- FCP: <1.5s
- Code splitting enabled

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add tests (maintain 70%+ coverage)
4. Submit PR

---

## 📄 License

MIT License

---

## 🆕 What's New in Veo 3.1

**Released: October 16, 2025**

### Key Improvements
- **Better Prompt Adherence**: Deeper understanding of narrative structure and cinematic styles
- **Enhanced Audio**: Native audio generation with dialogue support, multi-person conversations
- **Video Extension**: Extend existing Veo videos by up to 7 additional seconds
- **Reference Images**: Use up to 3 images to maintain consistent characters/styles
- **Improved Image-to-Video**: Better quality and prompt adherence

### Migration from Veo 3.0
The platform supports both Veo 3.1 and 3.0 models. All templates have been upgraded to Veo 3.1 with enhanced prompts following the new best practices.

**Model Mapping:**
- `veo-3.0-generate-001` → `veo-3.1-generate-preview` (recommended)
- `veo-3.0-fast-generate-001` → `veo-3.1-fast-generate-preview` (recommended)

Legacy 3.0 models remain available for backward compatibility.

---

## 🙏 Acknowledgments

- Google Veo 3.1 API
- Consensus (UI inspiration)
- Next.js Team

---

## 📖 Additional Documentation

- **[API_KEY_SECURITY.md](API_KEY_SECURITY.md)** - API key setup, security best practices, billing limits
- **[CONFIGURATION_FIXED.md](CONFIGURATION_FIXED.md)** - Complete summary of all configuration changes
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide (Docker, Vercel, etc.)
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Feature completion tracking
- **[backend/.env.example](backend/.env.example)** - Environment variable template

---

**Built for botspot.trade** 🎬
