#!/usr/bin/env python3
"""
Parameter optimizer to target >80% win rate via backtests.

Runs randomized sweeps over key config parameters and evaluates
win rate using the built-in Backtester. Persists the best set
to `.env` and writes a markdown summary.
"""
import os
import sys
import json
import argparse
import random
import asyncio
from datetime import datetime, timedelta

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.backtesting.backtester import Backtester


def set_params(params: dict):
    """Apply parameters to Config class variables for this process."""
    for k, v in params.items():
        if hasattr(Config, k):
            setattr(Config, k, v)


def sample_params() -> dict:
    """Randomly sample a parameter set within sensible ranges."""
    rsi_oversold = random.randint(30, 42)
    rsi_overbought = random.randint(58, 70)
    # Ensure some gap and validity
    if rsi_overbought - rsi_oversold < 20:
        rsi_overbought = rsi_oversold + 20
        rsi_overbought = min(rsi_overbought, 75)

    params = {
        # Trade entry strictness
        'CONFIDENCE_THRESHOLD': round(random.uniform(0.80, 0.96), 2),
        'ULTRA_MIN_CONFIDENCE': round(random.uniform(0.90, 0.99), 2),
        # RSI band
        'RSI_OVERSOLD': rsi_oversold,
        'RSI_OVERBOUGHT': rsi_overbought,
        # Risk:Reward tuning for momentum/mean-reversion (and SL guardrails)
        'STOP_LOSS_ATR_MULTIPLIER': round(random.uniform(1.2, 2.5), 2),
        'TAKE_PROFIT_ATR_MULTIPLIER': round(random.uniform(1.0, 2.4), 2),
        # Ultra filters
        'MIN_VOLUME_RATIO': round(random.uniform(1.1, 2.5), 2),
        'MIN_ATR_RATIO': round(random.uniform(1.0, 2.0), 2),
        'MIN_TREND_STRENGTH': int(random.uniform(20, 45)),
        'MIN_MOMENTUM_CONSISTENCY': int(random.uniform(2, 5)),
        # Trading hours (UTC window)
        'TRADING_HOURS_START': int(random.choice([10, 11, 12, 13])),
        'TRADING_HOURS_END': int(random.choice([15, 16, 17, 18])),
    }
    return params


async def run_once(days: int) -> dict:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    backtester = Backtester(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    result = await backtester.run_backtest()
    backtester.close()
    # Clean non-serializable fields (e.g., validation_result object)
    d = dict(result.__dict__)
    if 'validation_result' in d:
        vr = d.pop('validation_result')
        try:
            # Add a compact summary if available
            d['validation_summary'] = {
                'is_valid': getattr(vr, 'is_valid', None),
                'overall_score': getattr(vr, 'overall_score', None),
                'issues_count': len(getattr(vr, 'issues', []) or []),
            }
        except Exception:
            pass
    return d


def update_env_file(path: str, updates: dict):
    """Update specific keys in a .env file, preserving others."""
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

    # Rebuild env content preserving comments/newlines at top
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


def save_results_md(path: str, best: dict, history: list):
    lines = []
    lines.append(f"# Win Rate Optimization Results\n")
    lines.append(f"- Timestamp: {datetime.now().isoformat(timespec='seconds')}\n")
    lines.append(f"- Best Win Rate: {best['result']['win_rate']:.2f}%\n")
    lines.append(f"- Best Total Signals: {best['result']['total_signals']}\n")
    lines.append(f"- Best Params: {json.dumps(best['params'], ensure_ascii=False)}\n")
    lines.append("\n## Search History (top 10 by win rate)\n")
    ranked = sorted(history, key=lambda x: x['result']['win_rate'], reverse=True)[:10]
    for i, item in enumerate(ranked, 1):
        lines.append(f"{i}. {item['result']['win_rate']:.2f}% WR | trades={item['result']['total_signals']} | params={json.dumps(item['params'])}")
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")


async def main():
    parser = argparse.ArgumentParser(description='Optimize parameters to target >80% win rate via backtests')
    parser.add_argument('--iterations', type=int, default=12, help='Number of random trials')
    parser.add_argument('--days', type=int, default=30, help='Backtest lookback window in days')
    parser.add_argument('--target', type=float, default=80.0, help='Target win rate')
    parser.add_argument('--min-trades', type=int, default=10, help='Minimum trades to consider a result valid')
    parser.add_argument('--env', default='.env', help='Path to .env to update with best params')
    # Constraints
    parser.add_argument('--max-drawdown', type=float, default=30.0, help='Max allowed drawdown (%)')
    parser.add_argument('--min-profit-factor', type=float, default=0.9, help='Min allowed profit factor')
    parser.add_argument('--min-sharpe', type=float, default=0.2, help='Min allowed Sharpe ratio')
    args = parser.parse_args()

    history = []
    best = None

    for i in range(1, args.iterations + 1):
        params = sample_params()
        set_params(params)

        print(f"[Trial {i}/{args.iterations}] params={params}")
        try:
            result = await run_once(args.days)
        except Exception as e:
            print(f"  -> error: {e}")
            continue

        print(f"  -> win_rate={result['win_rate']:.2f}% | trades={result['total_signals']} | pnl=${result['total_pnl']:.2f} | pf={result.get('profit_factor', 0):.2f} | dd={result.get('max_drawdown', 0):.2f}% | sharpe={result.get('sharpe_ratio', 0):.2f}")
        row = {'params': params, 'result': result}
        history.append(row)

        # Constraints check
        meets_trades = result['total_signals'] >= args.min_trades
        meets_dd = result.get('max_drawdown', 1000) <= args.max_drawdown
        meets_pf = result.get('profit_factor', 0) >= args.min_profit_factor
        meets_sharpe = result.get('sharpe_ratio', 0) >= args.min_sharpe
        eligible = meets_trades and meets_dd and meets_pf and meets_sharpe

        # Track best respecting constraints; tie-break by WR, then trades, then PF, then drawdown
        def is_better(a, b):
            if b is None:
                return True
            ra, rb = a['result'], b['result']
            keys = ['win_rate', 'total_signals', 'profit_factor']
            # higher is better for first three
            for k in keys:
                if ra.get(k, 0) != rb.get(k, 0):
                    return ra.get(k, 0) > rb.get(k, 0)
            # lower drawdown last
            return ra.get('max_drawdown', 1e9) < rb.get('max_drawdown', 1e9)

        if eligible and is_better(row, best):
            best = row

        # Early stop if target hit with enough trades and constraints
        if (result['win_rate'] >= args.target and eligible):
            print("  -> target achieved; stopping early.")
            break

    if not best:
        # Fallback to best by win rate even if below min trades
        if history:
            best = sorted(history, key=lambda x: x['result']['win_rate'], reverse=True)[0]
        else:
            print("No successful backtests completed.")
            sys.exit(1)

    # Persist best params to .env
    updates = {
        'CONFIDENCE_THRESHOLD': best['params']['CONFIDENCE_THRESHOLD'],
        'ULTRA_MIN_CONFIDENCE': best['params']['ULTRA_MIN_CONFIDENCE'],
        'RSI_OVERSOLD': best['params']['RSI_OVERSOLD'],
        'RSI_OVERBOUGHT': best['params']['RSI_OVERBOUGHT'],
        'STOP_LOSS_ATR_MULTIPLIER': best['params']['STOP_LOSS_ATR_MULTIPLIER'],
        'TAKE_PROFIT_ATR_MULTIPLIER': best['params']['TAKE_PROFIT_ATR_MULTIPLIER'],
        'MIN_VOLUME_RATIO': best['params']['MIN_VOLUME_RATIO'],
        'MIN_ATR_RATIO': best['params']['MIN_ATR_RATIO'],
        'MIN_TREND_STRENGTH': best['params']['MIN_TREND_STRENGTH'],
        'MIN_MOMENTUM_CONSISTENCY': best['params']['MIN_MOMENTUM_CONSISTENCY'],
        'TRADING_HOURS_START': best['params']['TRADING_HOURS_START'],
        'TRADING_HOURS_END': best['params']['TRADING_HOURS_END'],
    }
    update_env_file(args.env, updates)

    # Save results
    with open('optimization_results.json', 'w', encoding='utf-8') as f:
        json.dump({'best': best, 'history': history}, f, indent=2)
    save_results_md('WINRATE_OPTIMIZATION_REPORT.md', best, history)

    print("\nBest result:")
    print(json.dumps(best, indent=2))
    print(f"\nUpdated {args.env} with best parameters.")


if __name__ == '__main__':
    asyncio.run(main())
