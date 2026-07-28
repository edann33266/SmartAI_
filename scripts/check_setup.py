"""
Quick setup checker for SalesAI
Run this to verify your configuration before starting the app.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def check_setup():
    print("=" * 60)
    print("SalesAI Setup Checker")
    print("=" * 60)
    print()
    
    issues = []
    warnings = []
    
    # Check 1: Gemini API Key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "YOUR_GEMINI_API_KEY_HERE":
        issues.append("❌ GEMINI_API_KEY not set in .env file")
        print("❌ Gemini API Key: NOT CONFIGURED")
        print("   → Get your key at: https://aistudio.google.com/app/apikey")
        print("   → Add it to .env file: GEMINI_API_KEY=your_key_here")
    else:
        print("✅ Gemini API Key: CONFIGURED")
    
    print()
    
    # Check 2: SMTP Configuration
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    dry_run = os.getenv("DRY_RUN", "true").lower()
    
    if dry_run == "true":
        print("⚠️  Email Sending: DRY RUN MODE (emails won't actually send)")
        warnings.append("Emails will only print to console")
    else:
        if smtp_user and smtp_pass:
            print("✅ Email Sending: CONFIGURED (will send real emails)")
        else:
            issues.append("❌ SMTP credentials missing but DRY_RUN=false")
            print("❌ Email Sending: SMTP credentials missing")
    
    print()
    
    # Check 3: Customer Data
    csv_path = Path("data/customers.csv")
    if csv_path.exists():
        import csv
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            count = sum(1 for _ in reader)
        print(f"✅ Customer Data: {count} leads found")
    else:
        issues.append("❌ data/customers.csv not found")
        print("❌ Customer Data: NOT FOUND")
    
    print()
    
    # Check 4: Dependencies
    try:
        import google.genai
        print("✅ Dependencies: google-genai installed")
    except ImportError:
        issues.append("❌ google-genai not installed")
        print("❌ Dependencies: google-genai missing")
        print("   → Run: pip install -r requirements.txt")
    
    print()
    print("=" * 60)
    
    if issues:
        print("\n🔴 ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print("\nPlease fix these issues before running the app.")
        return False
    elif warnings:
        print("\n🟡 WARNINGS:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
        print("\nYou can proceed, but review the warnings above.")
        return True
    else:
        print("\n🟢 ALL CHECKS PASSED!")
        print("\nYou're ready to run:")
        print("  • Command line: python main.py")
        print("  • Web interface: python api.py")
        return True

if __name__ == "__main__":
    success = check_setup()
    exit(0 if success else 1)
