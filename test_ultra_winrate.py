#!/usr/bin/env python3
"""
Test script for ultra high win rate mode
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.exchange.data_fetcher import ExchangeDataFetcher
from src.strategies.signal_generator import SignalGenerator

async def test_ultra_high_winrate():
    """Test ultra high win rate signal generation"""
    try:
        print("🚀 Testing Ultra High Win Rate Mode...")
        
        # Initialize components
        exchange_fetcher = ExchangeDataFetcher()
        signal_generator = SignalGenerator()
        
        # Test symbols
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
        
        print(f"📊 Testing {len(symbols)} symbols...")
        
        total_signals = 0
        high_confidence_signals = 0
        
        for symbol in symbols:
            try:
                print(f"\n🔍 Analyzing {symbol}...")
                
                # Get 5m data
                df = await exchange_fetcher.get_ohlcv_data(symbol, '5m', limit=200)
                
                if df is None or len(df) < 200:
                    print(f"❌ Insufficient data for {symbol}")
                    continue
                
                # Generate signal
                signal = signal_generator.generate_signal(symbol, df, exchange_fetcher)
                
                if signal:
                    total_signals += 1
                    confidence = signal['confidence']
                    
                    if confidence >= 0.95:
                        high_confidence_signals += 1
                        print(f"✅ HIGH CONFIDENCE SIGNAL: {signal['direction']} - {confidence:.2f}")
                        print(f"   Entry: ${signal['entry_price']:.4f}")
                        print(f"   Stop Loss: ${signal['stop_loss']:.4f}")
                        print(f"   Take Profit: ${signal['take_profit']:.4f}")
                        print(f"   R:R: {signal['risk_reward']:.2f}")
                        
                        if 'confirmation_conditions' in signal:
                            print(f"   Multi-timeframe confirmed: {len(signal['confirmation_conditions'])} conditions")
                    else:
                        print(f"⚠️  Low confidence signal: {signal['direction']} - {confidence:.2f}")
                else:
                    print(f"❌ No signal generated for {symbol}")
                    
            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                continue
        
        print(f"\n📊 Results Summary:")
        print(f"   Total signals: {total_signals}")
        print(f"   High confidence (≥95%): {high_confidence_signals}")
        print(f"   High confidence rate: {(high_confidence_signals/total_signals*100):.1f}%" if total_signals > 0 else "   High confidence rate: 0%")
        
        # Close connections
        exchange_fetcher.close()
        
        print("\n✅ Ultra High Win Rate test completed!")
        
    except Exception as e:
        print(f"❌ Error in ultra high win rate test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_ultra_high_winrate())
