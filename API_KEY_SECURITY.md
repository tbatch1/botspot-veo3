# 🔐 API Key Security & Regeneration Guide

## ⚠️ CRITICAL: Your API Key Was Exposed

Your Gemini API key (`AIzaSyD5E8Ehrp_nhLA9_33yW3uEawMBZpJG-1U`) was previously exposed in the `backend/.env` file. While this file is now secured, you **MUST regenerate your API key immediately** as a security best practice.

---

## 🚨 Immediate Action Required

### Step 1: Regenerate Your API Key

1. **Go to Google AI Studio**:
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with your Google account

2. **Delete the Old Key**:
   - Find the key starting with `AIzaSyD5E8Ehrp_nhLA9_33yW3uEawMBZpJG-1U`
   - Click the delete/revoke button
   - Confirm deletion

3. **Create a New Key**:
   - Click "Create API Key" button
   - Select your Google Cloud project (or create new)
   - Copy the new key (starts with `AIza...`)
   - **Important**: Copy it now - you won't be able to see it again!

4. **Update Your Configuration**:
   ```bash
   # Edit backend/.env
   nano backend/.env  # or use your preferred editor

   # Replace the placeholder with your NEW key
   GEMINI_API_KEY=AIza_YOUR_NEW_KEY_HERE
   ```

5. **Restart Backend**:
   ```bash
   cd backend
   npm start
   ```

6. **Verify It Works**:
   - Backend should show: `API Key: ✓ Set`
   - Test generation with a sample video

---

## 🛡️ Security Best Practices

### 1. Never Commit API Keys
- ✅ `.env` files are already in `.gitignore`
- ✅ Always use `.env.example` for templates
- ❌ Never hardcode keys in source code
- ❌ Never commit `.env` files to git

### 2. Set Billing Limits
1. Go to Google Cloud Console: https://console.cloud.google.com
2. Navigate to "Billing" → "Budgets & Alerts"
3. Set monthly budget (e.g., $50/month)
4. Enable email alerts at 50%, 90%, 100%

**Veo 3 Pricing**:
- Fast Model: $0.15/second
- Standard Model: $0.40/second
- 8-second video: $1.20 - $3.20 each

### 3. Enable API Key Restrictions
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your API key
3. Under "API restrictions":
   - Select "Restrict key"
   - Choose "Vertex AI API" or "Gemini API"
4. Under "Application restrictions" (optional):
   - Add your server IP address
   - Or restrict to HTTP referrers

### 4. Use Environment Variables Properly
- ✅ Development: Use `.env` file (never commit)
- ✅ Production: Use platform environment variables
  - Vercel: Dashboard → Settings → Environment Variables
  - Railway: Dashboard → Variables
  - Docker: Use docker secrets or env files (not in image)

### 5. Monitor API Usage
1. Check usage regularly: https://console.cloud.google.com/apis/dashboard
2. Review billing: https://console.cloud.google.com/billing
3. Set up alerts for unusual activity
4. Check logs for suspicious requests

---

## 🔍 How to Check If Key Is Compromised

### Signs Your Key May Be Compromised:
- ❌ Unexpected charges in Google Cloud billing
- ❌ High API usage you didn't initiate
- ❌ Quota exceeded errors when you haven't been using it
- ❌ Key was committed to public GitHub repo
- ❌ Key was shared in chat/email/Slack

### What To Do:
1. **Immediately revoke the key**
2. **Create new key with restrictions**
3. **Review billing for unauthorized usage**
4. **Enable 2FA on your Google account**
5. **Contact Google Cloud Support** if you see fraudulent charges

---

## 📋 Configuration Checklist

### Development Environment
- [ ] API key regenerated (old one revoked)
- [ ] New key added to `backend/.env`
- [ ] `.env` file in `.gitignore` ✅ (already done)
- [ ] Backend starts successfully on port 3000
- [ ] Test video generation works
- [ ] Billing alerts configured in Google Cloud

### Production Deployment
- [ ] API key stored in platform environment variables
- [ ] Never include `.env` in Docker images
- [ ] Use secrets management (Docker secrets, K8s secrets, etc.)
- [ ] Enable API key restrictions by IP/domain
- [ ] Set strict CORS_ORIGIN in production
- [ ] Enable rate limiting (already configured)
- [ ] Monitor logs for suspicious activity

---

## 🌐 Production Deployment Security

### Docker
```yaml
# docker-compose.yml
services:
  api:
    environment:
      # Never hardcode - use .env file or secrets
      GEMINI_API_KEY: ${GEMINI_API_KEY}
```

```bash
# Create .env file for docker-compose (DO NOT COMMIT)
echo "GEMINI_API_KEY=your_new_key" > .env
docker-compose up -d
```

### Vercel + Railway/Render
```bash
# Vercel (Frontend)
vercel env add NEXT_PUBLIC_API_URL
# Value: https://your-backend-url.com

# Railway (Backend)
railway variables set GEMINI_API_KEY=your_new_key
railway variables set NODE_ENV=production
railway up
```

### Kubernetes (Advanced)
```bash
# Create secret
kubectl create secret generic veo3-secrets \
  --from-literal=gemini-api-key=your_new_key

# Use in deployment
# See k8s-deployment.yaml (create if needed)
```

---

## 🔄 Regular Maintenance

### Weekly
- [ ] Check API usage dashboard
- [ ] Review application logs for errors

### Monthly
- [ ] Review Google Cloud billing
- [ ] Verify rate limiting is working
- [ ] Check for security updates

### Quarterly
- [ ] Rotate API key (optional but recommended)
- [ ] Review and update API restrictions
- [ ] Audit user access permissions

---

## 📞 Support & Resources

### Google Cloud Support
- Console: https://console.cloud.google.com
- Support: https://cloud.google.com/support
- API Dashboard: https://console.cloud.google.com/apis/dashboard

### Veo 3 Documentation
- API Docs: https://ai.google.dev/docs
- Pricing: https://ai.google.dev/pricing
- Quotas: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

### Emergency Contact
- If you see unauthorized charges: support@google.com
- Report compromised key: https://support.google.com/cloud/answer/6310037

---

## ✅ Verification Steps

After regenerating your key, verify everything works:

```bash
# 1. Start backend
cd backend
npm start
# Should show: ✓ API Key: Set

# 2. Test health endpoint
curl http://localhost:3000/api/health
# Should return: "apiKey": "configured"

# 3. Start frontend
cd ../app
npm run dev
# Should open on http://localhost:3001

# 4. Test video generation
# Go to http://localhost:3001
# Select a template
# Click "Generate Video"
# Should work without API key errors
```

---

## 🎯 Summary

**What Was Done**:
- ✅ Removed exposed API key from `backend/.env`
- ✅ Changed backend port from 4000 → 3000
- ✅ Updated frontend API client to use port 3000
- ✅ Fixed docker-compose.yml frontend path
- ✅ Created comprehensive `.env.example`
- ✅ Added security documentation

**What You Need To Do**:
1. **Regenerate API key** at https://makersuite.google.com/app/apikey
2. **Update `backend/.env`** with new key
3. **Set billing limits** in Google Cloud Console
4. **Test the application** to ensure everything works

**Long-term Security**:
- Never commit `.env` files ✅ (already protected)
- Use environment variables in production ✅ (ready)
- Enable API restrictions ⚠️ (recommended)
- Monitor usage regularly 📊 (your responsibility)

---

**Your application is now configured for security and long-term stability!** 🎉
