"""
Quick start script for SalesAI
This will check your setup and guide you through getting started.
"""
import os
import sys
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def print_banner():
    print("\n" + "=" * 60)
    print("  ⚡ SalesAI - AI-Powered Sales Outreach Platform")
    print("=" * 60 + "\n")

def check_gemini_key():
    """Check if Gemini API key is configured."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "YOUR_GEMINI_API_KEY_HERE" or gemini_key == "your_gemini_api_key_here":
        print("❌ Gemini API Key not configured!\n")
        print("To get started:")
        print("1. Visit: https://aistudio.google.com/app/apikey")
        print("2. Click 'Create API Key'")
        print("3. Copy your API key")
        print("4. Open .env file and set: GEMINI_API_KEY=your_key_here")
        print("\nWould you like to open the API key page now? (y/n): ", end="")
        
        response = input().strip().lower()
        if response == 'y':
            webbrowser.open("https://aistudio.google.com/app/apikey")
            print("\n✓ Opened browser. Come back after you've added your key to .env")
        
        return False
    return True

def check_dependencies():
    """Check if required packages are installed."""
    try:
        import google.genai
        import fastapi
        import pandas
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}\n")
        print("Please run: pip install -r requirements.txt")
        return False

def main():
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Gemini API key
    if not check_gemini_key():
        sys.exit(1)
    
    print("\n✅ Setup looks good!\n")
    print("Choose how to run SalesAI:\n")
    print("1. Web Interface (Recommended) - Beautiful UI with live preview")
    print("2. Command Line - Simple script execution")
    print("3. Run setup checker only")
    print("4. Exit")
    print("\nEnter your choice (1-4): ", end="")
    
    choice = input().strip()
    
    if choice == "1":
        print("\n🚀 Starting Web Interface...\n")
        print("Instructions:")
        print("1. Keep this terminal open (backend server)")
        print("2. Open frontend/index.html in your browser")
        print("3. Or visit: http://localhost:8000/customers to test API")
        print("\nStarting backend server on http://localhost:8000...")
        print("Press Ctrl+C to stop\n")
        print("-" * 60 + "\n")
        
        # Start the API server
        import uvicorn
        from api import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    elif choice == "2":
        print("\n🚀 Running Command Line Interface...\n")
        print("-" * 60 + "\n")
        from main import main as run_main
        run_main()
        
    elif choice == "3":
        print("\n🔍 Running setup checker...\n")
        from check_setup import check_setup
        check_setup()
        
    else:
        print("\n👋 Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
