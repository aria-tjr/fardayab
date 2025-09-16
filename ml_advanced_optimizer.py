#!/usr/bin/env python3
"""
Advanced Machine Learning Optimization System
Uses multiple ML algorithms for intelligent parameter prediction and evolution
"""
import asyncio
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
import random
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from improved_optimizer import ImprovedOptimizer

@dataclass
class MLModel:
    """Machine Learning Model wrapper"""
    name: str
    model: Any
    scaler: Any
    performance: float
    predictions: List[float]
    feature_importance: Optional[Dict[str, float]] = None

class AdvancedMLOptimizer(ImprovedOptimizer):
    """Advanced ML-powered optimization system"""
    
    def __init__(self):
        super().__init__()
        
        # More permissive ranges for high frequency trading
        self.param_ranges = {
            'CONFIDENCE_THRESHOLD': (0.65, 0.90),
            'ULTRA_MIN_CONFIDENCE': (0.70, 0.95),
            'RSI_OVERSOLD': (25, 45),
            'RSI_OVERBOUGHT': (55, 75),
            'STOP_LOSS_ATR_MULTIPLIER': (1.0, 2.5),
            'TAKE_PROFIT_ATR_MULTIPLIER': (1.5, 3.0),
            'MIN_VOLUME_RATIO': (1.0, 2.5),
            'MIN_ATR_RATIO': (1.0, 2.0),
            'MIN_TREND_STRENGTH': (10, 40),
            'MIN_MOMENTUM_CONSISTENCY': (1, 4),
            'TRADING_HOURS_START': (6, 18),
            'TRADING_HOURS_END': (14, 22),
            'MIN_RSI_DIVERGENCE': (2, 15),
            'MAX_VOLATILITY': (0.03, 0.10),
            'POSITION_SIZE': (0.01, 0.10),
            'MAX_DRAWDOWN_PCT': (3.0, 10.0),
            'MAX_CONCURRENT_TRADES': (1, 6),
            'MAX_CONSECUTIVE_LOSSES': (2, 8)
        }
        
        # ML Models
        self.ml_models = {}
        self.ensemble_model = None
        self.feature_scaler = StandardScaler()
        self.target_scaler = MinMaxScaler()
        
        # Training data
        self.training_data = []
        self.feature_columns = list(self.param_ranges.keys())
        
        # ML Configuration
        self.min_training_samples = 50
        self.retrain_frequency = 20  # Retrain every 20 iterations
        self.ensemble_weights = {}
        
        # Performance tracking
        self.ml_performance_history = []
        self.prediction_accuracy = []
        
    def create_ml_models(self) -> Dict[str, Any]:
        """Create ensemble of ML models"""
        models = {
            'random_forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=8,
                min_samples_split=5,
                random_state=42
            ),
            'extra_trees': ExtraTreesRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            ),
            'neural_network': MLPRegressor(
                hidden_layer_sizes=(100, 50, 25),
                activation='relu',
                solver='adam',
                alpha=0.001,
                learning_rate='adaptive',
                max_iter=1000,
                random_state=42
            ),
            'svr': SVR(
                kernel='rbf',
                C=100,
                gamma='scale',
                epsilon=0.01
            ),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=0.1),
            'elastic_net': ElasticNet(alpha=0.1, l1_ratio=0.5)
        }
        return models
    
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for ML models"""
        if len(self.training_data) < self.min_training_samples:
            return None, None
        
        # Convert to DataFrame
        df = pd.DataFrame(self.training_data)
        
        # Prepare features (parameters)
        X = df[self.feature_columns].values
        
        # Prepare targets (fitness scores)
        y = df['fitness_score'].values
        
        # Scale features
        X_scaled = self.feature_scaler.fit_transform(X)
        
        # Scale targets
        y_scaled = self.target_scaler.fit_transform(y.reshape(-1, 1)).flatten()
        
        return X_scaled, y_scaled
    
    def train_ml_models(self) -> Dict[str, MLModel]:
        """Train all ML models"""
        X, y = self.prepare_training_data()
        if X is None:
            return {}
        
        models = self.create_ml_models()
        trained_models = {}
        
        print(f"🤖 Training {len(models)} ML models with {len(X)} samples...")
        
        for name, model in models.items():
            try:
                # Train model
                model.fit(X, y)
                
                # Cross-validation score
                cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
                performance = cv_scores.mean()
                
                # Make predictions
                predictions = model.predict(X)
                
                # Calculate feature importance (if available)
                feature_importance = None
                if hasattr(model, 'feature_importances_'):
                    feature_importance = dict(zip(self.feature_columns, model.feature_importances_))
                elif hasattr(model, 'coef_'):
                    feature_importance = dict(zip(self.feature_columns, abs(model.coef_)))
                
                trained_models[name] = MLModel(
                    name=name,
                    model=model,
                    scaler=self.feature_scaler,
                    performance=performance,
                    predictions=predictions,
                    feature_importance=feature_importance
                )
                
                print(f"  ✅ {name}: R² = {performance:.3f}")
                
            except Exception as e:
                print(f"  ❌ {name}: Error - {e}")
                continue
        
        return trained_models
    
    def create_ensemble_model(self, ml_models: Dict[str, MLModel]) -> Any:
        """Create ensemble model from individual models"""
        if not ml_models:
            return None
        
        # Calculate weights based on performance
        total_performance = sum(model.performance for model in ml_models.values())
        weights = {name: model.performance / total_performance 
                  for name, model in ml_models.items()}
        
        self.ensemble_weights = weights
        
        class EnsembleModel:
            def __init__(self, models, weights):
                self.models = models
                self.weights = weights
            
            def predict(self, X):
                predictions = np.zeros(len(X))
                for name, model in self.models.items():
                    predictions += self.weights[name] * model.model.predict(X)
                return predictions
        
        return EnsembleModel(ml_models, weights)
    
    def predict_fitness(self, parameters: Dict[str, Any]) -> float:
        """Predict fitness using ML models"""
        if not self.ml_models:
            return 0.0
        
        try:
            # Convert parameters to array
            X = np.array([parameters[col] for col in self.feature_columns]).reshape(1, -1)
            
            # Scale features
            X_scaled = self.feature_scaler.transform(X)
            
            # Use ensemble model if available
            if self.ensemble_model:
                prediction = self.ensemble_model.predict(X_scaled)[0]
            else:
                # Use best individual model
                best_model = max(self.ml_models.values(), key=lambda x: x.performance)
                prediction = best_model.model.predict(X_scaled)[0]
            
            # Inverse transform prediction
            prediction = self.target_scaler.inverse_transform([[prediction]])[0][0]
            
            return max(prediction, 0.0)  # Ensure non-negative
            
        except Exception as e:
            print(f"⚠️  ML prediction error: {e}")
            return 0.0
    
    def suggest_parameters_ml(self, num_suggestions: int = 10) -> List[Dict[str, Any]]:
        """Use ML to suggest promising parameters"""
        if not self.ml_models:
            return []
        
        suggestions = []
        
        # Generate random parameters
        for _ in range(num_suggestions * 3):  # Generate more to filter
            params = self.create_random_parameters()
            predicted_fitness = self.predict_fitness(params)
            
            # Only keep high-predicted fitness parameters
            if predicted_fitness > 50:  # Threshold for "good" predictions
                suggestions.append(params)
                if len(suggestions) >= num_suggestions:
                    break
        
        # If not enough high-predicted parameters, add some random ones
        while len(suggestions) < num_suggestions:
            suggestions.append(self.create_random_parameters())
        
        return suggestions[:num_suggestions]
    
    def analyze_feature_importance(self) -> Dict[str, float]:
        """Analyze feature importance across all models"""
        if not self.ml_models:
            return {}
        
        importance_scores = {col: 0.0 for col in self.feature_columns}
        
        for model in self.ml_models.values():
            if model.feature_importance:
                weight = self.ensemble_weights.get(model.name, 1.0)
                for feature, importance in model.feature_importance.items():
                    importance_scores[feature] += importance * weight
        
        # Normalize scores
        total = sum(importance_scores.values())
        if total > 0:
            importance_scores = {k: v/total for k, v in importance_scores.items()}
        
        return importance_scores
    
    def calculate_fitness(self, win_rate: float, total_signals: int, total_pnl: float, 
                         max_drawdown: float, sharpe_ratio: float, profit_factor: float,
                         trading_frequency: float) -> float:
        """Enhanced fitness calculation for high frequency trading"""
        
        # Primary: Win rate (heavily weighted)
        win_rate_score = min(win_rate / 80.0, 1.0) * 35
        
        # Secondary: Trading frequency (heavily weighted)
        freq_score = min(trading_frequency / 3.0, 1.0) * 30
        
        # Signal generation bonus
        signal_score = min(total_signals / 30.0, 1.0) * 15
        
        # Risk management
        drawdown_penalty = max(0, (max_drawdown - 15) / 15) * 10
        sharpe_bonus = max(0, min(sharpe_ratio / 1.0, 1.0)) * 5
        
        # Profit factor bonus
        pf_bonus = max(0, min((profit_factor - 1.0) / 1.0, 1.0)) * 5
        
        # PnL bonus
        pnl_bonus = max(0, min(total_pnl / 300, 1.0)) * 5
        
        # Calculate final fitness
        fitness = (win_rate_score + freq_score + signal_score + sharpe_bonus + 
                  pf_bonus + pnl_bonus - drawdown_penalty)
        
        return max(fitness, 0)
    
    async def evaluate_parameters(self, params: Dict[str, Any]) -> Any:
        """Evaluate parameters and store training data"""
        result = await super().evaluate_parameters(params)
        
        # Store for ML training
        training_sample = params.copy()
        training_sample['fitness_score'] = result.fitness_score
        training_sample['win_rate'] = result.win_rate
        training_sample['trading_frequency'] = result.trading_frequency
        training_sample['total_signals'] = result.total_signals
        training_sample['max_drawdown'] = result.max_drawdown
        training_sample['sharpe_ratio'] = result.sharpe_ratio
        training_sample['profit_factor'] = result.profit_factor
        training_sample['total_pnl'] = result.total_pnl
        
        self.training_data.append(training_sample)
        
        return result
    
    async def optimize(self, iterations: int = 200) -> list:
        """Run ML-powered optimization"""
        print(f"🤖 Advanced ML Optimization System")
        print(f"🎯 Target: 80%+ Win Rate + 3+ Trades per Day")
        print(f"🔄 Running {iterations} iterations with ML guidance...")
        print("=" * 70)
        
        for i in range(iterations):
            if i % 20 == 0:
                print(f"📈 Iteration {i+1}/{iterations}")
            
            # Retrain ML models periodically
            if i > 0 and i % self.retrain_frequency == 0:
                print(f"🤖 Retraining ML models...")
                self.ml_models = self.train_ml_models()
                self.ensemble_model = self.create_ensemble_model(self.ml_models)
                
                # Analyze feature importance
                importance = self.analyze_feature_importance()
                if importance:
                    print(f"🔍 Top 5 Important Features:")
                    sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
                    for feature, score in sorted_features[:5]:
                        print(f"   {feature}: {score:.3f}")
            
            # Choose parameters: ML-suggested or random
            if i > self.min_training_samples and self.ml_models:
                # Use ML to suggest parameters
                if i % 3 == 0:  # Use ML suggestions 1/3 of the time
                    suggestions = self.suggest_parameters_ml(1)
                    if suggestions:
                        params = suggestions[0]
                    else:
                        params = self.create_random_parameters()
                else:
                    params = self.create_random_parameters()
            else:
                params = self.create_random_parameters()
            
            # Evaluate parameters
            result = await self.evaluate_parameters(params)
            self.results.append(result)
            
            # Update best result
            if self.best_result is None or result.fitness_score > self.best_result.fitness_score:
                self.best_result = result
            
            # Log progress
            if i % 20 == 0:
                print(f"  Win rate: {result.win_rate:.2f}% | Signals: {result.total_signals} | "
                      f"Freq: {result.trading_frequency:.2f}/day | Fitness: {result.fitness_score:.2f}")
                
                # Show ML prediction accuracy if available
                if self.ml_models and len(self.training_data) > 10:
                    recent_data = self.training_data[-10:]
                    actual_fitness = [d['fitness_score'] for d in recent_data]
                    predicted_fitness = [self.predict_fitness({k: v for k, v in d.items() 
                                                             if k in self.feature_columns}) 
                                       for d in recent_data]
                    
                    if predicted_fitness and all(p > 0 for p in predicted_fitness):
                        mse = mean_squared_error(actual_fitness, predicted_fitness)
                        print(f"  ML Prediction MSE: {mse:.2f}")
            
            # Early stopping if both targets achieved
            if (result.win_rate >= 80.0 and result.trading_frequency >= 3.0):
                print(f"🎉 TARGET ACHIEVED! Win rate: {result.win_rate:.2f}%, "
                      f"Trading freq: {result.trading_frequency:.2f}/day")
                break
        
        # Final model training
        print(f"🤖 Final ML model training...")
        self.ml_models = self.train_ml_models()
        self.ensemble_model = self.create_ensemble_model(self.ml_models)
        
        # Sort results by fitness
        self.results.sort(key=lambda x: x.fitness_score, reverse=True)
        
        return self.results
    
    def save_ml_analysis(self):
        """Save ML analysis results"""
        if not self.ml_models:
            return
        
        analysis = {
            'model_performance': {name: model.performance for name, model in self.ml_models.items()},
            'ensemble_weights': self.ensemble_weights,
            'feature_importance': self.analyze_feature_importance(),
            'training_samples': len(self.training_data),
            'best_parameters': self.best_result.parameters if self.best_result else None
        }
        
        with open('ml_optimization_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"📊 ML analysis saved to ml_optimization_analysis.json")

async def main():
    """Main function for ML-powered optimization"""
    print("🚀 Advanced Machine Learning Optimization System")
    print("🎯 Target: 80%+ Win Rate with 3+ Trades per Day")
    print("🤖 Using ensemble of ML models for intelligent parameter prediction")
    print("=" * 80)
    
    optimizer = AdvancedMLOptimizer()
    
    try:
        # Run ML-powered optimization
        results = await optimizer.optimize(iterations=200)
        
        # Show results
        print("\n" + "=" * 80)
        print("📊 ML-POWERED OPTIMIZATION RESULTS")
        print("=" * 80)
        
        if optimizer.best_result:
            best = optimizer.best_result
            print(f"🏆 Best Win Rate: {best.win_rate:.2f}%")
            print(f"📈 Total Signals: {best.total_signals}")
            print(f"📊 Trading Frequency: {best.trading_frequency:.2f} signals/day")
            print(f"💰 Total P&L: ${best.total_pnl:.2f}")
            print(f"📉 Max Drawdown: {best.max_drawdown:.2f}%")
            print(f"📊 Sharpe Ratio: {best.sharpe_ratio:.2f}")
            print(f"🎯 Fitness Score: {best.fitness_score:.2f}")
            
            # Check achievements
            win_rate_ok = best.win_rate >= 80.0
            freq_ok = best.trading_frequency >= 3.0
            
            print(f"\n🎯 TARGET ACHIEVEMENT:")
            print(f"  Win Rate 80%+: {'✅ YES' if win_rate_ok else '❌ NO'} ({best.win_rate:.2f}%)")
            print(f"  Trading Freq 3+/day: {'✅ YES' if freq_ok else '❌ NO'} ({best.trading_frequency:.2f})")
            
            if win_rate_ok and freq_ok:
                print(f"\n🎉 BOTH TARGETS ACHIEVED!")
            else:
                print(f"\n⚠️  Targets not fully achieved, but ML system is learning...")
        
        # Show ML model performance
        if optimizer.ml_models:
            print(f"\n🤖 ML MODEL PERFORMANCE:")
            for name, model in optimizer.ml_models.items():
                print(f"  {name}: R² = {model.performance:.3f}")
        
        # Show feature importance
        importance = optimizer.analyze_feature_importance()
        if importance:
            print(f"\n🔍 FEATURE IMPORTANCE (Top 10):")
            sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            for feature, score in sorted_features[:10]:
                print(f"  {feature}: {score:.3f}")
        
        # Show top 10 results
        print(f"\n🏅 TOP 10 RESULTS:")
        for i, result in enumerate(results[:10], 1):
            status = "✅" if result.win_rate >= 80.0 and result.trading_frequency >= 3.0 else "⚠️"
            print(f"{i:2d}. {status} WR: {result.win_rate:6.2f}% | "
                  f"Signals: {result.total_signals:2d} | "
                  f"Freq: {result.trading_frequency:4.2f}/day | "
                  f"Fitness: {result.fitness_score:5.2f}")
        
        # Save results
        optimizer.save_results()
        optimizer.save_ml_analysis()
        
        print(f"\n📁 Results saved to:")
        print(f"  - improved_optimization_results.json")
        print(f"  - improved_optimization_report.md")
        print(f"  - ml_optimization_analysis.json")
        print(f"  - .env (updated with best parameters)")
        
    except Exception as e:
        print(f"❌ Error during ML optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
