#!/usr/bin/env python3
"""
Advanced Continuous Parameter Optimizer for 80%+ Win Rate
Uses Genetic Algorithm + Machine Learning + Multi-Objective Optimization
"""
import os
import sys
import json
import random
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.backtesting.backtester import Backtester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('continuous_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """Result of optimization iteration"""
    generation: int
    individual_id: int
    parameters: Dict[str, Any]
    win_rate: float
    total_signals: int
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    fitness_score: float
    trading_frequency: float
    timestamp: datetime

@dataclass
class PopulationStats:
    """Population statistics for a generation"""
    generation: int
    best_win_rate: float
    avg_win_rate: float
    best_fitness: float
    avg_fitness: float
    best_trading_freq: float
    avg_trading_freq: float
    population_size: int
    diversity_score: float

class GeneticOptimizer:
    """Advanced genetic algorithm optimizer for trading parameters"""
    
    def __init__(self, 
                 target_win_rate: float = 80.0,
                 min_trading_frequency: float = 0.5,
                 population_size: int = 50,
                 max_generations: int = 100,
                 mutation_rate: float = 0.15,
                 crossover_rate: float = 0.8,
                 elite_size: int = 5):
        
        self.target_win_rate = target_win_rate
        self.min_trading_frequency = min_trading_frequency
        self.population_size = population_size
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        
        # Parameter ranges for optimization
        self.param_ranges = {
            'CONFIDENCE_THRESHOLD': (0.75, 0.99),
            'ULTRA_MIN_CONFIDENCE': (0.85, 0.99),
            'RSI_OVERSOLD': (25, 45),
            'RSI_OVERBOUGHT': (55, 75),
            'STOP_LOSS_ATR_MULTIPLIER': (0.8, 3.0),
            'TAKE_PROFIT_ATR_MULTIPLIER': (0.8, 3.0),
            'MIN_VOLUME_RATIO': (1.0, 4.0),
            'MIN_ATR_RATIO': (1.0, 3.0),
            'MIN_TREND_STRENGTH': (15, 60),
            'MIN_MOMENTUM_CONSISTENCY': (2, 6),
            'TRADING_HOURS_START': (8, 16),
            'TRADING_HOURS_END': (12, 20),
            'MIN_RSI_DIVERGENCE': (5, 25),
            'MAX_VOLATILITY': (0.02, 0.08),
            'POSITION_SIZE': (0.02, 0.15),
            'MAX_DRAWDOWN_PCT': (2.0, 8.0),
            'MAX_CONCURRENT_TRADES': (1, 4),
            'MAX_CONSECUTIVE_LOSSES': (2, 6)
        }
        
        # ML model for parameter prediction
        self.ml_model = None
        self.scaler = StandardScaler()
        self.training_data = []
        
        # Results storage
        self.population_history = []
        self.best_individuals = []
        self.optimization_log = []
        
        # Threading for parallel evaluation
        self.max_workers = min(8, os.cpu_count())
        
    def create_random_individual(self) -> Dict[str, Any]:
        """Create a random individual with parameters within ranges"""
        individual = {}
        
        for param, (min_val, max_val) in self.param_ranges.items():
            if isinstance(min_val, int):
                individual[param] = random.randint(min_val, max_val)
            else:
                individual[param] = round(random.uniform(min_val, max_val), 3)
        
        # Ensure logical constraints
        if individual['RSI_OVERBOUGHT'] - individual['RSI_OVERSOLD'] < 15:
            individual['RSI_OVERBOUGHT'] = individual['RSI_OVERSOLD'] + 15
            individual['RSI_OVERBOUGHT'] = min(individual['RSI_OVERBOUGHT'], 75)
        
        if individual['TRADING_HOURS_END'] <= individual['TRADING_HOURS_START']:
            individual['TRADING_HOURS_END'] = individual['TRADING_HOURS_START'] + 4
        
        if individual['TAKE_PROFIT_ATR_MULTIPLIER'] <= individual['STOP_LOSS_ATR_MULTIPLIER']:
            individual['TAKE_PROFIT_ATR_MULTIPLIER'] = individual['STOP_LOSS_ATR_MULTIPLIER'] + 0.5
        
        return individual
    
    def create_population(self) -> List[Dict[str, Any]]:
        """Create initial population"""
        population = []
        for _ in range(self.population_size):
            individual = self.create_random_individual()
            population.append(individual)
        return population
    
    async def evaluate_individual(self, individual: Dict[str, Any], generation: int, individual_id: int) -> OptimizationResult:
        """Evaluate a single individual using backtesting"""
        try:
            # Set parameters in Config
            for param, value in individual.items():
                if hasattr(Config, param):
                    setattr(Config, param, value)
            
            # Run backtest
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            backtester = Backtester(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            result = await backtester.run_backtest()
            backtester.close()
            
            # Calculate trading frequency (signals per day)
            days = (end_date - start_date).days
            trading_frequency = result.total_signals / days if days > 0 else 0
            
            # Calculate fitness score (multi-objective optimization)
            fitness = self.calculate_fitness(
                win_rate=result.win_rate,
                total_signals=result.total_signals,
                total_pnl=result.total_pnl,
                max_drawdown=result.max_drawdown,
                sharpe_ratio=result.sharpe_ratio,
                profit_factor=result.profit_factor,
                trading_frequency=trading_frequency
            )
            
            return OptimizationResult(
                generation=generation,
                individual_id=individual_id,
                parameters=individual.copy(),
                win_rate=result.win_rate,
                total_signals=result.total_signals,
                total_pnl=result.total_pnl,
                max_drawdown=result.max_drawdown,
                sharpe_ratio=result.sharpe_ratio,
                profit_factor=result.profit_factor,
                fitness_score=fitness,
                trading_frequency=trading_frequency,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error evaluating individual {individual_id}: {e}")
            # Return poor fitness for failed evaluations
            return OptimizationResult(
                generation=generation,
                individual_id=individual_id,
                parameters=individual.copy(),
                win_rate=0.0,
                total_signals=0,
                total_pnl=-1000.0,
                max_drawdown=100.0,
                sharpe_ratio=-10.0,
                profit_factor=0.0,
                fitness_score=-1000.0,
                trading_frequency=0.0,
                timestamp=datetime.now()
            )
    
    def calculate_fitness(self, win_rate: float, total_signals: int, total_pnl: float, 
                         max_drawdown: float, sharpe_ratio: float, profit_factor: float,
                         trading_frequency: float) -> float:
        """Calculate multi-objective fitness score"""
        
        # Primary objective: Win rate (heavily weighted)
        win_rate_score = min(win_rate / self.target_win_rate, 1.0) * 100
        
        # Secondary objective: Trading frequency (moderate weight)
        freq_score = min(trading_frequency / self.min_trading_frequency, 2.0) * 30
        
        # Risk management (moderate weight)
        drawdown_penalty = max(0, (max_drawdown - 15) / 15) * 20  # Penalty for high drawdown
        sharpe_bonus = max(0, min(sharpe_ratio / 2.0, 1.0)) * 15  # Bonus for good Sharpe
        
        # Profit factor bonus
        pf_bonus = max(0, min((profit_factor - 1.0) / 2.0, 1.0)) * 10
        
        # Signal quality bonus (penalize too few signals)
        signal_penalty = max(0, (10 - total_signals) / 10) * 10 if total_signals < 10 else 0
        
        # PnL bonus (moderate weight)
        pnl_bonus = max(0, min(total_pnl / 1000, 1.0)) * 15
        
        # Calculate final fitness
        fitness = (win_rate_score + freq_score + sharpe_bonus + pf_bonus + pnl_bonus - 
                  drawdown_penalty - signal_penalty)
        
        return max(fitness, 0)  # Ensure non-negative fitness
    
    async def evaluate_population_parallel(self, population: List[Dict[str, Any]], generation: int) -> List[OptimizationResult]:
        """Evaluate population in parallel"""
        results = []
        
        # Create tasks for parallel execution
        tasks = []
        for i, individual in enumerate(population):
            task = asyncio.create_task(self.evaluate_individual(individual, generation, i))
            tasks.append(task)
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {result}")
                # Create a poor result for failed evaluations
                valid_results.append(OptimizationResult(
                    generation=generation,
                    individual_id=i,
                    parameters=population[i].copy(),
                    win_rate=0.0,
                    total_signals=0,
                    total_pnl=-1000.0,
                    max_drawdown=100.0,
                    sharpe_ratio=-10.0,
                    profit_factor=0.0,
                    fitness_score=-1000.0,
                    trading_frequency=0.0,
                    timestamp=datetime.now()
                ))
            else:
                valid_results.append(result)
        
        return valid_results
    
    def select_parents(self, results: List[OptimizationResult], num_parents: int) -> List[Dict[str, Any]]:
        """Select parents using tournament selection"""
        parents = []
        
        for _ in range(num_parents):
            # Tournament selection (size 3)
            tournament_size = 3
            tournament_candidates = random.sample(results, min(tournament_size, len(results)))
            winner = max(tournament_candidates, key=lambda x: x.fitness_score)
            parents.append(winner.parameters)
        
        return parents
    
    def crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Create two offspring through crossover"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        child1 = {}
        child2 = {}
        
        for param in self.param_ranges.keys():
            if random.random() < 0.5:
                child1[param] = parent1[param]
                child2[param] = parent2[param]
            else:
                child1[param] = parent2[param]
                child2[param] = parent1[param]
        
        # Ensure logical constraints
        child1 = self.enforce_constraints(child1)
        child2 = self.enforce_constraints(child2)
        
        return child1, child2
    
    def mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """Mutate an individual"""
        if random.random() > self.mutation_rate:
            return individual
        
        mutated = individual.copy()
        
        # Select random parameters to mutate
        params_to_mutate = random.sample(
            list(self.param_ranges.keys()), 
            random.randint(1, max(1, len(self.param_ranges) // 4))
        )
        
        for param in params_to_mutate:
            min_val, max_val = self.param_ranges[param]
            
            if isinstance(min_val, int):
                # Integer parameter
                current_val = mutated[param]
                mutation_range = max(1, (max_val - min_val) // 10)
                new_val = current_val + random.randint(-mutation_range, mutation_range)
                mutated[param] = max(min_val, min(max_val, new_val))
            else:
                # Float parameter
                current_val = mutated[param]
                mutation_range = (max_val - min_val) * 0.1
                new_val = current_val + random.uniform(-mutation_range, mutation_range)
                mutated[param] = max(min_val, min(max_val, new_val))
        
        # Ensure logical constraints
        mutated = self.enforce_constraints(mutated)
        
        return mutated
    
    def enforce_constraints(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce logical constraints on parameters"""
        # RSI constraints
        if individual['RSI_OVERBOUGHT'] - individual['RSI_OVERSOLD'] < 15:
            individual['RSI_OVERBOUGHT'] = individual['RSI_OVERSOLD'] + 15
            individual['RSI_OVERBOUGHT'] = min(individual['RSI_OVERBOUGHT'], 75)
        
        # Trading hours constraints
        if individual['TRADING_HOURS_END'] <= individual['TRADING_HOURS_START']:
            individual['TRADING_HOURS_END'] = individual['TRADING_HOURS_START'] + 4
        
        # ATR multiplier constraints
        if individual['TAKE_PROFIT_ATR_MULTIPLIER'] <= individual['STOP_LOSS_ATR_MULTIPLIER']:
            individual['TAKE_PROFIT_ATR_MULTIPLIER'] = individual['STOP_LOSS_ATR_MULTIPLIER'] + 0.5
        
        return individual
    
    def create_next_generation(self, results: List[OptimizationResult]) -> List[Dict[str, Any]]:
        """Create next generation using genetic operators"""
        # Sort by fitness
        results.sort(key=lambda x: x.fitness_score, reverse=True)
        
        # Keep elite individuals
        elite = [r.parameters for r in results[:self.elite_size]]
        
        # Select parents
        parents = self.select_parents(results, self.population_size - self.elite_size)
        
        # Create offspring
        offspring = []
        for i in range(0, len(parents) - 1, 2):
            child1, child2 = self.crossover(parents[i], parents[i + 1])
            child1 = self.mutate(child1)
            child2 = self.mutate(child2)
            offspring.extend([child1, child2])
        
        # If odd number of parents, add one more
        if len(parents) % 2 == 1:
            child1, child2 = self.crossover(parents[-1], parents[0])
            child1 = self.mutate(child1)
            offspring.append(child1)
        
        # Combine elite and offspring
        next_generation = elite + offspring[:self.population_size - len(elite)]
        
        return next_generation
    
    def calculate_population_stats(self, results: List[OptimizationResult], generation: int) -> PopulationStats:
        """Calculate population statistics"""
        win_rates = [r.win_rate for r in results]
        fitness_scores = [r.fitness_score for r in results]
        trading_freqs = [r.trading_frequency for r in results]
        
        # Calculate diversity (standard deviation of parameters)
        diversity_scores = []
        for param in self.param_ranges.keys():
            values = [r.parameters[param] for r in results]
            if len(set(values)) > 1:  # Only if there's variation
                diversity_scores.append(np.std(values))
        
        diversity_score = np.mean(diversity_scores) if diversity_scores else 0
        
        return PopulationStats(
            generation=generation,
            best_win_rate=max(win_rates),
            avg_win_rate=np.mean(win_rates),
            best_fitness=max(fitness_scores),
            avg_fitness=np.mean(fitness_scores),
            best_trading_freq=max(trading_freqs),
            avg_trading_freq=np.mean(trading_freqs),
            population_size=len(results),
            diversity_score=diversity_score
        )
    
    def train_ml_model(self, results: List[OptimizationResult]):
        """Train ML model to predict fitness from parameters"""
        if len(results) < 20:  # Need minimum data
            return
        
        try:
            # Prepare training data
            X = []
            y = []
            
            for result in results:
                # Convert parameters to feature vector
                features = []
                for param in self.param_ranges.keys():
                    value = result.parameters[param]
                    # Normalize to 0-1 range
                    min_val, max_val = self.param_ranges[param]
                    normalized = (value - min_val) / (max_val - min_val)
                    features.append(normalized)
                
                X.append(features)
                y.append(result.fitness_score)
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Random Forest
            self.ml_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.ml_model.fit(X_scaled, y)
            
            # Cross-validation score
            cv_scores = cross_val_score(self.ml_model, X_scaled, y, cv=5)
            logger.info(f"ML model trained. CV score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
    
    def suggest_parameters(self) -> Optional[Dict[str, Any]]:
        """Use ML model to suggest promising parameters"""
        if self.ml_model is None:
            return None
        
        try:
            # Generate random parameters
            individual = self.create_random_individual()
            
            # Convert to feature vector
            features = []
            for param in self.param_ranges.keys():
                value = individual[param]
                min_val, max_val = self.param_ranges[param]
                normalized = (value - min_val) / (max_val - min_val)
                features.append(normalized)
            
            # Predict fitness
            X = np.array([features])
            X_scaled = self.scaler.transform(X)
            predicted_fitness = self.ml_model.predict(X_scaled)[0]
            
            # If prediction is good, return the parameters
            if predicted_fitness > np.mean([r.fitness_score for r in self.best_individuals[-10:]]) if self.best_individuals else 50:
                return individual
            
        except Exception as e:
            logger.error(f"Error suggesting parameters: {e}")
        
        return None
    
    async def optimize(self) -> List[OptimizationResult]:
        """Run the complete optimization process"""
        logger.info(f"Starting genetic optimization for {self.max_generations} generations")
        logger.info(f"Target win rate: {self.target_win_rate}%, Min trading frequency: {self.min_trading_frequency}")
        
        # Create initial population
        population = self.create_population()
        
        for generation in range(self.max_generations):
            logger.info(f"Generation {generation + 1}/{self.max_generations}")
            
            # Evaluate population
            results = await self.evaluate_population_parallel(population, generation)
            
            # Store results
            self.population_history.extend(results)
            
            # Find best individuals
            best_results = sorted(results, key=lambda x: x.fitness_score, reverse=True)
            self.best_individuals.extend(best_results[:5])  # Keep top 5
            
            # Calculate population statistics
            stats = self.calculate_population_stats(results, generation)
            self.optimization_log.append(stats)
            
            # Log progress
            logger.info(f"  Best win rate: {stats.best_win_rate:.2f}%")
            logger.info(f"  Avg win rate: {stats.avg_win_rate:.2f}%")
            logger.info(f"  Best fitness: {stats.best_fitness:.2f}")
            logger.info(f"  Best trading freq: {stats.best_trading_freq:.2f}")
            logger.info(f"  Diversity: {stats.diversity_score:.3f}")
            
            # Check for early stopping
            if stats.best_win_rate >= self.target_win_rate and stats.best_trading_freq >= self.min_trading_frequency:
                logger.info(f"Target achieved! Win rate: {stats.best_win_rate:.2f}%, Trading freq: {stats.best_trading_freq:.2f}")
                break
            
            # Train ML model every 10 generations
            if generation % 10 == 0 and generation > 0:
                self.train_ml_model(results)
            
            # Add ML-suggested individuals
            if self.ml_model and generation > 5:
                for _ in range(3):  # Add 3 ML-suggested individuals
                    suggested = self.suggest_parameters()
                    if suggested:
                        population[random.randint(0, len(population) - 1)] = suggested
            
            # Create next generation
            population = self.create_next_generation(results)
            
            # Save progress every 10 generations
            if generation % 10 == 0:
                self.save_progress()
        
        # Final evaluation
        logger.info("Final evaluation...")
        final_results = await self.evaluate_population_parallel(population, self.max_generations)
        self.population_history.extend(final_results)
        
        # Find overall best
        all_results = sorted(self.population_history, key=lambda x: x.fitness_score, reverse=True)
        best_result = all_results[0]
        
        logger.info(f"Optimization completed!")
        logger.info(f"Best win rate: {best_result.win_rate:.2f}%")
        logger.info(f"Best trading frequency: {best_result.trading_frequency:.2f}")
        logger.info(f"Best fitness: {best_result.fitness_score:.2f}")
        
        return all_results
    
    def save_progress(self):
        """Save optimization progress"""
        try:
            # Save best individuals
            best_data = [asdict(result) for result in self.best_individuals[-50:]]  # Last 50
            with open('optimization_best_individuals.json', 'w') as f:
                json.dump(best_data, f, indent=2, default=str)
            
            # Save population stats
            stats_data = [asdict(stat) for stat in self.optimization_log]
            with open('optimization_stats.json', 'w') as f:
                json.dump(stats_data, f, indent=2, default=str)
            
            logger.info("Progress saved")
            
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def load_progress(self):
        """Load previous optimization progress"""
        try:
            # Load best individuals
            if os.path.exists('optimization_best_individuals.json'):
                with open('optimization_best_individuals.json', 'r') as f:
                    data = json.load(f)
                    self.best_individuals = [OptimizationResult(**item) for item in data]
                logger.info(f"Loaded {len(self.best_individuals)} previous best individuals")
            
            # Load stats
            if os.path.exists('optimization_stats.json'):
                with open('optimization_stats.json', 'r') as f:
                    data = json.load(f)
                    self.optimization_log = [PopulationStats(**item) for item in data]
                logger.info(f"Loaded {len(self.optimization_log)} previous generations")
                
        except Exception as e:
            logger.error(f"Error loading progress: {e}")

class ContinuousOptimizer:
    """Main continuous optimization controller"""
    
    def __init__(self):
        self.genetic_optimizer = GeneticOptimizer()
        self.is_running = False
        self.optimization_thread = None
        
    async def start_continuous_optimization(self):
        """Start continuous optimization process"""
        self.is_running = True
        logger.info("Starting continuous optimization...")
        
        # Load previous progress
        self.genetic_optimizer.load_progress()
        
        while self.is_running:
            try:
                # Run optimization cycle
                results = await self.genetic_optimizer.optimize()
                
                # Update configuration with best parameters
                if results:
                    best_result = results[0]
                    self.update_config_with_best(best_result)
                    
                    # Generate report
                    self.generate_optimization_report(results)
                
                # Wait before next cycle (1 hour)
                logger.info("Waiting 1 hour before next optimization cycle...")
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in continuous optimization: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def stop_continuous_optimization(self):
        """Stop continuous optimization"""
        self.is_running = False
        logger.info("Stopping continuous optimization...")
    
    def update_config_with_best(self, best_result: OptimizationResult):
        """Update configuration with best parameters"""
        try:
            # Update .env file
            env_updates = {}
            for param, value in best_result.parameters.items():
                env_updates[param] = value
            
            self.update_env_file('.env', env_updates)
            
            # Update Config class
            for param, value in best_result.parameters.items():
                if hasattr(Config, param):
                    setattr(Config, param, value)
            
            logger.info(f"Updated configuration with best parameters (Win rate: {best_result.win_rate:.2f}%)")
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
    
    def update_env_file(self, path: str, updates: dict):
        """Update .env file with new parameters"""
        lines = []
        existing = {}
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            for line in lines:
                if not line or line.strip().startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                existing[k.strip()] = v
        
        # Apply updates
        for k, v in updates.items():
            existing[k] = str(v)
        
        # Rebuild env content
        new_lines = []
        seen = set()
        for line in lines:
            if not line or line.strip().startswith('#') or '=' not in line:
                new_lines.append(line)
                continue
            k, _, _ = line.partition('=')
            key = k.strip()
            if key in updates:
                new_lines.append(f"{key}={existing[key]}")
                seen.add(key)
            else:
                new_lines.append(line)
        
        for k, v in existing.items():
            if k not in [l.partition('=')[0].strip() for l in new_lines if '=' in l]:
                new_lines.append(f"{k}={v}")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(new_lines) + "\n")
    
    def generate_optimization_report(self, results: List[OptimizationResult]):
        """Generate comprehensive optimization report"""
        try:
            best_result = results[0]
            
            report = f"""
# 🚀 Continuous Optimization Report

## 📊 Current Best Results
- **Win Rate**: {best_result.win_rate:.2f}%
- **Trading Frequency**: {best_result.trading_frequency:.2f} signals/day
- **Total P&L**: ${best_result.total_pnl:.2f}
- **Max Drawdown**: {best_result.max_drawdown:.2f}%
- **Sharpe Ratio**: {best_result.sharpe_ratio:.2f}
- **Profit Factor**: {best_result.profit_factor:.2f}
- **Fitness Score**: {best_result.fitness_score:.2f}

## 🎯 Target Achievement
- **Target Win Rate**: {self.genetic_optimizer.target_win_rate}%
- **Achieved**: {'✅ YES' if best_result.win_rate >= self.genetic_optimizer.target_win_rate else '❌ NO'}
- **Target Trading Frequency**: {self.genetic_optimizer.min_trading_frequency}
- **Achieved**: {'✅ YES' if best_result.trading_frequency >= self.genetic_optimizer.min_trading_frequency else '❌ NO'}

## 🔧 Optimized Parameters
"""
            
            for param, value in best_result.parameters.items():
                report += f"- **{param}**: {value}\n"
            
            report += f"""
## 📈 Optimization Statistics
- **Total Evaluations**: {len(results)}
- **Generations Completed**: {len(self.genetic_optimizer.optimization_log)}
- **Best Win Rate Found**: {max([r.win_rate for r in results]):.2f}%
- **Average Win Rate**: {np.mean([r.win_rate for r in results]):.2f}%
- **Best Trading Frequency**: {max([r.trading_frequency for r in results]):.2f}

## 🎯 Next Steps
"""
            
            if best_result.win_rate < self.genetic_optimizer.target_win_rate:
                report += "- Continue optimization to reach 80%+ win rate\n"
            
            if best_result.trading_frequency < self.genetic_optimizer.min_trading_frequency:
                report += "- Adjust parameters to increase trading frequency\n"
            
            if best_result.max_drawdown > 15:
                report += "- Improve risk management to reduce drawdown\n"
            
            report += f"- Monitor performance and adjust targets as needed\n"
            report += f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Save report
            with open('continuous_optimization_report.md', 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info("Optimization report generated")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")

async def main():
    """Main function to run continuous optimization"""
    optimizer = ContinuousOptimizer()
    
    try:
        await optimizer.start_continuous_optimization()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        optimizer.stop_continuous_optimization()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Continuous optimization stopped")

if __name__ == "__main__":
    asyncio.run(main())
