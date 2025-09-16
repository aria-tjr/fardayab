#!/usr/bin/env python3
"""
Debug Signal Generation
Find out why signals are not being generated
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategies.signal_generator import SignalGenerator
from src.config import Config

def create_debug_data(symbol: str = 'BTC/USDT') -> pd.DataFrame:
    """Create data with known signal patterns"""
    periods = 500
    dates = pd.date_range(start=datetime.now() - timedelta(hours=periods//12), 
                         periods=periods, freq='5min')
    
    base_price = 43000
    
    # Create trending data that should generate signals
    data = []
    for i in range(periods):
        # Create uptrend in first half, downtrend in second half
        if i < periods // 2:
            trend = 0.0005  # Uptrend
        else:
            trend = -0.0005  # Downtrend
        
        # Base price with trend
        price = base_price * (1 + trend * i + np.random.normal(0, 0.001))
        
        # Create realistic OHLC
        volatility = price * 0.002
        open_price = data[-1]['close'] if data else price
        close_price = price
        high_price = max(open_price, close_price) + np.random.uniform(0, volatility)
        low_price = min(open_price, close_price) - np.random.uniform(0, volatility)
        
        # High volume to pass filters
        volume = np.random.uniform(8000000, 12000000)
        
        data.append({
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    return pd.DataFrame(data, index=dates)

def debug_signal_conditions(df: pd.DataFrame, index: int) -> dict:
    """Debug why signal conditions are not met"""
    signal_gen = SignalGenerator()
    
    # Get data up to current point
    current_data = df.iloc[:index+1]
    
    if len(current_data) < 200:
        return {'error': 'Not enough data for indicators'}
    
    try:
        # Calculate indicators manually
        indicators = signal_gen.calculate_indicators(current_data)
        
        # Get current values
        current_price = current_data['close'].iloc[-1]
        ema21 = indicators['ema_21'].iloc[-1]
        ema50 = indicators['ema_50'].iloc[-1] 
        ema200 = indicators['ema_200'].iloc[-1]
        rsi = indicators['rsi'].iloc[-1]
        donchian_upper = indicators['donchian_upper'].iloc[-1]
        donchian_lower = indicators['donchian_lower'].iloc[-1]
        volume = current_data['volume'].iloc[-1]
        volume_ma = indicators['volume_ma_20'].iloc[-1]
        
        # Check LONG conditions
        long_conditions = []
        long_conditions.append(f"Price vs EMA200: {current_price:.2f} > {ema200:.2f} = {current_price > ema200}")
        long_conditions.append(f"EMA21 vs EMA50: {ema21:.2f} > {ema50:.2f} = {ema21 > ema50}")
        long_conditions.append(f"RSI vs {Config.TREND_RSI_LONG_MIN}: {rsi:.1f} > {Config.TREND_RSI_LONG_MIN} = {rsi > Config.TREND_RSI_LONG_MIN}")
        long_conditions.append(f"Donchian breakout: {current_price:.2f} >= {donchian_upper:.2f} = {current_price >= donchian_upper * 0.999}")
        long_conditions.append(f"Volume filter: {volume:.0f} > {volume_ma * Config.MIN_VOLUME_RATIO:.0f} = {volume > volume_ma * Config.MIN_VOLUME_RATIO}")
        
        # Check SHORT conditions
        short_conditions = []
        short_conditions.append(f"Price vs EMA200: {current_price:.2f} < {ema200:.2f} = {current_price < ema200}")
        short_conditions.append(f"EMA21 vs EMA50: {ema21:.2f} < {ema50:.2f} = {ema21 < ema50}")
        short_conditions.append(f"RSI vs {Config.TREND_RSI_SHORT_MAX}: {rsi:.1f} < {Config.TREND_RSI_SHORT_MAX} = {rsi < Config.TREND_RSI_SHORT_MAX}")
        short_conditions.append(f"Donchian breakdown: {current_price:.2f} <= {donchian_lower:.2f} = {current_price <= donchian_lower * 1.001}")
        short_conditions.append(f"Volume filter: {volume:.0f} > {volume_ma * Config.MIN_VOLUME_RATIO:.0f} = {volume > volume_ma * Config.MIN_VOLUME_RATIO}")
        
        # Count met conditions
        long_met = sum([
            current_price > ema200,
            ema21 > ema50,
            rsi > Config.TREND_RSI_LONG_MIN,
            current_price >= donchian_upper * 0.999,
            volume > volume_ma * Config.MIN_VOLUME_RATIO
        ])
        
        short_met = sum([
            current_price < ema200,
            ema21 < ema50,
            rsi < Config.TREND_RSI_SHORT_MAX,
            current_price <= donchian_lower * 1.001,
            volume > volume_ma * Config.MIN_VOLUME_RATIO
        ])
        
        return {
            'timestamp': current_data.index[-1],
            'price': current_price,
            'rsi': rsi,
            'long_conditions_met': long_met,
            'short_conditions_met': short_met,
            'long_conditions': long_conditions,
            'short_conditions': short_conditions,
            'confidence_threshold': Config.CONFIDENCE_THRESHOLD,
            'min_conditions_needed': 3
        }
        
    except Exception as e:
        return {'error': f'Error calculating indicators: {e}'}

def main():
    """Debug signal generation"""
    print("🔍 SIGNAL GENERATION DEBUG")
    print("=" * 50)
    
    # Show current config
    print(f"📋 Current Configuration:")
    print(f"   CONFIDENCE_THRESHOLD: {Config.CONFIDENCE_THRESHOLD}")
    print(f"   TREND_RSI_LONG_MIN: {Config.TREND_RSI_LONG_MIN}")
    print(f"   TREND_RSI_SHORT_MAX: {Config.TREND_RSI_SHORT_MAX}")
    print(f"   MIN_VOLUME_RATIO: {Config.MIN_VOLUME_RATIO}")
    
    # Create test data
    df = create_debug_data()
    signal_gen = SignalGenerator()
    
    print(f"\n📊 Testing with {len(df)} data points...")
    
    # Test signal generation at different points
    test_points = [250, 300, 350, 400, 450]
    
    for i, point in enumerate(test_points):
        print(f"\n🔍 Debug Point {i+1} (Index {point}):")
        print("-" * 30)
        
        # Debug conditions
        debug_info = debug_signal_conditions(df, point)
        
        if 'error' in debug_info:
            print(f"❌ {debug_info['error']}")
            continue
        
        print(f"📅 Time: {debug_info['timestamp']}")
        print(f"💰 Price: ${debug_info['price']:.2f}")
        print(f"📈 RSI: {debug_info['rsi']:.1f}")
        
        print(f"\n🟢 LONG Conditions ({debug_info['long_conditions_met']}/5 met):")
        for condition in debug_info['long_conditions']:
            print(f"   {condition}")
        
        print(f"\n🔴 SHORT Conditions ({debug_info['short_conditions_met']}/5 met):")
        for condition in debug_info['short_conditions']:
            print(f"   {condition}")
        
        # Try to generate actual signal
        current_data = df.iloc[:point+1]
        try:
            signal = signal_gen.generate_signal('BTC/USDT', current_data)
            if signal:
                print(f"\n✅ SIGNAL GENERATED:")
                print(f"   Direction: {signal['direction']}")
                print(f"   Type: {signal['type']}")
                print(f"   Confidence: {signal['confidence']:.3f}")
                print(f"   Conditions: {len(signal.get('conditions_met', []))}")
            else:
                print(f"\n❌ NO SIGNAL GENERATED")
                if debug_info['long_conditions_met'] >= 3:
                    print(f"   LONG conditions met but confidence too low?")
                if debug_info['short_conditions_met'] >= 3:
                    print(f"   SHORT conditions met but confidence too low?")
        except Exception as e:
            print(f"\n❌ Error generating signal: {e}")
    
    # Test with relaxed thresholds
    print(f"\n🔧 TESTING WITH RELAXED THRESHOLDS:")
    print("=" * 40)
    
    # Save original values
    original_confidence = Config.CONFIDENCE_THRESHOLD
    original_volume_ratio = Config.MIN_VOLUME_RATIO
    
    # Set more permissive thresholds
    Config.CONFIDENCE_THRESHOLD = 0.4
    Config.MIN_VOLUME_RATIO = 1.0
    
    signals_found = 0
    
    for point in range(220, len(df) - 10, 20):
        current_data = df.iloc[:point+1]
        try:
            signal = signal_gen.generate_signal('BTC/USDT', current_data)
            if signal:
                signals_found += 1
                print(f"✅ Signal {signals_found} at index {point}:")
                print(f"   Direction: {signal['direction']}")
                print(f"   Confidence: {signal['confidence']:.3f}")
                print(f"   Type: {signal['type']}")
                
                if signals_found >= 5:  # Limit output
                    break
        except Exception as e:
            continue
    
    # Restore original values
    Config.CONFIDENCE_THRESHOLD = original_confidence
    Config.MIN_VOLUME_RATIO = original_volume_ratio
    
    if signals_found == 0:
        print("❌ Still no signals with relaxed thresholds")
        
        # Check if filters are working
        print(f"\n🔍 CHECKING FILTERS:")
        test_data = df.iloc[:300]
        try:
            indicators = signal_gen.calculate_indicators(test_data)
            filters_passed = signal_gen.apply_filters(test_data, indicators)
            print(f"   Filters passed: {filters_passed}")
            
            if not filters_passed:
                print("   ❌ Data not passing basic filters")
                
                # Check individual filter components
                current_volume = test_data['volume'].iloc[-1]
                volume_ma = indicators['volume_ma_20'].iloc[-1]
                current_atr = indicators['atr'].iloc[-1]
                atr_ma = indicators['atr_ma_20'].iloc[-1]
                current_hour = datetime.now().hour
                
                print(f"   Volume check: {current_volume:.0f} vs {volume_ma * Config.MIN_VOLUME_RATIO:.0f}")
                print(f"   ATR check: {current_atr:.4f} vs {atr_ma * Config.MIN_ATR_RATIO:.4f}")
                print(f"   Time check: {current_hour} in range {Config.TRADING_HOURS_START}-{Config.TRADING_HOURS_END}")
                
        except Exception as e:
            print(f"   ❌ Error checking filters: {e}")
    else:
        print(f"✅ Found {signals_found} signals with relaxed thresholds")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 30)
    
    if signals_found == 0:
        print("• The signal generation logic may be too strict")
        print("• Consider lowering CONFIDENCE_THRESHOLD to 0.4-0.5")
        print("• Consider relaxing volume filters")
        print("• Check if trading hours filter is too restrictive")
        print("• Verify indicator calculations are correct")
    else:
        print("• Signals can be generated with relaxed thresholds")
        print("• Current thresholds may be too conservative")
        print("• Consider gradual threshold reduction")
    
    return signals_found

if __name__ == "__main__":
    main()
