# 🚀 DEPLOYMENT GUIDE - Step by Step

## 📍 Current Status
✅ Your app is ready for deployment
✅ All files are prepared
✅ Zero-cost options available

---

## 🎯 QUICK DEPLOYMENT (15 Minutes)

### Option 1: Deploy to Render.com (FREE - RECOMMENDED)

#### Step 1: Create GitHub Repository

1. Go to https://github.com (create free account if needed)
2. Click "New Repository"
3. Name it: `nonprofit-platform`
4. Make it PRIVATE (for security)
5. Don't initialize with README

#### Step 2: Upload Your Code to GitHub

```bash
# In your nonprofit-platform folder
cd "/Users/shivbhumie/Desktop/Ai Project /Claude/Trial/nonprofit-platform"

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Add your GitHub repository (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/nonprofit-platform.git

# Push code
git push -u origin main
```

#### Step 3: Deploy to Render

1. Go to https://render.com
2. Sign up for FREE account (use GitHub login)
3. Click "New +" → "Web Service"
4. Connect your GitHub account
5. Select your `nonprofit-platform` repository
6. Configure:
   - **Name**: your-nonprofit-platform
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Click "Create Web Service"

#### Step 4: Set Environment Variables

In Render dashboard, go to "Environment":

```
ENV=production
SECRET_KEY=click-generate
APP_URL=https://your-app.onrender.com
```

#### Step 5: Create Free Database

1. In Render, click "New +" → "PostgreSQL"
2. Name: nonprofit-db
3. Choose "Free" plan
4. Click "Create Database"
5. Copy the connection string

#### Step 6: Connect Database

1. Go back to your web service
2. Add environment variable:
   - Key: `DATABASE_URL`
   - Value: (paste the connection string)

#### Step 7: Access Your App

Your app will be available at:
```
https://your-app-name.onrender.com
```

---

### Option 2: Deploy to Your Company's Existing Hosting

If your NGO already has web hosting with cPanel:

#### Step 1: Prepare Files

```bash
cd "/Users/shivbhumie/Desktop/Ai Project /Claude/Trial/nonprofit-platform"

# Create deployment package
python scripts/deploy_production.py
```

#### Step 2: Upload via FTP

1. Use FileZilla or cPanel File Manager
2. Upload the `deployment` folder contents to:
   - `public_html/nonprofit/` (or any subdirectory)

#### Step 3: Setup Python in cPanel

1. Login to cPanel
2. Find "Setup Python App"
3. Click "Create Application"
4. Configure:
   - Python version: 3.8 or higher
   - Application root: /home/username/public_html/nonprofit
   - Application URL: nonprofit
   - Application startup file: app/main.py
5. Click "Create"

#### Step 4: Install Dependencies

In cPanel Python app:
1. Click "Run pip install"
2. Enter: `-r requirements.txt`
3. Click "Execute"

#### Step 5: Set Environment Variables

In cPanel Python app, add:
```
ENV=production
SECRET_KEY=generate-a-random-string
APP_URL=https://your-domain.org/nonprofit
```

#### Step 6: Restart Application

Click "Restart" in cPanel Python app

---

### Option 3: Deploy to VPS/Cloud Server

If you have access to a Linux server:

#### Step 1: Connect to Server

```bash
ssh username@your-server.com
```

#### Step 2: Install Python and Dependencies

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install nginx (web server)
sudo apt install nginx -y
```

#### Step 3: Upload Application

```bash
# On your local machine
cd "/Users/shivbhumie/Desktop/Ai Project /Claude/Trial/nonprofit-platform"

# Create archive
tar -czf nonprofit-platform.tar.gz .

# Upload to server
scp nonprofit-platform.tar.gz username@your-server:/home/username/
```

#### Step 4: Setup Application on Server

```bash
# On the server
cd /home/username
tar -xzf nonprofit-platform.tar.gz -C /var/www/nonprofit-platform/
cd /var/www/nonprofit-platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 5: Configure as Service

```bash
# Create service file
sudo nano /etc/systemd/system/nonprofit.service
```

Add this content:
```ini
[Unit]
Description=Nonprofit Platform
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/nonprofit-platform
Environment="PATH=/var/www/nonprofit-platform/venv/bin"
ExecStart=/var/www/nonprofit-platform/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### Step 6: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/nonprofit
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.org;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### Step 7: Enable and Start

```bash
# Enable nginx site
sudo ln -s /etc/nginx/sites-available/nonprofit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Start service
sudo systemctl enable nonprofit
sudo systemctl start nonprofit

# Check status
sudo systemctl status nonprofit
```

#### Step 8: Setup SSL (HTTPS)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get free SSL certificate
sudo certbot --nginx -d your-domain.org

# Auto-renewal is configured automatically
```

---

## 🌐 DOMAIN CONFIGURATION

### If Using Subdomain (data.your-ngo.org):

1. Login to your domain registrar (GoDaddy, Namecheap, etc.)
2. Go to DNS settings
3. Add A record:
   - Type: A
   - Host: data
   - Points to: Your server IP or Render IP
   - TTL: 3600

### If Using Main Domain (your-ngo.org):

1. Update A record:
   - Type: A
   - Host: @
   - Points to: Your server IP
   - TTL: 3600

---

## 📱 POST-DEPLOYMENT CHECKLIST

### Immediately After Deployment:

- [ ] Visit your URL
- [ ] Test search functionality
- [ ] Import IRS data (visit /api/import/start)
- [ ] Test data export
- [ ] Check mobile responsiveness

### Security Steps:

- [ ] Change SECRET_KEY in production
- [ ] Enable HTTPS (automatic on Render)
- [ ] Set strong passwords
- [ ] Regular backups

---

## 🆘 TROUBLESHOOTING

### Application Not Loading?

```bash
# Check logs (Render)
# Go to Render dashboard → Logs

# Check logs (VPS)
sudo journalctl -u nonprofit -f
```

### Database Connection Failed?

1. Verify DATABASE_URL is correct
2. For SQLite, ensure file permissions:
```bash
chmod 666 nonprofits.db
```

### Import Not Working?

1. Check internet connection
2. Verify IRS URLs are accessible
3. Check disk space

---

## 💰 COST COMPARISON

| Method | Monthly Cost | Pros | Cons |
|--------|-------------|------|------|
| **Render.com** | $0 | Automatic, includes database | Sleeps after 15 min inactivity |
| **Your Hosting** | $0 (if existing) | Full control | Need technical knowledge |
| **VPS** | $5-10 | Full control, always on | Requires maintenance |
| **GitHub Pages** | $0 | Simple | Frontend only |

---

## 🎯 RECOMMENDED APPROACH

1. **Start with Render.com** (FREE)
   - Deploy in 15 minutes
   - Test with real users
   - No commitment

2. **Later: Move to VPS if needed**
   - When you need always-on service
   - When you have more traffic
   - When you have budget

---

## 📞 QUICK COMMANDS REFERENCE

### Local Development:
```bash
cd "/Users/shivbhumie/Desktop/Ai Project /Claude/Trial/nonprofit-platform"
./start.sh
```

### Deploy to Render:
```bash
git add .
git commit -m "Update"
git push origin main
# Render auto-deploys
```

### Check Status:
```bash
# Local
curl http://localhost:8000/api/health

# Production
curl https://your-app.onrender.com/api/health
```

---

## 🎉 SUCCESS INDICATORS

Your deployment is successful when:

✅ Homepage loads at your URL
✅ Search returns results
✅ Can export data
✅ API docs work (/docs)
✅ No errors in logs

---

## 🚨 IMPORTANT NOTES

1. **Render Free Tier**: App sleeps after 15 minutes of inactivity. First request takes 30 seconds to wake up.

2. **Data Persistence**: 
   - Render: Data persists in PostgreSQL
   - VPS: Data persists in SQLite file
   - Always backup regularly

3. **Scaling**: Start free, upgrade only when needed

4. **Support**: 
   - Render: support@render.com
   - Community: GitHub Issues

---

## 📋 NEXT STEPS

After successful deployment:

1. **Load IRS Data**
   ```
   Visit: https://your-app.onrender.com/api/import/start
   ```

2. **Share with Team**
   - Send URL to colleagues
   - Get feedback
   - Train users

3. **Customize** (optional)
   - Update logo/colors in index.html
   - Add your NGO branding
   - Modify search filters

4. **Monitor Usage**
   - Check Render dashboard
   - Monitor performance
   - Plan scaling if needed

---

**Need help? Start with Render.com - it's the easiest!** 🚀
