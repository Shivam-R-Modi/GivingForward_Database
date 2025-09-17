#!/usr/bin/env python3
"""
Setup script for Nonprofit Intelligence Platform
Run this to initialize everything
"""
import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50)

def check_python():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. You have {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor} detected")
    return True

def create_venv():
    """Create virtual environment"""
    print("\nCreating virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling dependencies...")
    
    # Determine pip path based on OS
    if sys.platform == "win32":
        pip_path = Path("venv/Scripts/pip")
    else:
        pip_path = Path("venv/bin/pip")
    
    if not pip_path.exists():
        print("❌ pip not found in virtual environment")
        return False
    
    try:
        # Upgrade pip first
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def initialize_database():
    """Initialize the database"""
    print("\nInitializing database...")
    
    # Python path in venv
    if sys.platform == "win32":
        python_path = Path("venv/Scripts/python")
    else:
        python_path = Path("venv/bin/python")
    
    try:
        # Import and run database initialization
        subprocess.run([
            str(python_path), "-c",
            "from app.database import db; print('Database initialized!')"
        ], check=True)
        print("✅ Database initialized")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def main():
    print_header("Nonprofit Intelligence Platform Setup")
    
    # Check Python version
    if not check_python():
        print("\nPlease install Python 3.8 or higher")
        sys.exit(1)
    
    # Create virtual environment
    if not create_venv():
        print("\nSetup failed at virtual environment creation")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\nSetup failed at dependency installation")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("\nSetup failed at database initialization")
        sys.exit(1)
    
    print_header("Setup Complete!")
    
    print("\n📋 Next steps:")
    print("\n1. Activate the virtual environment:")
    if sys.platform == "win32":
        print("   Windows: venv\\Scripts\\activate")
    else:
        print("   Mac/Linux: source venv/bin/activate")
    
    print("\n2. Start the application:")
    print("   uvicorn app.main:app --reload")
    
    print("\n3. Open your browser:")
    print("   http://localhost:8000")
    
    print("\n4. (Optional) Load IRS data:")
    print("   Visit http://localhost:8000/api/import/start")
    
    print("\n✨ Your nonprofit platform is ready to run locally!")
    print("💡 No costs, no cloud services needed!")

if __name__ == "__main__":
    main()
