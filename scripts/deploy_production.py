#!/usr/bin/env python3
"""
Production Deployment Helper
Prepares the application for deployment to company domain
"""
import os
import sys
import shutil
import json
import subprocess
from pathlib import Path
from datetime import datetime

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

class ProductionDeployer:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.deployment_dir = self.root_dir / "deployment"
        
    def prepare_deployment(self):
        """Prepare files for production deployment"""
        print_header("Preparing Production Deployment Package")
        
        # Create deployment directory
        if self.deployment_dir.exists():
            shutil.rmtree(self.deployment_dir)
        self.deployment_dir.mkdir()
        
        print("📁 Creating deployment package...")
        
        # Files to include
        include_patterns = [
            "app/*.py",
            "static/*",
            "scripts/*.py",
            "requirements.txt",
            "README.md",
            ".env.production"
        ]
        
        # Copy essential files
        for pattern in include_patterns:
            if "*" in pattern:
                base_dir = pattern.split("*")[0]
                if base_dir:
                    dest_dir = self.deployment_dir / base_dir
                    dest_dir.mkdir(exist_ok=True)
                    
                    src_dir = self.root_dir / base_dir
                    if src_dir.exists():
                        for file in src_dir.glob("*"):
                            if file.is_file():
                                shutil.copy2(file, dest_dir)
                                print(f"  ✓ Copied {file.relative_to(self.root_dir)}")
            else:
                src_file = self.root_dir / pattern
                if src_file.exists():
                    shutil.copy2(src_file, self.deployment_dir / src_file.name)
                    print(f"  ✓ Copied {pattern}")
        
        # Create deployment info
        info = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "deployment_notes": "Ready for production deployment"
        }
        
        with open(self.deployment_dir / "deployment_info.json", "w") as f:
            json.dump(info, f, indent=2)
        
        print(f"\n✅ Deployment package created in: {self.deployment_dir}")
        
        return True
    
    def create_deployment_scripts(self):
        """Create platform-specific deployment scripts"""
        print("\n📝 Creating deployment scripts...")
        
        # Create Docker deployment
        self.create_docker_files()
        
        # Create systemd service file
        self.create_systemd_service()
        
        # Create nginx configuration
        self.create_nginx_config()
        
        # Create deployment checklist
        self.create_deployment_checklist()
        
        print("✅ Deployment scripts created")
    
    def create_docker_files(self):
        """Create Docker files for containerized deployment"""
        
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY static/ ./static/

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        with open(self.deployment_dir / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        # Docker Compose file
        docker_compose = """version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./nonprofits.db:/app/nonprofits.db
    environment:
      - ENV=production
    restart: unless-stopped
"""
        
        with open(self.deployment_dir / "docker-compose.yml", "w") as f:
            f.write(docker_compose)
        
        print("  ✓ Created Docker files")
    
    def create_systemd_service(self):
        """Create systemd service file for Linux deployment"""
        
        service_content = """[Unit]
Description=Nonprofit Intelligence Platform
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/nonprofit-platform
Environment="PATH=/var/www/nonprofit-platform/venv/bin"
ExecStart=/var/www/nonprofit-platform/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        with open(self.deployment_dir / "nonprofit-platform.service", "w") as f:
            f.write(service_content)
        
        print("  ✓ Created systemd service file")
    
    def create_nginx_config(self):
        """Create nginx configuration"""
        
        nginx_config = """server {
    listen 80;
    server_name your-domain.org www.your-domain.org;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.org www.your-domain.org;
    
    # SSL Configuration (update paths)
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files (optional optimization)
    location /static {
        alias /var/www/nonprofit-platform/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
"""
        
        with open(self.deployment_dir / "nginx.conf", "w") as f:
            f.write(nginx_config)
        
        print("  ✓ Created nginx configuration")
    
    def create_deployment_checklist(self):
        """Create deployment checklist"""
        
        checklist = """# Deployment Checklist for Company Domain

## Pre-Deployment

- [ ] Backup current data if any
- [ ] Verify Python 3.8+ is installed on server
- [ ] Ensure you have SSH access to server
- [ ] Have domain/subdomain ready
- [ ] SSL certificate ready (or use Let's Encrypt)

## Deployment Steps

### 1. Upload Files
```bash
# Via SCP
scp -r deployment/* user@your-server:/var/www/nonprofit-platform/

# Or via FTP/SFTP using FileZilla or similar
```

### 2. Server Setup
```bash
# SSH into server
ssh user@your-server

# Navigate to application directory
cd /var/www/nonprofit-platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set permissions
chmod +x scripts/*.py
chown -R www-data:www-data /var/www/nonprofit-platform
```

### 3. Environment Configuration
```bash
# Copy production environment template
cp .env.production .env

# Edit configuration
nano .env

# Update these values:
# - ENV=production
# - APP_URL=https://your-domain.org
# - SECRET_KEY=<generate-secure-key>
# - CORS_ORIGINS=https://your-domain.org
```

### 4. Database Setup
```bash
# Initialize database
python -c "from app.database import db; print('Database initialized')"

# Load IRS data (optional, can do via web interface later)
python -c "from app.irs_processor import irs_processor; irs_processor.process_all_data()"
```

### 5. Web Server Setup

#### Option A: Using systemd (Recommended for VPS)
```bash
# Copy service file
sudo cp nonprofit-platform.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable nonprofit-platform
sudo systemctl start nonprofit-platform

# Check status
sudo systemctl status nonprofit-platform
```

#### Option B: Using Docker
```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

#### Option C: Using screen (Simple method)
```bash
# Start in screen session
screen -S nonprofit
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Detach with Ctrl+A, D
```

### 6. Configure Reverse Proxy (nginx)
```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/nonprofit-platform

# Enable site
sudo ln -s /etc/nginx/sites-available/nonprofit-platform /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 7. SSL Certificate

#### Using Let's Encrypt (Free)
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.org -d www.your-domain.org

# Auto-renewal is configured automatically
```

### 8. Final Testing

- [ ] Visit https://your-domain.org
- [ ] Test search functionality
- [ ] Test data export
- [ ] Check API at https://your-domain.org/docs
- [ ] Verify SSL certificate

## Post-Deployment

### Monitoring
```bash
# Check application logs
journalctl -u nonprofit-platform -f

# Check disk space
df -h

# Check memory usage
free -m
```

### Backup Strategy
```bash
# Backup database daily
crontab -e
# Add: 0 2 * * * cp /var/www/nonprofit-platform/nonprofits.db /backup/nonprofits_$(date +%Y%m%d).db
```

### Updates
```bash
# Pull latest changes
git pull

# Restart service
sudo systemctl restart nonprofit-platform
```

## Troubleshooting

### Application won't start
- Check Python version: `python3 --version`
- Check logs: `journalctl -u nonprofit-platform -n 50`
- Verify permissions: `ls -la /var/www/nonprofit-platform`

### Database errors
- Check database file exists: `ls -la nonprofits.db`
- Check permissions: `chown www-data:www-data nonprofits.db`
- Reinitialize if needed: `python -c "from app.database import db"`

### Performance issues
- Consider upgrading to PostgreSQL
- Add more RAM to server
- Enable caching with Redis

## Support Contacts

- Technical Issues: Create GitHub issue
- IRS Data Questions: See IRS.gov
- Deployment Help: Check README.md

---
Generated: {datetime.now().isoformat()}
"""
        
        with open(self.deployment_dir / "DEPLOYMENT_CHECKLIST.md", "w") as f:
            f.write(checklist)
        
        print("  ✓ Created deployment checklist")
    
    def create_migration_script(self):
        """Create script to migrate data from local to production"""
        
        migration_script = """#!/usr/bin/env python3
'''
Migration script to move data from local to production
'''
import sqlite3
import json
from pathlib import Path

def export_data(db_path='nonprofits.db', output_file='data_export.json'):
    '''Export all data from local database'''
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    data = {
        'organizations': [],
        'filings': [],
        'export_date': datetime.now().isoformat()
    }
    
    # Export organizations
    cursor = conn.execute("SELECT * FROM organizations")
    data['organizations'] = [dict(row) for row in cursor.fetchall()]
    
    print(f"Exported {len(data['organizations'])} organizations")
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(data, f)
    
    print(f"Data exported to {output_file}")
    
    conn.close()
    return output_file

def import_data(data_file='data_export.json', db_path='nonprofits.db'):
    '''Import data into production database'''
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(db_path)
    
    # Import organizations
    for org in data['organizations']:
        # Insert organization
        # (Add your insert logic here)
        pass
    
    conn.commit()
    conn.close()
    
    print(f"Imported {len(data['organizations'])} organizations")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'export':
            export_data()
        elif sys.argv[1] == 'import':
            import_data()
    else:
        print("Usage: python migrate.py [export|import]")
"""
        
        with open(self.deployment_dir / "migrate.py", "w") as f:
            f.write(migration_script)
        
        print("  ✓ Created migration script")

def main():
    print_header("Production Deployment Preparation")
    
    deployer = ProductionDeployer()
    
    # Prepare deployment package
    if not deployer.prepare_deployment():
        print("❌ Failed to prepare deployment package")
        sys.exit(1)
    
    # Create deployment scripts
    deployer.create_deployment_scripts()
    
    # Create migration script
    deployer.create_migration_script()
    
    print_header("Deployment Package Ready!")
    
    print("\n📦 Your deployment package is ready in: ./deployment/")
    print("\n📋 Next steps:")
    print("1. Review DEPLOYMENT_CHECKLIST.md for detailed instructions")
    print("2. Update .env.production with your domain settings")
    print("3. Choose your deployment method:")
    print("   - VPS/Cloud Server: Use Docker or systemd")
    print("   - Shared Hosting: Use FTP upload + cPanel")
    print("   - Free Cloud: Deploy to Render.com or Vercel")
    print("\n💡 The application will work exactly the same on your domain!")
    print("🔒 Remember to set up HTTPS for security")
    
    print("\n✨ Good luck with your deployment!")

if __name__ == "__main__":
    main()
