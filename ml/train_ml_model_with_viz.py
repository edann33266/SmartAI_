"""
Enhanced ML Model Training with Visualizations
Creates confusion matrix, ROC curve, feature importance, and training metrics
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
from sklearn.model_selection import learning_curve
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
    Create realistic sample training data.
    In production, replace this with actual historical conversion data.
    """
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'lead_score': [],
        'last_contact_days_ago': [],
        'annual_revenue': [],
        'industry': [],
        'region': [],
        'current_tool': [],
        'converted': []
    }
    
    industries = ['SaaS', 'Manufacturing', 'Retail', 'Technology', 'Finance', 'E-Commerce']
    regions = ['North America', 'Europe', 'Asia', 'Africa']
    tools = ['Excel', 'Salesforce', 'HubSpot', 'Freshsales', 'No CRM Tool', 'Custom In-house Tool']
    
    for i in range(n_samples):
        # Generate features with correlation to conversion
        lead_score = np.random.randint(20, 100)
        contact_days = np.random.randint(5, 300)
        revenue = np.random.randint(200000, 50000000)
        industry = np.random.choice(industries)
        region = np.random.choice(regions)
        tool = np.random.choice(tools)
        
        # Conversion logic with realistic probability
        conversion_prob = 0.0
        
        if lead_score >= 80:
            conversion_prob += 0.4
        elif lead_score >= 60:
            conversion_prob += 0.2
        
        if contact_days >= 30:
            conversion_prob += 0.3
        elif contact_days >= 14:
            conversion_prob += 0.15
        
        if revenue >= 10000000:
            conversion_prob += 0.2
        elif revenue >= 1000000:
            conversion_prob += 0.1
        
        if industry in ['SaaS', 'Technology']:
            conversion_prob += 0.1
        
        # Add randomness
        conversion_prob += np.random.uniform(-0.2, 0.2)
        conversion_prob = max(0, min(1, conversion_prob))
        
        converted = 1 if np.random.random() < conversion_prob else 0
        
        data['lead_score'].append(lead_score)
        data['last_contact_days_ago'].append(contact_days)
        data['annual_revenue'].append(revenue)
        data['industry'].append(industry)
        data['region'].append(region)
        data['current_tool'].append(tool)
        data['converted'].append(converted)
    
    return pd.DataFrame(data)


def plot_confusion_matrix(y_true, y_pred, viz_folder):
    """Create and save confusion matrix visualization."""
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True,
                square=True, linewidths=1, linecolor='black')
    
    plt.title('Confusion Matrix\nLead Conversion Prediction', fontsize=16, fontweight='bold', pad=20)
    plt.ylabel('Actual', fontsize=12, fontweight='bold')
    plt.xlabel('Predicted', fontsize=12, fontweight='bold')
    
    # Add labels
    plt.xticks([0.5, 1.5], ['Not Converted (0)', 'Converted (1)'])
    plt.yticks([0.5, 1.5], ['Not Converted (0)', 'Converted (1)'])
    
    # Add text annotations
    accuracy = accuracy_score(y_true, y_pred)
    plt.text(1, -0.3, f'Accuracy: {accuracy:.2%}', 
             ha='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(viz_folder / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {viz_folder / 'confusion_matrix.png'}")
    plt.close()


def plot_roc_curve(y_true, y_pred_proba, viz_folder):
    """Create and save ROC curve."""
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(10, 8))
    plt.plot(fpr, tpr, color='darkorange', lw=2, 
             label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', 
             label='Random Classifier')
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12, fontweight='bold')
    plt.ylabel('True Positive Rate', fontsize=12, fontweight='bold')
    plt.title('ROC Curve - Lead Conversion Prediction', 
              fontsize=16, fontweight='bold', pad=20)
    plt.legend(loc="lower right", fontsize=11)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(viz_folder / 'roc_curve.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {viz_folder / 'roc_curve.png'}")
    plt.close()


def plot_precision_recall_curve(y_true, y_pred_proba, viz_folder):
    """Create and save Precision-Recall curve."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
    
    plt.figure(figsize=(10, 8))
    plt.plot(recall, precision, color='blue', lw=2, label='Precision-Recall curve')
    plt.xlabel('Recall', fontsize=12, fontweight='bold')
    plt.ylabel('Precision', fontsize=12, fontweight='bold')
    plt.title('Precision-Recall Curve', fontsize=16, fontweight='bold', pad=20)
    plt.legend(loc="lower left", fontsize=11)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(viz_folder / 'precision_recall_curve.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {viz_folder / 'precision_recall_curve.png'}")
    plt.close()


def plot_feature_importance(scorer, viz_folder):
    """Create and save feature importance chart."""
    importance = scorer.get_feature_importance()
    
    if not importance:
        print("⚠️  No feature importance available")
        return
    
    features = list(importance.keys())
    values = list(importance.values())
    
    plt.figure(figsize=(12, 8))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(features)))
    bars = plt.barh(features, values, color=colors, edgecolor='black', linewidth=1.5)
    
    plt.xlabel('Importance Score', fontsize=12, fontweight='bold')
    plt.ylabel('Features', fontsize=12, fontweight='bold')
    plt.title('Feature Importance in Lead Conversion Prediction', 
              fontsize=16, fontweight='bold', pad=20)
    plt.grid(axis='x', alpha=0.3)
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, values)):
        plt.text(value + 0.01, i, f'{value:.3f}', 
                va='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(viz_folder / 'feature_importance.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {viz_folder / 'feature_importance.png'}")
    plt.close()


def plot_learning_curves(scorer, X, y, viz_folder):
    """Create and save learning curves."""
    train_sizes, train_scores, val_scores = learning_curve(
        scorer.model, X, y, cv=5, n_jobs=-1,
        train_sizes=np.linspace(0.1, 1.0, 10),
        scoring='accuracy'
    )
    
    train_mean = np.mean(train_scores, axis=1)
    train_std = np.std(train_scores, axis=1)
    val_mean = np.mean(val_scores, axis=1)
    val_std = np.std(val_scores, axis=1)
    
    plt.figure(figsize=(12, 8))
    plt.plot(train_sizes, train_mean, 'o-', color='blue', 
             label='Training Score', linewidth=2, markersize=8)
    plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, 
                     alpha=0.2, color='blue')
    
    plt.plot(train_sizes, val_mean, 'o-', color='red', 
             label='Validation Score', linewidth=2, markersize=8)
    plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, 
                     alpha=0.2, color='red')
    
    plt.xlabel('Training Set Size', fontsize=12, fontweight='bold')
    plt.ylabel('Accuracy Score', fontsize=12, fontweight='bold')
    plt.title('Learning Curves - Model Performance vs Training Size', 
              fontsize=16, fontweight='bold', pad=20)
    plt.legend(loc='lower right', fontsize=11)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(viz_folder / 'learning_curves.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {viz_folder / 'learning_curves.png'}")
    plt.close()


def plot_metrics_comparison(metrics, viz_folder):
    """Create and save metrics comparison chart."""
    metric_names = list(metrics.keys())
    metric_values = list(metrics.values())
    
    plt.figure(figsize=(12, 8))
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    bars = plt.bar(metric_names, metric_values, color=colors, 
                   edgecolor='black', linewidth=2, alpha=0.8)
    
    plt.ylabel('Score', fontsize=12, fontweight='bold')
    plt.title('Model Performance Metrics', fontsize=16, fontweight='bold', pad=20)
    plt.ylim([0, 1.1])
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, metric_values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{value:.3f}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(viz_folder / 'metrics_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {viz_folder / 'metrics_comparison.png'}")
    plt.close()


def plot_class_distribution(y, viz_folder):
    """Create and save class distribution chart."""
    unique, counts = np.unique(y, return_counts=True)
    
    plt.figure(figsize=(10, 8))
    colors = ['#e74c3c', '#2ecc71']
    bars = plt.bar(['Not Converted (0)', 'Converted (1)'], counts, 
                   color=colors, edgecolor='black', linewidth=2, alpha=0.8)
    
    plt.ylabel('Count', fontsize=12, fontweight='bold')
    plt.title('Class Distribution in Training Data', 
              fontsize=16, fontweight='bold', pad=20)
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels and percentages
    total = sum(counts)
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        percentage = (count / total) * 100
        plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{count}\n({percentage:.1f}%)',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(viz_folder / 'class_distribution.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {viz_folder / 'class_distribution.png'}")
    plt.close()


def main():
    print("=" * 70)
    print("SalesAI ML Lead Scorer Training with Visualizations")
    print("=" * 70)
    print()
    
    # Create visualizations folder
    viz_folder = create_visualizations_folder()
    print(f"✓ Visualizations will be saved to: {viz_folder}/")
    print()
    
    # Create training data
    print("Creating training data...")
    training_data = create_sample_training_data()
    print(f"✓ Created {len(training_data)} training samples")
    print()
    
    # Show data summary
    print("Data Summary:")
    print(f"  • Total samples: {len(training_data)}")
    print(f"  • Converted leads: {training_data['converted'].sum()}")
    print(f"  • Not converted: {len(training_data) - training_data['converted'].sum()}")
    print(f"  • Conversion rate: {training_data['converted'].mean():.1%}")
    print()
    
    # Plot class distribution
    plot_class_distribution(training_data['converted'].values, viz_folder)
    
    # Train model
    print("Training ML model...")
    print("-" * 70)
    scorer = MLLeadScorer()
    scorer.train_model(training_data)
    print("-" * 70)
    print()
    
    # Get predictions for visualization
    from sklearn.model_selection import train_test_split
    
    # Prepare data
    training_data['industry_encoded'] = scorer.label_encoders['industry'].transform(training_data['industry'])
    training_data['region_encoded'] = scorer.label_encoders['region'].transform(training_data['region'])
    training_data['has_current_tool'] = (
        training_data['current_tool'].notna() & 
        (training_data['current_tool'] != 'None')
    ).astype(int)
    
    X = training_data[scorer.feature_names].values
    y = training_data['converted'].values
    
    X_scaled = scorer.scaler.transform(X)
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )
    
    # Get predictions
    y_pred = scorer.model.predict(X_test)
    y_pred_proba = scorer.model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'Accuracy': accuracy_score(y_test, y_pred),
        'Precision': precision_score(y_test, y_pred, zero_division=0),
        'Recall': recall_score(y_test, y_pred, zero_division=0),
        'F1-Score': f1_score(y_test, y_pred, zero_division=0)
    }
    
    print("Model Performance Metrics:")
    for metric, value in metrics.items():
        print(f"  • {metric}: {value:.3f}")
    print()
    
    # Create visualizations
    print("Creating visualizations...")
    print("-" * 70)
    
    plot_confusion_matrix(y_test, y_pred, viz_folder)
    plot_roc_curve(y_test, y_pred_proba, viz_folder)
    plot_precision_recall_curve(y_test, y_pred_proba, viz_folder)
    plot_feature_importance(scorer, viz_folder)
    plot_learning_curves(scorer, X_scaled, y, viz_folder)
    plot_metrics_comparison(metrics, viz_folder)
    
    print("-" * 70)
    print()
    
    # Show feature importance
    print("Feature Importance:")
    for feature, importance in scorer.get_feature_importance().items():
        bar = "█" * int(importance * 50)
        print(f"  {feature:25s} {bar} {importance:.3f}")
    print()
    
    # Classification report
    print("Detailed Classification Report:")
    print("-" * 70)
    print(classification_report(y_test, y_pred, 
                                target_names=['Not Converted', 'Converted']))
    print("-" * 70)
    print()
    
    print("=" * 70)
    print("✅ Training Complete!")
    print("=" * 70)
    print()
    print(f"Model saved to: models/lead_scorer.pkl")
    print(f"Visualizations saved to: {viz_folder}/")
    print()
    print("Generated visualizations:")
    print("  1. confusion_matrix.png - Model prediction accuracy")
    print("  2. roc_curve.png - ROC curve and AUC score")
    print("  3. precision_recall_curve.png - Precision vs Recall")
    print("  4. feature_importance.png - Most important features")
    print("  5. learning_curves.png - Training vs validation performance")
    print("  6. metrics_comparison.png - All metrics comparison")
    print("  7. class_distribution.png - Training data distribution")
    print()
    print("Next steps:")
    print("  1. Review visualizations in the 'visualizations' folder")
    print("  2. Run: python api.py")
    print("  3. The API will automatically use the trained ML model")
    print()


if __name__ == "__main__":
    main()
