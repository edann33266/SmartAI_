"""
ML-based Lead Scoring System
Uses Random Forest to predict lead quality and conversion probability
"""
import pickle
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


class MLLeadScorer:
    """
    Machine Learning based lead scoring system.
    Predicts lead quality and conversion probability.
    """
    
    def __init__(self, model_path: str = "models/lead_scorer.pkl"):
        self.model_path = Path(model_path)
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.feature_names = [
            'lead_score',
            'last_contact_days_ago',
            'annual_revenue',
            'industry_encoded',
            'region_encoded',
            'has_current_tool'
        ]
        
        # Load model if exists
        if self.model_path.exists():
            self.load_model()
    
    def prepare_features(self, customer) -> np.ndarray:
        """
        Extract and prepare features from customer object.
        """
        # Encode categorical variables
        if 'industry' not in self.label_encoders:
            self.label_encoders['industry'] = LabelEncoder()
            self.label_encoders['region'] = LabelEncoder()
        
        # Handle unseen categories gracefully
        try:
            industry_encoded = self.label_encoders['industry'].transform([customer.industry])[0]
        except ValueError:
            industry_encoded = -1  # Unknown category
        
        try:
            region_encoded = self.label_encoders['region'].transform([customer.region])[0]
        except ValueError:
            region_encoded = -1  # Unknown category
        
        # Create feature vector
        features = np.array([
            customer.lead_score,
            customer.last_contact_days_ago,
            customer.annual_revenue / 1000000,  # Normalize to millions
            industry_encoded,
            region_encoded,
            1 if customer.current_tool and customer.current_tool != "None" else 0
        ]).reshape(1, -1)
        
        return features
    
    def predict_conversion_probability(self, customer) -> float:
        """
        Predict the probability that this lead will convert.
        Returns a score between 0 and 1.
        """
        if self.model is None:
            # Fallback to rule-based scoring if no model
            return self._rule_based_score(customer)
        
        features = self.prepare_features(customer)
        
        if self.scaler:
            features = self.scaler.transform(features)
        
        # Get probability of positive class
        probability = self.model.predict_proba(features)[0][1]
        return float(probability)
    
    def _rule_based_score(self, customer) -> float:
        """
        Fallback rule-based scoring when ML model is not available.
        """
        score = 0.0
        
        # Lead score contribution (40%)
        score += (customer.lead_score / 100) * 0.4
        
        # Recency contribution (20%)
        if customer.last_contact_days_ago >= 30:
            score += 0.2
        elif customer.last_contact_days_ago >= 14:
            score += 0.15
        elif customer.last_contact_days_ago >= 7:
            score += 0.1
        
        # Revenue contribution (20%)
        if customer.annual_revenue >= 1000000:
            score += 0.2
        elif customer.annual_revenue >= 500000:
            score += 0.15
        elif customer.annual_revenue >= 100000:
            score += 0.1
        
        # Industry contribution (10%)
        high_value_industries = ['SaaS', 'Technology', 'Finance']
        if customer.industry in high_value_industries:
            score += 0.1
        
        # Current tool contribution (10%)
        if customer.current_tool and customer.current_tool != "None":
            score += 0.1  # Has a tool to replace
        
        return min(score, 1.0)
    
    def rank_leads(self, customers: List) -> List[Tuple[object, float]]:
        """
        Rank all leads by conversion probability.
        Returns list of (customer, score) tuples sorted by score descending.
        """
        scored_leads = []
        
        for customer in customers:
            score = self.predict_conversion_probability(customer)
            scored_leads.append((customer, score))
        
        # Sort by score descending
        scored_leads.sort(key=lambda x: x[1], reverse=True)
        
        return scored_leads
    
    def select_top_leads(self, customers: List, threshold: float = 0.7, max_leads: int = None) -> List:
        """
        Select top leads based on ML scoring.
        
        Args:
            customers: List of customer objects
            threshold: Minimum conversion probability (0-1)
            max_leads: Maximum number of leads to return (None = no limit)
        
        Returns:
            List of selected customers
        """
        ranked_leads = self.rank_leads(customers)
        
        # Filter by threshold
        selected = [customer for customer, score in ranked_leads if score >= threshold]
        
        # Limit number if specified
        if max_leads:
            selected = selected[:max_leads]
        
        return selected
    
    def train_model(self, training_data: pd.DataFrame):
        """
        Train the ML model on historical data.
        
        Expected columns:
        - lead_score
        - last_contact_days_ago
        - annual_revenue
        - industry
        - region
        - current_tool
        - converted (target: 0 or 1)
        """
        # Encode categorical variables
        self.label_encoders['industry'] = LabelEncoder()
        self.label_encoders['region'] = LabelEncoder()
        
        training_data['industry_encoded'] = self.label_encoders['industry'].fit_transform(
            training_data['industry']
        )
        training_data['region_encoded'] = self.label_encoders['region'].fit_transform(
            training_data['region']
        )
        training_data['has_current_tool'] = (
            training_data['current_tool'].notna() & 
            (training_data['current_tool'] != 'None')
        ).astype(int)
        
        # Prepare features and target
        X = training_data[self.feature_names].values
        y = training_data['converted'].values
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        print(f"Model trained successfully!")
        print(f"Training accuracy: {train_score:.3f}")
        print(f"Testing accuracy: {test_score:.3f}")
        
        # Save model
        self.save_model()
    
    def save_model(self):
        """Save trained model to disk."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from disk."""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.feature_names = model_data['feature_names']
            
            print(f"Model loaded from {self.model_path}")
        except Exception as e:
            print(f"Could not load model: {e}")
            print("Using rule-based scoring as fallback")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores from the trained model.
        """
        if self.model is None:
            return {}
        
        importance = dict(zip(self.feature_names, self.model.feature_importances_))
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))


# Example usage and training script
if __name__ == "__main__":
    # Create sample training data
    sample_data = pd.DataFrame({
        'lead_score': [85, 92, 65, 78, 95, 70, 88, 60, 90, 75],
        'last_contact_days_ago': [30, 45, 10, 20, 60, 5, 35, 15, 50, 25],
        'annual_revenue': [1200000, 800000, 500000, 1500000, 2000000, 300000, 1000000, 400000, 1800000, 600000],
        'industry': ['SaaS', 'Manufacturing', 'Retail', 'SaaS', 'Technology', 'Retail', 'Finance', 'Manufacturing', 'Technology', 'SaaS'],
        'region': ['North America', 'Europe', 'Asia', 'North America', 'North America', 'Asia', 'Europe', 'Asia', 'North America', 'Europe'],
        'current_tool': ['Excel', 'None', 'Salesforce', 'Excel', 'HubSpot', 'None', 'Excel', 'None', 'Salesforce', 'Excel'],
        'converted': [1, 1, 0, 1, 1, 0, 1, 0, 1, 0]  # 1 = converted, 0 = not converted
    })
    
    # Train model
    scorer = MLLeadScorer()
    scorer.train_model(sample_data)
    
    # Show feature importance
    print("\nFeature Importance:")
    for feature, importance in scorer.get_feature_importance().items():
        print(f"  {feature}: {importance:.3f}")
