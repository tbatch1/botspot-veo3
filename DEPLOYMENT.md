# 🚀 Deployment Guide - Botspot Veo3

## Production Deployment Options

### Option 1: Docker (Recommended)

The easiest way to deploy Botspot Veo3 is using Docker Compose:

```bash
# From project root
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**What gets deployed:**
- MongoDB database (port 27017)
- Backend API (port 3000)
- Frontend (port 80 via Nginx)

### Option 2: Manual Production Build

#### Backend Production

```bash
cd backend

# Install production dependencies
npm install --production

# Set environment variables
export NODE_ENV=production
export GEMINI_API_KEY=your_api_key_here
export MONGO_URI=mongodb://your-mongo-host:27017/botspot-veo3
export PORT=3000

# Start with PM2 (process manager)
npm install -g pm2
pm2 start server.js --name botspot-api

# Or use forever
npm install -g forever
forever start server.js
```

#### Frontend Production

```bash
cd app

# Build production bundle
npm run build

# Start production server
npm start

# Or use PM2
pm2 start npm --name botspot-frontend -- start
```

### Option 3: Vercel + MongoDB Atlas

**Frontend (Vercel)**:
1. Push code to GitHub
2. Connect repository to Vercel
3. Set build command: `cd app && npm run build`
4. Set output directory: `app/.next`
5. Add environment variable: `NEXT_PUBLIC_API_URL`

**Backend (Railway/Render/Heroku)**:
1. Deploy backend to your platform of choice
2. Set environment variables
3. Connect to MongoDB Atlas
4. Update frontend `NEXT_PUBLIC_API_URL`

---

## Environment Variables

### Backend (.env)
```bash
# Required
PORT=3000
NODE_ENV=production
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/botspot-veo3

# Optional (for real video generation)
GEMINI_API_KEY=your_gemini_api_key_here

# Security
CORS_ORIGIN=https://yourdomain.com
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## Pre-Deployment Checklist

### Security
- [ ] Change default MongoDB credentials
- [ ] Set CORS_ORIGIN to your domain
- [ ] Add rate limiting (already configured)
- [ ] Enable HTTPS/TLS
- [ ] Set secure cookies
- [ ] Add CSP headers
- [ ] Remove console.logs from production

### Performance
- [ ] Run `npm run build` without errors
- [ ] Test production build locally
- [ ] Check bundle size (<300KB)
- [ ] Enable CDN for static assets
- [ ] Configure caching headers
- [ ] Add compression (gzip/brotli)

### Monitoring
- [ ] Set up error tracking (Sentry/LogRocket)
- [ ] Configure uptime monitoring
- [ ] Set up analytics
- [ ] Add health check endpoints
- [ ] Configure log aggregation

### Testing
- [ ] All tests passing (`npm run test:ci`)
- [ ] E2E tests passing (`npm run e2e`)
- [ ] Manual QA on staging
- [ ] Load testing completed
- [ ] Security audit passed

---

## Production Configuration

### Nginx Configuration (if not using Docker)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### MongoDB Atlas Setup

1. Create cluster at mongodb.com/cloud/atlas
2. Whitelist IP addresses
3. Create database user
4. Get connection string
5. Add to `MONGO_URI` environment variable

```
mongodb+srv://username:password@cluster.mongodb.net/botspot-veo3?retryWrites=true&w=majority
```

---

## Monitoring

### Health Checks

```bash
# Backend health
curl https://api.yourdomain.com/api/health

# Expected response
{
  "status": "healthy",
  "service": "Veo 3 API",
  "timestamp": "2025-10-03T...",
  "apiKey": "configured",
  "canGenerateVideos": true
}
```

### Logs

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# PM2 logs
pm2 logs botspot-api
pm2 logs botspot-frontend

# Check errors
grep "ERROR" backend/logs/error.log
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  backend:
    image: botspot-backend
    deploy:
      replicas: 3
    environment:
      - MONGO_URI=${MONGO_URI}
```

### Load Balancing

Use Nginx or cloud load balancer to distribute traffic across backend instances.

### Database

- Use MongoDB Atlas with auto-scaling
- Enable sharding for large datasets
- Add read replicas for high traffic

---

## Troubleshooting

### App won't start
```bash
# Check logs
docker-compose logs

# Verify environment variables
docker-compose config

# Restart services
docker-compose restart
```

### Database connection issues
```bash
# Test MongoDB connection
mongo "mongodb+srv://cluster.mongodb.net/test" --username user

# Check network connectivity
ping cluster.mongodb.net
```

### Frontend errors
```bash
# Rebuild
cd app && npm run build

# Clear cache
rm -rf .next

# Check API connection
curl http://localhost:3000/api/health
```

---

## Rollback Procedure

### Docker
```bash
# List available versions
docker images botspot-backend

# Rollback to previous version
docker-compose down
docker tag botspot-backend:v1.0 botspot-backend:latest
docker-compose up -d
```

### Manual
```bash
# Checkout previous version
git log --oneline
git checkout <commit-hash>

# Rebuild and restart
npm run build
pm2 restart all
```

---

## Support

For production issues:
1. Check logs first
2. Verify environment variables
3. Test API health endpoint
4. Review recent deployments
5. Contact support@botspot.trade

---

**Deployment completed? Run through the checklist above!** ✅
