"""
Script to train the ML lead scoring model.
Run this to create a trained model from historical data.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import (
    confusion_matrix, 
    classification_report, 
    roc_curve, 
    auc,
    precision_recall_curve,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)
from ml_lead_scorer import MLLeadScorer


# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def create_visualizations_folder():
    """Create folder for saving visualizations."""
    viz_folder = Path("visualizations")
    viz_folder.mkdir(exist_ok=True)
    return viz_folder


def create_sample_training_data():
    """
    Create sample training data for demonstration.
    In production, replace this with actual historical conversion data.
    """
    data = pd.DataFrame({
        'lead_score': [
            92, 85, 78, 95, 70, 88, 65, 90, 75, 82,
            68, 93, 77, 86, 72, 91, 80, 74, 89, 76,
            94, 71, 87, 79, 96, 73, 84, 81, 69, 83
        ],
        'last_contact_days_ago': [
            45, 30, 10, 60, 5, 35, 15, 50, 25, 40,
            8, 55, 20, 38, 12, 48, 28, 18, 42, 22,
            52, 14, 36, 24, 58, 16, 32, 26, 10, 34
        ],
        'annual_revenue': [
            1200000, 800000, 500000, 2000000, 300000, 1000000, 400000, 1800000, 600000, 900000,
            450000, 1900000, 550000, 950000, 350000, 1700000, 750000, 480000, 1100000, 580000,
            2100000, 380000, 920000, 650000, 2200000, 420000, 880000, 720000, 320000, 850000
        ],
        'industry': [
            'SaaS', 'Manufacturing', 'Retail', 'Technology', 'Retail', 'Finance', 'Manufacturing',
            'Technology', 'SaaS', 'Finance', 'Retail', 'SaaS', 'Manufacturing', 'Technology',
            'Retail', 'SaaS', 'Finance', 'Manufacturing', 'Technology', 'Retail',
            'SaaS', 'Manufacturing', 'Finance', 'Retail', 'Technology', 'Manufacturing',
            'SaaS', 'Finance', 'Retail', 'Technology'
        ],
        'region': [
            'North America', 'Europe', 'Asia', 'North America', 'Asia', 'Europe', 'Asia',
            'North America', 'Europe', 'North America', 'Asia', 'North America', 'Europe',
            'North America', 'Asia', 'North America', 'Europe', 'Asia', 'North America', 'Europe',
            'North America', 'Asia', 'Europe', 'Asia', 'North America', 'Europe', 'North America',
            'Europe', 'Asia', 'North America'
        ],
        'current_tool': [
            'Excel', 'None', 'Salesforce', 'HubSpot', 'None', 'Excel', 'None', 'Salesforce',
            'Excel', 'HubSpot', 'None', 'Excel', 'Salesforce', 'HubSpot', 'None', 'Excel',
            'Salesforce', 'None', 'HubSpot', 'Excel', 'Salesforce', 'None', 'HubSpot', 'Excel',
            'Salesforce', 'None', 'HubSpot', 'Excel', 'None', 'Salesforce'
        ],
        'converted': [
            # High score + good recency + high revenue = likely to convert
            1, 1, 0, 1, 0, 1, 0, 1, 0, 1,
            0, 1, 0, 1, 0, 1, 1, 0, 1, 0,
            1, 0, 1, 0, 1, 0, 1, 1, 0, 1
        ]
    })
    
    return data


def main():
    print("=" * 60)
    print("SalesAI ML Lead Scorer Training")
    print("=" * 60)
    print()
    
    # Create training data
    print("Creating training data...")
    training_data = create_sample_training_data()
    print(f"✓ Created {len(training_data)} training samples")
    print()
    
    # Show data summary
    print("Data Summary:")
    print(f"  • Converted leads: {training_data['converted'].sum()}")
    print(f"  • Not converted: {len(training_data) - training_data['converted'].sum()}")
    print(f"  • Conversion rate: {training_data['converted'].mean():.1%}")
    print()
    
    # Train model
    print("Training ML model...")
    print("-" * 60)
    scorer = MLLeadScorer()
    scorer.train_model(training_data)
    print("-" * 60)
    print()
    
    # Show feature importance
    print("Feature Importance:")
    for feature, importance in scorer.get_feature_importance().items():
        bar = "█" * int(importance * 50)
        print(f"  {feature:25s} {bar} {importance:.3f}")
    print()
    
    # Test predictions
    print("Testing predictions on sample data...")
    print("-" * 60)
    
    # Create test customer objects
    from agents import Customer
    
    test_customers = [
        Customer(
            name="High Quality Lead",
            email="high@example.com",
            company="Tech Corp",
            industry="SaaS",
            lead_score=95,
            last_contact_days_ago=45,
            annual_revenue=2000000,
            current_tool="Excel",
            region="North America"
        ),
        Customer(
            name="Medium Quality Lead",
            email="medium@example.com",
            company="Retail Inc",
            industry="Retail",
            lead_score=75,
            last_contact_days_ago=20,
            annual_revenue=600000,
            current_tool="None",
            region="Europe"
        ),
        Customer(
            name="Low Quality Lead",
            email="low@example.com",
            company="Small Shop",
            industry="Retail",
            lead_score=60,
            last_contact_days_ago=5,
            annual_revenue=200000,
            current_tool="None",
            region="Asia"
        )
    ]
    
    for customer in test_customers:
        prob = scorer.predict_conversion_probability(customer)
        print(f"{customer.name:25s} → {prob:.1%} conversion probability")
    
    print("-" * 60)
    print()
    
    print("✓ Model training complete!")
    print(f"✓ Model saved to: models/lead_scorer.pkl")
    print()
    print("Next steps:")
    print("  1. Run: python api.py")
    print("  2. The API will automatically use the ML model")
    print("  3. Check /stats endpoint for ML insights")
    print()


if __name__ == "__main__":
    main()
