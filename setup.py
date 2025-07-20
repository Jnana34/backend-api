#!/usr/bin/env python3
"""
Setup script for ShopFusion Django backend
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    print("🚀 Setting up ShopFusion Django Backend")
    
    # Check if .env exists
    env_file = Path('.env')
    if not env_file.exists():
        print("\n📝 Creating .env file from .env.example...")
        try:
            with open('.env.example', 'r') as example:
                content = example.read()
            with open('.env', 'w') as env:
                env.write(content)
            print("✅ .env file created. Please update it with your settings.")
        except FileNotFoundError:
            print("❌ .env.example not found")
            return False
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Check database connection
    if not run_command("python manage.py check_db", "Checking database connection"):
        print("\n🔧 Database connection failed. Please:")
        print("1. Ensure PostgreSQL is running: sudo service postgresql start")
        print("2. Create database: createdb -p 5433 -U postgres shopfusion_db")
        print("3. Update .env file with correct credentials")
        return False
    
    # Make migrations
    apps = ['accounts', 'products', 'orders', 'core']
    for app in apps:
        if not run_command(f"python manage.py makemigrations {app}", f"Making migrations for {app}"):
            return False
    
    # Run migrations
    if not run_command("python manage.py migrate", "Running database migrations"):
        return False
    
    # Verify setup
    if not run_command("python manage.py check_db", "Verifying database setup"):
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Run the server: python manage.py runserver")
    print("3. Visit http://localhost:8000/admin/ to access admin panel")
    print("4. API will be available at http://localhost:8000/api/")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
