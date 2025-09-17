#!/bin/bash
# Quick Deploy Script - Automates deployment preparation

echo "🚀 NONPROFIT PLATFORM - QUICK DEPLOY"
echo "===================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first:"
    echo "   Mac: brew install git"
    echo "   Ubuntu/Debian: sudo apt-get install git"
    echo "   Windows: Download from https://git-scm.com"
    exit 1
fi

echo "This script will help you deploy your nonprofit platform."
echo "Choose your deployment method:"
echo ""
echo "1) Deploy to Render.com (FREE - Recommended)"
echo "2) Prepare files for manual deployment"
echo "3) Create Docker deployment"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "📦 Preparing for Render.com deployment..."
        echo ""
        
        # Check if GitHub remote exists
        if git remote -v | grep -q origin; then
            echo "✅ Git repository already configured"
        else
            echo "Setting up Git repository..."
            git init
            
            echo "📝 Please enter your GitHub username:"
            read github_username
            
            echo "📝 Please enter your repository name (e.g., nonprofit-platform):"
            read repo_name
            
            git remote add origin "https://github.com/$github_username/$repo_name.git"
            echo "✅ Git remote added"
        fi
        
        # Add render.yaml if not exists
        if [ ! -f "render.yaml" ]; then
            echo "Creating render.yaml configuration..."
            cat > render.yaml << 'EOL'
services:
  - type: web
    name: nonprofit-platform
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
EOL
            echo "✅ render.yaml created"
        fi
        
        # Commit all changes
        echo "Preparing to push to GitHub..."
        git add .
        git commit -m "Deploy to Render" 2>/dev/null || echo "No changes to commit"
        
        echo ""
        echo "🎯 NEXT STEPS:"
        echo "=============="
        echo ""
        echo "1. Create a GitHub repository:"
        echo "   Go to: https://github.com/new"
        echo "   Name: $repo_name"
        echo "   Make it PRIVATE"
        echo ""
        echo "2. Push your code:"
        echo "   git push -u origin main"
        echo ""
        echo "3. Deploy on Render:"
        echo "   a. Go to https://render.com"
        echo "   b. Sign up (FREE)"
        echo "   c. Click 'New +' → 'Web Service'"
        echo "   d. Connect GitHub and select your repo"
        echo "   e. Click 'Create Web Service'"
        echo ""
        echo "Your app will be live at: https://[your-app-name].onrender.com"
        echo ""
        ;;
        
    2)
        echo ""
        echo "📦 Creating deployment package..."
        
        # Create deployment directory
        rm -rf deployment 2>/dev/null
        mkdir -p deployment
        
        # Copy necessary files
        cp -r app deployment/
        cp -r static deployment/
        cp requirements.txt deployment/
        cp .env.production deployment/.env
        
        # Create deployment instructions
        cat > deployment/DEPLOY_INSTRUCTIONS.txt << 'EOL'
DEPLOYMENT INSTRUCTIONS
======================

1. Upload all files to your server via FTP or SSH
2. SSH into your server
3. Run these commands:

   cd /path/to/deployment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000

4. Configure your web server (nginx/Apache) to proxy to port 8000
5. Set up SSL certificate for HTTPS

For detailed instructions, see DEPLOYMENT_GUIDE.md
EOL
        
        # Create zip file
        zip -r deployment.zip deployment/ > /dev/null 2>&1
        
        echo "✅ Deployment package created: deployment.zip"
        echo ""
        echo "Upload deployment.zip to your server and extract it."
        ;;
        
    3)
        echo ""
        echo "🐳 Creating Docker deployment..."
        
        # Create Dockerfile
        cat > Dockerfile << 'EOL'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOL
        
        # Create docker-compose.yml
        cat > docker-compose.yml << 'EOL'
version: '3.8'
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
EOL
        
        echo "✅ Docker files created"
        echo ""
        echo "To deploy with Docker:"
        echo "  docker-compose up -d"
        echo ""
        ;;
        
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo "✨ Deployment preparation complete!"
echo ""
echo "For detailed instructions, see DEPLOYMENT_GUIDE.md"
