# Express.js Backend Deployment Guide

Quick deployment options for the Accessibility Checker Express.js backend.

## 🚀 Quick Deploy Options

### 1. Railway (Recommended - Easiest)

#### Prerequisites
- GitHub account
- OpenAI API key

#### Steps
1. **Fork/Clone Repository**
   ```bash
   git clone https://github.com/your-username/accessibility-checker.git
   cd express-backend
   ```

2. **Connect to Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Set Environment Variables**
   - In Railway dashboard, go to Variables tab
   - Add: `OPENAI_API_KEY=your_openai_api_key_here`
   - Add: `NODE_ENV=production`

4. **Deploy**
   - Railway automatically detects `package.json`
   - Builds and deploys automatically
   - Get your live URL!

**Time to deploy: 2-3 minutes** ⚡

### 2. Render

#### Prerequisites
- GitHub account
- OpenAI API key

#### Steps
1. **Connect Repository**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
   - **Name**: accessibility-checker-api
   - **Environment**: Node
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`

3. **Set Environment Variables**
   - In Render dashboard, go to Environment tab
   - Add: `OPENAI_API_KEY=your_openai_api_key_here`
   - Add: `NODE_ENV=production`

4. **Deploy**
   - Click "Create Web Service"
   - Render builds and deploys automatically

**Time to deploy: 5-7 minutes** ⚡

### 3. Vercel

#### Prerequisites
- Vercel account
- OpenAI API key

#### Steps
1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy**
   ```bash
   cd express-backend
   vercel --prod
   ```

3. **Set Environment Variables**
   - In Vercel dashboard
   - Go to Settings → Environment Variables
   - Add: `OPENAI_API_KEY=your_openai_api_key_here`

**Time to deploy: 3-5 minutes** ⚡

### 4. Heroku

#### Prerequisites
- Heroku account
- Heroku CLI
- OpenAI API key

#### Steps
1. **Install Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Or download from heroku.com
   ```

2. **Create Heroku App**
   ```bash
   cd express-backend
   heroku create your-app-name
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set OPENAI_API_KEY=your_openai_api_key_here
   heroku config:set NODE_ENV=production
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

**Time to deploy: 5-10 minutes** ⚡

## 🔧 Environment Variables

### Required
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Optional
```bash
PORT=3000
NODE_ENV=production
LOG_LEVEL=info
ALLOWED_ORIGINS=*
RATE_LIMIT_MAX_REQUESTS=100
MAX_FILE_SIZE=10485760
MAX_FILES=5
```

## 📊 Platform Comparison

| Platform | Setup Time | Cost | Ease | Features |
|----------|------------|------|------|----------|
| **Railway** | 2-3 min | $5/month | ⭐⭐⭐⭐⭐ | Auto-deploy, easy config |
| **Render** | 5-7 min | Free tier | ⭐⭐⭐⭐ | Good free tier |
| **Vercel** | 3-5 min | Free tier | ⭐⭐⭐⭐ | Great for APIs |
| **Heroku** | 5-10 min | $7/month | ⭐⭐⭐ | Most features |

## 🎯 Recommended for Hackathons

### **Railway** (Best Choice)
- ✅ Fastest setup
- ✅ Automatic deployments
- ✅ Easy environment variables
- ✅ Good free tier
- ✅ No credit card required

### **Render** (Free Option)
- ✅ Completely free
- ✅ Good performance
- ✅ Easy setup
- ✅ Automatic deployments

## 🚀 Production Optimizations

### 1. Add Health Checks
```javascript
// Already included in server.js
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});
```

### 2. Enable Logging
```javascript
// Already configured with Winston
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  )
});
```

### 3. Set Up Monitoring
- **Railway**: Built-in metrics
- **Render**: Built-in monitoring
- **Vercel**: Analytics included
- **Heroku**: Add-ons available

### 4. Configure CORS
```javascript
// Already configured
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
  credentials: true
}));
```

## 🔍 Testing Your Deployment

### 1. Health Check
```bash
curl https://your-app.railway.app/health
```

### 2. Test Upload
```bash
curl -X POST -F "images=@test-image.jpg" \
  https://your-app.railway.app/api/upload
```

### 3. Test Analysis
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"images":[{"filename":"test.jpg","base64":"..."}]}' \
  https://your-app.railway.app/api/analyze
```

## 🛠️ Troubleshooting

### Common Issues

#### **OpenAI API Key Error**
```bash
# Check environment variable is set
echo $OPENAI_API_KEY
```

#### **Build Failures**
```bash
# Check Node.js version
node --version  # Should be 18+

# Check package.json
cat package.json
```

#### **Memory Issues**
```bash
# Add to package.json
"scripts": {
  "start": "node --max-old-space-size=512 server.js"
}
```

#### **File Upload Issues**
```bash
# Check file size limits
MAX_FILE_SIZE=10485760  # 10MB
```

### Debug Commands

#### **Check Logs**
```bash
# Railway
railway logs

# Render
# Check dashboard logs

# Heroku
heroku logs --tail
```

#### **Test Locally**
```bash
# Test with environment variables
OPENAI_API_KEY=your_key npm start
```

## 📈 Scaling Considerations

### For High Traffic
1. **Add Redis Caching**
   ```bash
   npm install redis
   ```

2. **Implement Queue System**
   ```bash
   npm install bull
   ```

3. **Add Database**
   ```bash
   npm install pg
   ```

4. **Use CDN**
   - Cloudflare
   - AWS CloudFront

### Cost Optimization
- **Railway**: $5/month for hobby plan
- **Render**: Free tier available
- **Vercel**: Generous free tier
- **Heroku**: $7/month for basic

## 🎉 Success Checklist

- [ ] Repository connected to platform
- [ ] Environment variables set
- [ ] Health check working
- [ ] Upload endpoint working
- [ ] Analysis endpoint working
- [ ] CORS configured
- [ ] Rate limiting active
- [ ] Logging enabled
- [ ] Monitoring set up

## 🚀 Next Steps

1. **Add Frontend**: Connect React/Vue.js app
2. **Add Database**: Store analysis results
3. **Add Authentication**: User management
4. **Add Caching**: Redis for performance
5. **Add Monitoring**: Error tracking
6. **Add CI/CD**: Automated testing

---

**Ready to deploy!** 🚀 Your accessibility checker will be live in minutes!
