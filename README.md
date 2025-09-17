# Nonprofit Intelligence Platform

## 🎯 Zero-Cost Nonprofit Data Analysis Platform

A completely free, open-source platform for searching and analyzing IRS nonprofit data. Built specifically for NGOs with zero budget for software.

## ✨ Features

- 🔍 Search 2.1M+ nonprofit organizations
- 📊 Filter by state, category (NTEE codes), revenue, assets
- 💾 Export results to CSV/JSON
- 🌐 Works 100% offline after initial data load
- 📱 Mobile-responsive design
- 🚀 Fast SQLite full-text search
- 💰 **Completely FREE** - no paid services required

## 🛠️ Technology Stack (All Free)

- **Backend**: Python FastAPI
- **Database**: SQLite (built into Python)
- **Frontend**: Pure HTML/JavaScript (no build process)
- **Search**: SQLite FTS5 (built-in full-text search)
- **Hosting**: Can run on any computer or free cloud services

## 📦 Quick Start (Local Development)

### Prerequisites

- Python 3.8 or higher ([Download Python](https://www.python.org/downloads/))
- 10GB free disk space (for IRS data)
- Any modern web browser

### Option 1: Automated Setup (Recommended)

```bash
# 1. Clone or download this repository
git clone https://github.com/your-org/nonprofit-platform.git
cd nonprofit-platform

# 2. Run the setup script
python scripts/setup.py

# 3. Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Start the application
uvicorn app.main:app --reload

# 5. Open browser
# Visit http://localhost:8000
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the application
uvicorn app.main:app --reload

# 5. Open http://localhost:8000
```

## 📊 Loading IRS Data

The platform needs IRS nonprofit data to function. You have two options:

### Option 1: Automatic Download (Recommended)
1. Start the application
2. Visit http://localhost:8000
3. Click "Import Data" or go to http://localhost:8000/api/import/start
4. Wait 10-30 minutes for download and processing

### Option 2: Manual Download
1. Download EO BMF files from https://www.irs.gov/charities-non-profits
2. Place CSV files in the `data/raw` directory
3. The system will process them on next startup

## 🚀 Deployment to Company Domain

### Step 1: Prepare for Production

1. Copy `.env.production` to `.env`
2. Update the production settings:
```bash
# Edit .env file
ENV=production
APP_URL=https://your-domain.org
SECRET_KEY=your-generated-secret-key
```

3. Generate a secure secret key:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 2: Deployment Options

#### Option A: Deploy to Your Company Server

If your company has a Linux server:

```bash
# 1. Copy files to server
scp -r nonprofit-platform/ user@your-server:/var/www/

# 2. SSH into server
ssh user@your-server

# 3. Install Python and dependencies
cd /var/www/nonprofit-platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Run with systemd (recommended) or screen
screen -S nonprofit
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Configure nginx/apache to proxy to port 8000
```

#### Option B: Deploy to Free Cloud Services

**Render.com (Recommended for NGOs)**
1. Create account at https://render.com
2. Connect your GitHub repository
3. Create new Web Service
4. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Vercel (Frontend) + Railway (Backend)**
1. Deploy frontend to Vercel
2. Deploy backend to Railway
3. Update frontend API URL to Railway endpoint

#### Option C: Shared Hosting (If You Have It)

Many NGOs have shared hosting. If yours supports Python:

1. Upload files via FTP
2. Use cPanel's Python selector
3. Create Python app pointing to `app/main.py`
4. Set up subdomain like `data.your-ngo.org`

### Step 3: Domain Configuration

Point your domain/subdomain to the deployment:

1. Add A record or CNAME in your DNS settings
2. Enable HTTPS (use Cloudflare for free SSL)
3. Update CORS origins in `.env`

## 📂 Project Structure

```
nonprofit-platform/
├── app/
│   ├── main.py          # FastAPI application
│   ├── database.py      # Database operations
│   ├── irs_processor.py # IRS data processing
│   └── config.py        # Configuration
├── static/
│   └── index.html       # Frontend interface
├── data/                # Data storage (auto-created)
├── scripts/
│   └── setup.py         # Setup script
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
└── nonprofits.db        # SQLite database (auto-created)
```

## 🔧 Configuration

All configuration is done via environment variables in `.env`:

- `ENV`: development or production
- `APP_URL`: Your application URL
- `DATABASE_URL`: Database connection (SQLite by default)
- `SECRET_KEY`: Secret key for security

## 🌍 Free Hosting Options

| Service | What It Provides | Limits | Good For |
|---------|-----------------|---------|----------|
| GitHub Pages | Static hosting | 100GB bandwidth/month | Frontend only |
| Vercel | Frontend + Serverless | 100GB bandwidth/month | Full app |
| Render | Full hosting + database | Free tier with limits | Complete solution |
| Railway | Full hosting | $5 credit/month | Testing |
| PythonAnywhere | Python hosting | 1 web app | Simple deployment |
| Replit | Online IDE + hosting | Always-on with limits | Development |

## 📈 Performance

With SQLite and proper indexing:
- Search 2M+ organizations in <100ms
- Handle 50+ concurrent users
- Run on 2GB RAM
- Work completely offline

## 🔒 Security Notes

For production deployment:
1. Always change the SECRET_KEY
2. Use HTTPS (free with Cloudflare)
3. Limit CORS origins
4. Regular backups of SQLite database
5. Consider rate limiting for public APIs

## 🤝 Contributing

This is open source! Feel free to:
- Report issues
- Suggest features
- Submit pull requests
- Fork for your own NGO

## 📝 License

MIT License - Use freely for any purpose

## 💡 Tips for NGOs

1. **Start Local**: Test everything locally first
2. **Use Free Tiers**: Many cloud services offer free tiers
3. **Share Resources**: Partner with other NGOs to share hosting
4. **Apply for Credits**: Many cloud providers offer nonprofit credits
5. **Use Cloudflare**: Free CDN and security

## 🆘 Support

- **Documentation**: See `/docs` folder
- **Issues**: Open a GitHub issue
- **Community**: Join our Discord
- **Email**: support@your-ngo.org

## 🎯 Roadmap

- [ ] Add data visualization charts
- [ ] Implement donation tracking
- [ ] Add grant opportunity matching
- [ ] Create mobile app (PWA)
- [ ] Add multi-language support

## 🙏 Acknowledgments

- IRS for providing public nonprofit data
- Open source community for free tools
- All NGOs working to make the world better

---

**Built with ❤️ for NGOs with zero budget**

*No credit card required. No trial period. Just free.*
