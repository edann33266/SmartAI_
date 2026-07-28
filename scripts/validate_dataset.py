"""
Script to validate and preview the sales_leads_dataset.csv
"""
import csv
from pathlib import Path
from collections import Counter

def validate_dataset():
    print("=" * 70)
    print("Sales Leads Dataset Validation")
    print("=" * 70)
    print()
    
    dataset_path = Path("data/sales_leads_dataset.csv")
    
    if not dataset_path.exists():
        print(f"❌ Dataset not found at: {dataset_path}")
        print("   Please ensure the file exists in the data/ folder")
        return False
    
    print(f"✓ Dataset found: {dataset_path}")
    print()
    
    # Read and validate
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                print("❌ Dataset is empty!")
                return False
            
            print(f"✓ Total leads: {len(rows)}")
            print()
            
            # Check required columns
            required_columns = [
                'name', 'email', 'company', 'industry', 'lead_score',
                'contact_days_ago', 'annual_revenue', 'current_tool', 'region'
            ]
            
            actual_columns = list(rows[0].keys())
            print("Columns found:")
            for col in actual_columns:
                status = "✓" if col in required_columns else "⚠️"
                print(f"  {status} {col}")
            
            missing = set(required_columns) - set(actual_columns)
            if missing:
                print(f"\n⚠️  Missing columns: {', '.join(missing)}")
            print()
            
            # Statistics
            print("Dataset Statistics:")
            print("-" * 70)
            
            # Lead scores
            scores = [int(row['lead_score']) for row in rows if row['lead_score'].isdigit()]
            if scores:
                print(f"  Lead Scores:")
                print(f"    • Average: {sum(scores) / len(scores):.1f}")
                print(f"    • Min: {min(scores)}")
                print(f"    • Max: {max(scores)}")
                print(f"    • High quality (≥80): {len([s for s in scores if s >= 80])}")
            
            # Industries
            industries = Counter(row['industry'] for row in rows)
            print(f"\n  Industries ({len(industries)} unique):")
            for industry, count in industries.most_common(5):
                print(f"    • {industry}: {count}")
            
            # Regions
            regions = Counter(row['region'] for row in rows)
            print(f"\n  Regions ({len(regions)} unique):")
            for region, count in regions.most_common():
                print(f"    • {region}: {count}")
            
            # Current tools
            tools = Counter(row['current_tool'] for row in rows)
            print(f"\n  Current Tools ({len(tools)} unique):")
            for tool, count in tools.most_common(5):
                print(f"    • {tool}: {count}")
            
            print()
            print("-" * 70)
            
            # Sample leads
            print("\nSample Leads (first 5):")
            print("-" * 70)
            for i, row in enumerate(rows[:5], 1):
                print(f"\n{i}. {row['name']}")
                print(f"   Company: {row['company']}")
                print(f"   Email: {row['email']}")
                print(f"   Industry: {row['industry']}")
                print(f"   Lead Score: {row['lead_score']}")
                print(f"   Last Contact: {row['contact_days_ago']} days ago")
                print(f"   Revenue: ${int(row['annual_revenue']):,}")
                print(f"   Current Tool: {row['current_tool']}")
                print(f"   Region: {row['region']}")
            
            print()
            print("=" * 70)
            print("✅ Dataset validation complete!")
            print()
            print("Next steps:")
            print("  1. The system will automatically use this dataset")
            print("  2. Run: python main.py (CLI mode)")
            print("  3. Or run: python api.py (Web interface)")
            print()
            
            return True
            
    except Exception as e:
        print(f"❌ Error reading dataset: {e}")
        return False


if __name__ == "__main__":
    validate_dataset()
