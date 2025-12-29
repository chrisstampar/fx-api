# Deploying FastAPI to Railway

Railway is an excellent alternative to Vercel for FastAPI applications. It handles Python/ASGI apps natively without the compatibility issues.

## Why Railway?

- ✅ Native Python/ASGI support (no handler issues)
- ✅ Automatic HTTPS
- ✅ Easy GitHub integration
- ✅ Free tier available ($5 credit/month)
- ✅ No cold starts
- ✅ Better for FastAPI than Vercel

## Quick Deployment Steps

### 1. Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub (recommended for easy integration)
3. Complete account setup

### 2. Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `fx-api` repository
4. Railway will auto-detect it's a Python project

### 3. Configure Project

Railway should auto-detect:
- **Language:** Python
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

If it doesn't auto-detect, set:
- **Root Directory:** `/` (or leave empty)
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 4. Set Environment Variables

In Railway dashboard → Variables tab, add:

**Required:**
```
RPC_URLS=https://eth.llamarpc.com,https://rpc.ankr.com/eth,https://ethereum.publicnode.com
API_ENV=production
```

**Optional:**
```
SECRET_KEY=<generate using: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### 5. Deploy

Railway will automatically:
- Build your project
- Install dependencies
- Start the FastAPI server
- Provide a public URL

## Project Structure

Railway works with your existing structure:
```
api/
├── app/
│   └── main.py          # FastAPI app
├── requirements.txt      # Dependencies
├── index.py            # (Not needed for Railway, but harmless)
└── README.md
```

## Environment Variables

Set in Railway dashboard → Variables:

**Required:**
- `RPC_URLS` - Comma-separated RPC endpoints
- `API_ENV=production`

**Optional:**
- `SECRET_KEY` - Generate secure key
- `ALLOWED_ORIGINS` - CORS origins
- `RATE_LIMIT_PER_MINUTE` - Default: 100
- `RATE_LIMIT_PER_HOUR` - Default: 5000
- `RATE_LIMIT_PER_DAY` - Default: 50000

## Railway vs Vercel

| Feature | Railway | Vercel |
|---------|---------|--------|
| FastAPI Support | ✅ Native | ❌ Issues |
| Python Runtime | ✅ Excellent | ⚠️ Problematic |
| Cold Starts | ✅ Minimal | ✅ None |
| Free Tier | $5/month credit | Free (limited) |
| Timeout | Unlimited | 10s (free) |
| Setup | Simple | Complex |

## Troubleshooting

### Build Fails

- Check Railway logs for error messages
- Verify `requirements.txt` is correct
- Ensure Python version is compatible (3.8+)

### App Won't Start

- Check start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Verify environment variables are set
- Check Railway logs for startup errors

### Port Issues

Railway automatically sets `$PORT` environment variable. Your app should use:
```python
port = int(os.getenv("PORT", 8000))
```

But with uvicorn command above, Railway handles this automatically.

## Cost

- **Free Tier:** $5 credit/month
- **Hobby Plan:** $5/month (if you exceed free credit)
- Usually free tier is enough for API usage

## Next Steps

1. Deploy to Railway
2. Test your API endpoints
3. Update your frontend to use Railway URL
4. Set up custom domain (optional)

---

**Note:** Railway is much more reliable for FastAPI than Vercel. You shouldn't encounter the handler issues we had with Vercel.

