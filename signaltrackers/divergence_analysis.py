#!/usr/bin/env python3
"""
Market Divergence Analysis

Analyzes the historic market divergence between credit, equity, gold, and crypto markets.
Calculates crisis warning scores and tracks resolution of unprecedented market conditions.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


class DivergenceAnalyzer:
    """Analyzes market divergences and calculates crisis scores."""

    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)

    def load_file(self, filename):
        """Load a CSV file and return DataFrame."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            return None
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def get_latest_value(self, df, column=None):
        """Get the latest value from a DataFrame."""
        if df is None or df.empty:
            return None
        if column is None:
            column = df.columns[1]
        return df.iloc[-1][column]

    def calculate_gold_implied_credit_spread(self, gold_price):
        """
        Calculate what credit spreads SHOULD be based on gold price.

        Historical relationships:
        - Gold ~$1,500 → HY spread ~300-400 bp
        - Gold ~$2,000 → HY spread ~400-600 bp (COVID)
        - Gold ~$2,500 → HY spread ~500-800 bp
        - Gold ~$3,000 → HY spread ~800-1200 bp
        - Gold ~$4,500 → HY spread ~1200-1500 bp (structural crisis)

        Formula: Implied spread = base_spread * (gold_price / base_gold_price)^1.5
        """
        base_gold = 2000  # Base gold price
        base_spread = 400  # Base HY spread in bp at $2000 gold

        if gold_price is None:
            return None

        # Exponential relationship - gold rising faster = bigger crisis signal
        implied_spread = base_spread * ((gold_price / base_gold) ** 1.5)

        return implied_spread

    def calculate_crisis_score(self, metrics):
        """
        Calculate overall crisis warning score (0-100).

        Higher score = more warning signals flashing.
        """
        score = 0
        warnings = []

        # Credit spread warnings (0-25 points)
        if metrics.get('hy_spread'):
            hy = metrics['hy_spread']
            if hy < 250:
                score += 15
                warnings.append("HY spreads extremely tight (<250 bp)")
            elif hy < 300:
                score += 10
                warnings.append("HY spreads very tight (<300 bp)")
            elif hy > 600:
                score += 5
                warnings.append("HY spreads elevated (>600 bp)")

            if metrics.get('ig_spread'):
                ig = metrics['ig_spread']
                if ig < 80:
                    score += 10
                    warnings.append("IG spreads extremely tight (<80 bp)")

        # Gold warnings (0-25 points)
        if metrics.get('gold_price'):
            gold = metrics['gold_price']
            if gold > 4500:
                score += 25
                warnings.append("Gold at EXTREME levels (>$4500) - major crisis signal")
            elif gold > 4000:
                score += 20
                warnings.append("Gold very elevated (>$4000)")
            elif gold > 3500:
                score += 15
                warnings.append("Gold elevated (>$3500)")
            elif gold > 3000:
                score += 10
                warnings.append("Gold high (>$3000)")

        # Divergence warnings (0-25 points)
        if metrics.get('divergence_gap'):
            gap = metrics['divergence_gap']
            if gap > 800:
                score += 25
                warnings.append(f"EXTREME divergence gap: {gap:.0f} bp - unprecedented")
            elif gap > 600:
                score += 20
                warnings.append(f"Very large divergence gap: {gap:.0f} bp")
            elif gap > 400:
                score += 15
                warnings.append(f"Large divergence gap: {gap:.0f} bp")
            elif gap > 200:
                score += 10
                warnings.append(f"Moderate divergence gap: {gap:.0f} bp")

        # Market structure warnings (0-15 points)
        if metrics.get('breadth_ratio'):
            breadth = metrics['breadth_ratio']
            # Lower breadth = more concentrated/dangerous
            if breadth < 95:
                score += 10
                warnings.append("Market breadth weak - narrow rally")
            elif breadth < 98:
                score += 5
                warnings.append("Market breadth deteriorating")

        # Volatility warnings (0-10 points)
        if metrics.get('vix'):
            vix = metrics['vix']
            if vix > 30:
                score += 10
                warnings.append("VIX elevated - fear rising")
            elif vix > 25:
                score += 5
                warnings.append("VIX moderately elevated")
            elif vix < 15 and score > 30:
                # Low VIX with other warnings = complacency
                score += 5
                warnings.append("VIX low despite other warnings - complacency")

        # Bitcoin warnings (0-10 points)
        if metrics.get('bitcoin_price'):
            btc = metrics['bitcoin_price']
            btc_30d_change = metrics.get('bitcoin_30d_change', 0)

            # Bitcoin down while gold up = liquidity warning
            gold_30d_change = metrics.get('gold_30d_change', 0)
            if btc_30d_change < -10 and gold_30d_change > 5:
                score += 10
                warnings.append("Bitcoin weak while gold strong - liquidity tight")
            elif btc_30d_change < -5:
                score += 5
                warnings.append("Bitcoin weakness - risk-off in crypto")

        return min(score, 100), warnings

    def calculate_percentile(self, df, value, column):
        """Calculate what percentile a value is in historical data."""
        if df is None or value is None:
            return None
        values = df[column].dropna()
        percentile = (values < value).sum() / len(values) * 100
        return percentile

    def analyze_all_metrics(self):
        """Load all data and calculate comprehensive metrics."""

        metrics = {}

        # Load credit spreads
        hy_df = self.load_file('high_yield_spread.csv')
        ig_df = self.load_file('investment_grade_spread.csv')
        ccc_df = self.load_file('ccc_spread.csv')

        if hy_df is not None:
            metrics['hy_spread'] = self.get_latest_value(hy_df) * 100  # Convert to bp
            metrics['hy_spread_30d_change'] = (hy_df.iloc[-1][hy_df.columns[1]] -
                                               hy_df.iloc[max(0, len(hy_df)-21)][hy_df.columns[1]]) * 100
            metrics['hy_percentile'] = self.calculate_percentile(hy_df, hy_df.iloc[-1][hy_df.columns[1]], hy_df.columns[1])

        if ig_df is not None:
            metrics['ig_spread'] = self.get_latest_value(ig_df) * 100
            metrics['ig_spread_30d_change'] = (ig_df.iloc[-1][ig_df.columns[1]] -
                                               ig_df.iloc[max(0, len(ig_df)-21)][ig_df.columns[1]]) * 100

        if ccc_df is not None:
            metrics['ccc_spread'] = self.get_latest_value(ccc_df) * 100
            if metrics.get('hy_spread'):
                metrics['ccc_hy_ratio'] = metrics['ccc_spread'] / metrics['hy_spread']

        # Load equity data
        spy_df = self.load_file('sp500_price.csv')
        rsp_df = self.load_file('sp500_equal_weight_price.csv')
        iwm_df = self.load_file('small_cap_price.csv')
        qqq_df = self.load_file('nasdaq_price.csv')

        if spy_df is not None:
            metrics['sp500_price'] = self.get_latest_value(spy_df)
            if len(spy_df) > 20:
                metrics['sp500_30d_change'] = ((spy_df.iloc[-1][spy_df.columns[1]] /
                                                spy_df.iloc[-21][spy_df.columns[1]]) - 1) * 100

        # Market breadth
        breadth_df = self.load_file('market_breadth_ratio.csv')
        if breadth_df is not None:
            metrics['breadth_ratio'] = self.get_latest_value(breadth_df)

        # Gold
        gold_df = self.load_file('gold_price.csv')
        if gold_df is not None:
            # Gold ETF (GLD) trades at ~1/10th spot price
            metrics['gold_price'] = self.get_latest_value(gold_df) * 10  # Approximate spot
            if len(gold_df) > 20:
                metrics['gold_30d_change'] = ((gold_df.iloc[-1][gold_df.columns[1]] /
                                               gold_df.iloc[-21][gold_df.columns[1]]) - 1) * 100

            # Calculate implied credit spread
            metrics['gold_implied_spread'] = self.calculate_gold_implied_credit_spread(metrics['gold_price'])

            # Calculate divergence gap
            if metrics.get('hy_spread') and metrics.get('gold_implied_spread'):
                metrics['divergence_gap'] = metrics['gold_implied_spread'] - metrics['hy_spread']

        # Bitcoin
        btc_df = self.load_file('bitcoin_price.csv')
        if btc_df is not None:
            metrics['bitcoin_price'] = self.get_latest_value(btc_df)
            if len(btc_df) > 20:
                metrics['bitcoin_30d_change'] = ((btc_df.iloc[-1][btc_df.columns[1]] /
                                                  btc_df.iloc[-21][btc_df.columns[1]]) - 1) * 100

        # VIX
        vix_df = self.load_file('vix_price.csv')
        if vix_df is not None:
            metrics['vix'] = self.get_latest_value(vix_df)

        # Dollar
        dollar_df = self.load_file('dollar_index_price.csv')
        if dollar_df is not None:
            metrics['dollar_price'] = self.get_latest_value(dollar_df)

        return metrics

    def print_comprehensive_analysis(self):
        """Print comprehensive divergence analysis."""

        metrics = self.analyze_all_metrics()

        # Calculate crisis score
        crisis_score, warnings = self.calculate_crisis_score(metrics)

        print("\n" + "="*80)
        print("MARKET DIVERGENCE ANALYSIS")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # Crisis Score
        print(f"\n{'='*80}")
        print(f"CRISIS WARNING SCORE: {crisis_score}/100")
        print("="*80)

        if crisis_score >= 75:
            status = "🔴 EXTREME WARNING - Multiple severe stress signals"
        elif crisis_score >= 60:
            status = "🟠 HIGH WARNING - Significant divergences detected"
        elif crisis_score >= 40:
            status = "🟡 MODERATE WARNING - Notable concerns present"
        elif crisis_score >= 20:
            status = "🟢 LOW WARNING - Minor stress signals"
        else:
            status = "⚫ NORMAL - No significant warnings"

        print(f"\nStatus: {status}\n")

        if warnings:
            print("Active Warnings:")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")

        # Credit Markets
        print(f"\n{'='*80}")
        print("CREDIT MARKETS")
        print("="*80)

        if metrics.get('hy_spread'):
            print(f"\nHigh-Yield Spread: {metrics['hy_spread']:.0f} bp")
            if metrics.get('hy_spread_30d_change'):
                change_arrow = "↑" if metrics['hy_spread_30d_change'] > 0 else "↓"
                print(f"  30-day change: {change_arrow} {abs(metrics['hy_spread_30d_change']):.0f} bp")
            if metrics.get('hy_percentile'):
                print(f"  Historical percentile: {metrics['hy_percentile']:.1f}%")

            assessment = ""
            if metrics['hy_spread'] < 250:
                assessment = "EXTREMELY TIGHT - Late cycle / complacency"
            elif metrics['hy_spread'] < 350:
                assessment = "Very tight - Low default risk priced"
            elif metrics['hy_spread'] < 500:
                assessment = "Moderate - Normal conditions"
            elif metrics['hy_spread'] < 800:
                assessment = "Elevated - Stress building"
            else:
                assessment = "VERY WIDE - Crisis conditions"
            print(f"  Assessment: {assessment}")

        if metrics.get('ig_spread'):
            print(f"\nInvestment Grade Spread: {metrics['ig_spread']:.0f} bp")
            if metrics.get('ig_spread_30d_change'):
                change_arrow = "↑" if metrics['ig_spread_30d_change'] > 0 else "↓"
                print(f"  30-day change: {change_arrow} {abs(metrics['ig_spread_30d_change']):.0f} bp")

        if metrics.get('ccc_spread'):
            print(f"\nCCC-Rated Spread: {metrics['ccc_spread']:.0f} bp")
            if metrics.get('ccc_hy_ratio'):
                print(f"  CCC/HY Ratio: {metrics['ccc_hy_ratio']:.2f}x")
                if metrics['ccc_hy_ratio'] > 3.5:
                    print(f"    ⚠️  Distressed credits significantly lagging")
                elif metrics['ccc_hy_ratio'] > 3.0:
                    print(f"    → Distressed credits lagging somewhat")

        # Gold & Divergence
        print(f"\n{'='*80}")
        print("GOLD & DIVERGENCE ANALYSIS")
        print("="*80)

        if metrics.get('gold_price'):
            print(f"\nGold Price: ${metrics['gold_price']:.0f}")
            if metrics.get('gold_30d_change'):
                change_arrow = "↑" if metrics['gold_30d_change'] > 0 else "↓"
                print(f"  30-day change: {change_arrow} {abs(metrics['gold_30d_change']):.1f}%")

            print(f"\n  Gold-Implied HY Spread: {metrics.get('gold_implied_spread', 0):.0f} bp")
            print(f"  Actual HY Spread: {metrics.get('hy_spread', 0):.0f} bp")

            if metrics.get('divergence_gap'):
                print(f"\n  ⚠️  DIVERGENCE GAP: {metrics['divergence_gap']:.0f} bp")
                print(f"  {'-'*76}")
                print(f"  Gold is pricing {metrics['divergence_gap']:.0f} bp MORE stress than credit markets")

                if metrics['divergence_gap'] > 800:
                    print(f"  🔴 UNPRECEDENTED DIVERGENCE - One market is catastrophically wrong")
                elif metrics['divergence_gap'] > 600:
                    print(f"  🟠 EXTREME DIVERGENCE - Major disconnection between markets")
                elif metrics['divergence_gap'] > 400:
                    print(f"  🟡 LARGE DIVERGENCE - Significant market disagreement")
                elif metrics['divergence_gap'] > 200:
                    print(f"  🟢 MODERATE DIVERGENCE - Some disagreement present")

        # Equity Markets
        print(f"\n{'='*80}")
        print("EQUITY MARKETS & BREADTH")
        print("="*80)

        if metrics.get('sp500_price'):
            print(f"\nS&P 500: ${metrics['sp500_price']:.2f}")
            if metrics.get('sp500_30d_change'):
                change_arrow = "↑" if metrics['sp500_30d_change'] > 0 else "↓"
                print(f"  30-day change: {change_arrow} {abs(metrics['sp500_30d_change']):.1f}%")

        if metrics.get('breadth_ratio'):
            print(f"\nMarket Breadth (RSP/SPY): {metrics['breadth_ratio']:.2f}")
            if metrics['breadth_ratio'] < 95:
                print(f"  🔴 Very narrow rally - concentration risk extreme")
            elif metrics['breadth_ratio'] < 98:
                print(f"  🟡 Narrow rally - large caps outperforming significantly")
            else:
                print(f"  🟢 Healthy breadth - broad participation")

        if metrics.get('vix'):
            print(f"\nVIX: {metrics['vix']:.2f}")
            if metrics['vix'] > 30:
                print(f"  🔴 Elevated fear - market stress")
            elif metrics['vix'] > 20:
                print(f"  🟡 Moderate fear - uncertainty present")
            elif metrics['vix'] < 15:
                if crisis_score > 40:
                    print(f"  ⚠️  Low fear despite other warnings - COMPLACENCY")
                else:
                    print(f"  🟢 Low fear - calm markets")

        # Bitcoin & Liquidity
        print(f"\n{'='*80}")
        print("BITCOIN & LIQUIDITY SIGNALS")
        print("="*80)

        if metrics.get('bitcoin_price'):
            print(f"\nBitcoin: ${metrics['bitcoin_price']:,.2f}")
            if metrics.get('bitcoin_30d_change'):
                change_arrow = "↑" if metrics['bitcoin_30d_change'] > 0 else "↓"
                print(f"  30-day change: {change_arrow} {abs(metrics['bitcoin_30d_change']):.1f}%")

            # Bitcoin vs Gold analysis
            if metrics.get('gold_30d_change'):
                if metrics['bitcoin_30d_change'] < -5 and metrics['gold_30d_change'] > 5:
                    print(f"\n  🔴 Bitcoin falling while gold rising:")
                    print(f"     - Suggests liquidity tight despite safe-haven demand")
                    print(f"     - 'Digital gold' narrative not working")
                    print(f"     - Risk-off in speculative assets")
                elif metrics['bitcoin_30d_change'] > 10 and metrics['gold_30d_change'] > 5:
                    print(f"\n  🟡 Both Bitcoin and gold rising:")
                    print(f"     - Debasement fears + risk appetite")
                    print(f"     - Mixed signals")

        # Summary & Outlook
        print(f"\n{'='*80}")
        print("INTERPRETATION & OUTLOOK")
        print("="*80)

        print(f"\nWhat This Setup Means:\n")

        # Determine market regime
        gold_high = metrics.get('gold_price', 0) > 4000
        credit_tight = metrics.get('hy_spread', 1000) < 350
        btc_weak = metrics.get('bitcoin_30d_change', 0) < -5

        if gold_high and credit_tight:
            print("  🔴 EXTREME DIVERGENCE REGIME")
            print("     • Gold pricing major structural crisis")
            print("     • Credit markets in denial or lagging")
            print("     • Historic setup with NO clear precedent")
            print("     • One of these markets will be proven catastrophically wrong\n")

            print("  Most Likely Resolution:")
            print("     1. Credit spreads widen significantly (6-18 months)")
            print("     2. Gold validates at higher levels or consolidates")
            print("     3. Economic slowdown or crisis emerges")
            print("     4. Timeline: Resolution likely by late 2026")

        elif gold_high and not credit_tight:
            print("  🟡 GOLD LEADING CREDIT")
            print("     • Gold warned first, credit catching up")
            print("     • Normal pattern in crisis development")
            print("     • Monitor for continued credit deterioration")

        elif not gold_high and credit_tight:
            print("  🟢 NORMAL LATE-CYCLE")
            print("     • Typical late-cycle dynamics")
            print("     • Monitor for signs of turning")

        if btc_weak:
            print(f"\n  Bitcoin Weakness Suggests:")
            print(f"     • Liquidity tighter than credit spreads indicate")
            print(f"     • Speculation dead except in narrow sectors (AI)")
            print(f"     • Bitcoin acting as early warning of liquidity stress")

        print(f"\n{'='*80}")
        print("MONITORING PRIORITIES")
        print("="*80)

        print("\nWatch for these resolution triggers:\n")
        print("  Credit Spreads Breaking Out:")
        print(f"    • HY >350 bp = early warning")
        print(f"    • HY >500 bp = clear deterioration")
        print(f"    • HY >800 bp = crisis mode")

        print("\n  Market Breadth Collapse:")
        print(f"    • Breadth <95 = concerning concentration")
        print(f"    • Breadth <90 = AI bubble at risk")

        print("\n  Gold Confirmation:")
        print(f"    • Gold >$5,000 = crisis escalating")
        print(f"    • Gold <$4,000 = fears moderating")

        print("\n  Volatility Spike:")
        print(f"    • VIX >25 = fear returning")
        print(f"    • VIX >30 = crisis beginning")

        print(f"\n{'='*80}\n")


def main():
    """Main entry point."""
    analyzer = DivergenceAnalyzer()
    analyzer.print_comprehensive_analysis()


if __name__ == '__main__':
    main()
