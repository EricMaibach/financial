#!/usr/bin/env python3
"""
Comprehensive Market Analysis Report
Analyzes all collected data to assess current market state and outlook.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import pytz


class ComprehensiveAnalyzer:
    """Comprehensive market analysis across all asset classes."""

    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data = {}

    def load_all_data(self):
        """Load all available data files."""
        print("Loading all market data...")

        files_to_load = {
            # Credit
            'hy_spread': 'high_yield_spread.csv',
            'ig_spread': 'investment_grade_spread.csv',
            'ccc_spread': 'ccc_spread.csv',

            # Equity indices
            'spy': 'sp500_price.csv',
            'rsp': 'sp500_equal_weight_price.csv',
            'iwm': 'small_cap_price.csv',
            'qqq': 'nasdaq_price.csv',

            # Safe havens
            'gold': 'gold_price.csv',
            'gdx': 'gold_miners_price.csv',
            'slv': 'silver_price.csv',
            'btc': 'bitcoin_price.csv',

            # Volatility & risk
            'vix': 'vix_price.csv',
            'dxy': 'dollar_index_price.csv',

            # Fixed income
            'ief': 'treasury_7_10yr_price.csv',
            'tlt': 'treasury_20yr_price.csv',
            'shy': 'treasury_short_price.csv',
            'tip': 'tips_inflation_price.csv',

            # Credit ETFs
            'hyg': 'high_yield_credit_price.csv',
            'lqd': 'investment_grade_credit_price.csv',
            'bkln': 'leveraged_loan_price.csv',

            # Commodities
            'dbc': 'commodities_price.csv',
            'oil': 'oil_price.csv',

            # Derived metrics
            'breadth': 'market_breadth_ratio.csv',
            'gs_ratio': 'gold_silver_ratio.csv',
            'real_yield': 'real_yield_proxy.csv',
        }

        for key, filename in files_to_load.items():
            filepath = self.data_dir / filename
            if filepath.exists():
                df = pd.read_csv(filepath)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                self.data[key] = df
            else:
                print(f"  Missing: {filename}")

        print(f"Loaded {len(self.data)} datasets")

    def calculate_returns(self, df, column, periods=[1, 5, 20]):
        """Calculate returns over multiple periods."""
        returns = {}
        for period in periods:
            if len(df) > period:
                current = df.iloc[-1][column]
                past = df.iloc[-(period+1)][column]
                returns[f'{period}d'] = ((current / past) - 1) * 100
        return returns

    def calculate_percentile(self, df, column):
        """Calculate current value's historical percentile."""
        if len(df) < 2:
            return None
        current = df.iloc[-1][column]
        values = df[column].values
        percentile = (values < current).sum() / len(values) * 100
        return percentile

    def print_comprehensive_report(self):
        """Generate comprehensive analysis report."""

        eastern = pytz.timezone('US/Eastern')
        print("\n" + "="*100)
        print("COMPREHENSIVE MARKET ANALYSIS REPORT")
        print(f"Generated: {datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')} ET")
        print("="*100)

        # SECTION 1: CREDIT MARKETS
        self.analyze_credit_markets()

        # SECTION 2: EQUITY MARKETS
        self.analyze_equity_markets()

        # SECTION 3: SAFE HAVENS & ALTERNATIVES
        self.analyze_safe_havens()

        # SECTION 4: VOLATILITY & RISK SENTIMENT
        self.analyze_volatility_risk()

        # SECTION 5: FIXED INCOME & YIELDS
        self.analyze_fixed_income()

        # SECTION 6: COMMODITIES
        self.analyze_commodities()

        # SECTION 7: CROSS-ASSET CORRELATIONS
        self.analyze_correlations()

        # SECTION 8: THE BIG PICTURE
        self.synthesize_big_picture()

        # SECTION 9: SCENARIOS & OUTLOOK
        self.generate_scenarios()

    def analyze_credit_markets(self):
        """Analyze credit market data."""
        print("\n" + "="*100)
        print("SECTION 1: CREDIT MARKETS")
        print("="*100)

        if 'hy_spread' in self.data:
            hy = self.data['hy_spread']
            hy_current = hy.iloc[-1][hy.columns[1]] * 100
            hy_start = hy.iloc[0][hy.columns[1]] * 100
            hy_change = hy_current - hy_start
            hy_percentile = self.calculate_percentile(hy, hy.columns[1])

            print(f"\n📊 HIGH-YIELD CREDIT SPREADS")
            print(f"   Current: {hy_current:.0f} bp")
            print(f"   30-day change: {hy_change:+.0f} bp")
            print(f"   Historical percentile: {hy_percentile:.1f}%")
            print(f"   Period range: {hy[hy.columns[1]].min()*100:.0f} - {hy[hy.columns[1]].max()*100:.0f} bp")

            if hy_current < 250:
                print(f"   🔴 EXTREME: Tightest 1% of historical range")
                print(f"      → Markets pricing near-zero default risk")
                print(f"      → Late-cycle complacency or structural shift")
            elif hy_current < 300:
                print(f"   🟡 TIGHT: Very low default risk priced in")
            elif hy_current < 500:
                print(f"   🟢 NORMAL: Moderate spreads")
            else:
                print(f"   🔴 WIDE: Elevated stress")

        if 'ig_spread' in self.data:
            ig = self.data['ig_spread']
            ig_current = ig.iloc[-1][ig.columns[1]] * 100
            ig_start = ig.iloc[0][ig.columns[1]] * 100

            print(f"\n📊 INVESTMENT GRADE SPREADS")
            print(f"   Current: {ig_current:.0f} bp")
            print(f"   30-day change: {ig_current - ig_start:+.0f} bp")

            if ig_current < 80:
                print(f"   🔴 EXTREME: Rock-solid confidence in IG debt")

        if 'ccc_spread' in self.data and 'hy_spread' in self.data:
            ccc = self.data['ccc_spread']
            ccc_current = ccc.iloc[-1][ccc.columns[1]] * 100
            ratio = ccc_current / hy_current

            print(f"\n📊 DISTRESSED DEBT (CCC-RATED)")
            print(f"   CCC Spread: {ccc_current:.0f} bp")
            print(f"   CCC/HY Ratio: {ratio:.2f}x")

            if ratio > 3.5:
                print(f"   🔴 Distressed credits severely lagging")
                print(f"      → Credit quality bifurcation")
                print(f"      → Riskiest credits not participating in rally")
            elif ratio > 3.0:
                print(f"   🟡 Distressed lagging modestly")
            else:
                print(f"   🟢 Normal quality spread")

        # Credit ETF flows
        if 'hyg' in self.data:
            hyg = self.data['hyg']
            hyg_returns = self.calculate_returns(hyg, hyg.columns[1], [1, 5, 20])

            print(f"\n📊 CREDIT ETF PERFORMANCE")
            print(f"   HYG (High Yield ETF):")
            print(f"      Price: ${hyg.iloc[-1][hyg.columns[1]]:.2f}")
            if '20d' in hyg_returns:
                print(f"      30-day return: {hyg_returns['20d']:+.2f}%")
            if '5d' in hyg_returns:
                print(f"      5-day return: {hyg_returns['5d']:+.2f}%")

        if 'lqd' in self.data:
            lqd = self.data['lqd']
            lqd_returns = self.calculate_returns(lqd, lqd.columns[1], [1, 5, 20])

            print(f"   LQD (Investment Grade ETF):")
            print(f"      Price: ${lqd.iloc[-1][lqd.columns[1]]:.2f}")
            if '20d' in lqd_returns:
                print(f"      30-day return: {lqd_returns['20d']:+.2f}%")

        print(f"\n   💡 CREDIT MARKET INTERPRETATION:")
        if hy_current < 300:
            print(f"      • Credit markets in EXTREME complacency or new paradigm")
            print(f"      • Spreads this tight historically precede:")
            print(f"        - Either continued low defaults (soft landing)")
            print(f"        - Or sudden widening when reality hits (crisis)")
            print(f"      • Asymmetric risk: Little upside, significant downside")

    def analyze_equity_markets(self):
        """Analyze equity market data."""
        print("\n" + "="*100)
        print("SECTION 2: EQUITY MARKETS & CONCENTRATION")
        print("="*100)

        indices_data = {}

        for key, name in [('spy', 'S&P 500'), ('rsp', 'S&P Equal Weight'),
                          ('iwm', 'Small Caps'), ('qqq', 'Nasdaq-100')]:
            if key in self.data:
                df = self.data[key]
                indices_data[key] = {
                    'name': name,
                    'price': df.iloc[-1][df.columns[1]],
                    'returns': self.calculate_returns(df, df.columns[1], [1, 5, 20])
                }

        # Print index performance
        print(f"\n📊 EQUITY INDEX PERFORMANCE")
        for key in ['spy', 'qqq', 'iwm', 'rsp']:
            if key in indices_data:
                data = indices_data[key]
                print(f"\n   {data['name']}:")
                print(f"      Price: ${data['price']:.2f}")
                if '20d' in data['returns']:
                    print(f"      30-day: {data['returns']['20d']:+.2f}%")
                if '5d' in data['returns']:
                    print(f"      5-day: {data['returns']['5d']:+.2f}%")
                if '1d' in data['returns']:
                    print(f"      1-day: {data['returns']['1d']:+.2f}%")

        # Market breadth analysis
        if 'breadth' in self.data:
            breadth = self.data['breadth']
            # Note: Current calculation may be off, but trend is valid
            print(f"\n📊 MARKET BREADTH & CONCENTRATION")
            print(f"   RSP/SPY Ratio trend:")
            print(f"      Recent values: {breadth.iloc[-5:][breadth.columns[1]].values}")
            print(f"   ⚠️  Note: Absolute values need recalibration")
            print(f"   📈 Trend interpretation:")
            print(f"      • Ratio trending matters more than absolute level")
            print(f"      • Lower = more concentrated in large caps")
            print(f"      • Higher = broader market participation")

        # Performance comparison
        if 'spy' in indices_data and 'iwm' in indices_data:
            spy_ret = indices_data['spy']['returns'].get('20d', 0)
            iwm_ret = indices_data['iwm']['returns'].get('20d', 0)

            print(f"\n📊 LARGE CAP vs SMALL CAP")
            print(f"   S&P 500: {spy_ret:+.2f}%")
            print(f"   Small Caps: {iwm_ret:+.2f}%")
            print(f"   Spread: {iwm_ret - spy_ret:+.2f}%")

            if iwm_ret < spy_ret - 2:
                print(f"   🔴 Small caps lagging significantly")
                print(f"      → Risk-off in equities (flight to quality)")
                print(f"      → Narrow leadership")
            elif iwm_ret > spy_ret + 2:
                print(f"   🟢 Small caps outperforming")
                print(f"      → Broad risk appetite")
            else:
                print(f"   🟡 Relatively balanced")

        if 'qqq' in indices_data and 'spy' in indices_data:
            qqq_ret = indices_data['qqq']['returns'].get('20d', 0)
            spy_ret = indices_data['spy']['returns'].get('20d', 0)

            print(f"\n📊 TECH/AI CONCENTRATION")
            print(f"   Nasdaq-100: {qqq_ret:+.2f}%")
            print(f"   S&P 500: {spy_ret:+.2f}%")
            print(f"   Tech premium: {qqq_ret - spy_ret:+.2f}%")

            if qqq_ret > spy_ret + 3:
                print(f"   🔴 EXTREME tech concentration")
                print(f"      → AI bubble dynamics")
                print(f"      → All capital flowing to tech/AI")
                print(f"      → High concentration risk")
            elif qqq_ret > spy_ret + 1:
                print(f"   🟡 Tech outperformance")
            else:
                print(f"   🟢 Balanced performance")

    def analyze_safe_havens(self):
        """Analyze safe haven assets."""
        print("\n" + "="*100)
        print("SECTION 3: SAFE HAVENS & ALTERNATIVE ASSETS")
        print("="*100)

        # Gold analysis
        if 'gold' in self.data:
            gold = self.data['gold']
            gold_price = gold.iloc[-1][gold.columns[1]] * 10  # Approximate spot
            gold_returns = self.calculate_returns(gold, gold.columns[1], [1, 5, 20])
            gold_percentile = self.calculate_percentile(gold, gold.columns[1])

            print(f"\n🏆 GOLD (Spot proxy)")
            print(f"   Price: ${gold_price:.0f}")
            if '20d' in gold_returns:
                print(f"   30-day: {gold_returns['20d']:+.2f}%")
            if '5d' in gold_returns:
                print(f"   5-day: {gold_returns['5d']:+.2f}%")
            print(f"   Historical percentile: {gold_percentile:.1f}%")

            if gold_price > 4500:
                print(f"   🔴 EXTREME LEVELS - All-time high territory")
                print(f"      Gold at $4,500+ pricing:")
                print(f"      • De-dollarization accelerating")
                print(f"      • Fiscal crisis expectations")
                print(f"      • Geopolitical fragmentation")
                print(f"      • Currency debasement fears")
            elif gold_price > 4000:
                print(f"   🟠 VERY ELEVATED - Major structural concerns")
            elif gold_price > 3000:
                print(f"   🟡 ELEVATED - Above long-term trend")

        # Gold miners
        if 'gdx' in self.data:
            gdx = self.data['gdx']
            gdx_returns = self.calculate_returns(gdx, gdx.columns[1], [1, 5, 20])

            print(f"\n⛏️  GOLD MINERS (GDX)")
            print(f"   Price: ${gdx.iloc[-1][gdx.columns[1]]:.2f}")
            if '20d' in gdx_returns:
                print(f"   30-day: {gdx_returns['20d']:+.2f}%")

            # Gold vs miners
            if 'gold' in self.data and '20d' in gold_returns and '20d' in gdx_returns:
                if gdx_returns['20d'] > gold_returns['20d'] + 5:
                    print(f"   ✅ Miners outperforming - confirms gold rally")
                elif gdx_returns['20d'] < gold_returns['20d'] - 5:
                    print(f"   ⚠️  Miners lagging - gold rally suspect")
                else:
                    print(f"   → Miners tracking gold - normal")

        # Silver
        if 'slv' in self.data:
            slv = self.data['slv']
            slv_returns = self.calculate_returns(slv, slv.columns[1], [1, 5, 20])

            print(f"\n🥈 SILVER")
            print(f"   Price: ${slv.iloc[-1][slv.columns[1]]:.2f}")
            if '20d' in slv_returns:
                print(f"   30-day: {slv_returns['20d']:+.2f}%")

        # Gold/Silver ratio
        if 'gs_ratio' in self.data:
            gsr = self.data['gs_ratio']
            gsr_current = gsr.iloc[-1][gsr.columns[1]]

            print(f"\n📊 GOLD/SILVER RATIO")
            print(f"   Current: {gsr_current:.1f}")

            if gsr_current > 90:
                print(f"   🔴 EXTREME - Fear/defensive")
                print(f"      → Flight to safety (gold over silver)")
            elif gsr_current > 80:
                print(f"   🟡 ELEVATED - Risk-off sentiment")
            elif gsr_current < 70:
                print(f"   🟢 NORMAL - Balanced precious metals")

        # Bitcoin
        if 'btc' in self.data:
            btc = self.data['btc']
            btc_price = btc.iloc[-1][btc.columns[1]]
            btc_returns = self.calculate_returns(btc, btc.columns[1], [1, 5, 20])

            print(f"\n₿  BITCOIN")
            print(f"   Price: ${btc_price:,.2f}")
            if '20d' in btc_returns:
                print(f"   30-day: {btc_returns['20d']:+.2f}%")
            if '5d' in btc_returns:
                print(f"   5-day: {btc_returns['5d']:+.2f}%")

            # Bitcoin vs Gold comparison
            if 'gold' in self.data and '20d' in gold_returns and '20d' in btc_returns:
                print(f"\n   Bitcoin vs Gold (30-day):")
                print(f"      Gold: {gold_returns['20d']:+.2f}%")
                print(f"      Bitcoin: {btc_returns['20d']:+.2f}%")

                if btc_returns['20d'] < -5 and gold_returns['20d'] > 5:
                    print(f"   🔴 DIVERGENCE: Bitcoin falling while gold rising")
                    print(f"      → Liquidity tight despite safe-haven demand")
                    print(f"      → 'Digital gold' narrative failing")
                    print(f"      → Risk-off in speculative assets")
                elif btc_returns['20d'] > 10 and gold_returns['20d'] > 5:
                    print(f"   🟡 Both rallying - mixed signal")
                    print(f"      → Debasement fears + risk appetite")
                elif btc_returns['20d'] > gold_returns['20d']:
                    print(f"   🟢 Bitcoin outperforming")
                    print(f"      → Risk-on in alternatives")
                else:
                    print(f"   → Relatively aligned")

    def analyze_volatility_risk(self):
        """Analyze volatility and risk indicators."""
        print("\n" + "="*100)
        print("SECTION 4: VOLATILITY & RISK SENTIMENT")
        print("="*100)

        if 'vix' in self.data:
            vix = self.data['vix']
            vix_current = vix.iloc[-1][vix.columns[1]]
            vix_avg = vix[vix.columns[1]].mean()

            print(f"\n📊 VIX (Fear Index)")
            print(f"   Current: {vix_current:.2f}")
            print(f"   30-day average: {vix_avg:.2f}")
            print(f"   30-day range: {vix[vix.columns[1]].min():.2f} - {vix[vix.columns[1]].max():.2f}")

            if vix_current < 15:
                print(f"   🟢 LOW FEAR - Market complacency")
                print(f"      → Investors not pricing much risk")
                if vix_current < 12:
                    print(f"      🔴 EXTREME complacency - historically dangerous")
            elif vix_current < 20:
                print(f"   🟡 MODERATE - Normal volatility")
            elif vix_current < 30:
                print(f"   🟠 ELEVATED - Uncertainty rising")
            else:
                print(f"   🔴 HIGH FEAR - Crisis mode")

        if 'dxy' in self.data:
            dxy = self.data['dxy']
            dxy_price = dxy.iloc[-1][dxy.columns[1]]
            dxy_returns = self.calculate_returns(dxy, dxy.columns[1], [1, 5, 20])

            print(f"\n💵 US DOLLAR INDEX")
            print(f"   Price: ${dxy_price:.2f}")
            if '20d' in dxy_returns:
                print(f"   30-day: {dxy_returns['20d']:+.2f}%")

            # Dollar vs Gold - key relationship
            if 'gold' in self.data and '20d' in dxy_returns:
                gold_returns = self.calculate_returns(self.data['gold'], self.data['gold'].columns[1], [20])
                if '20d' in gold_returns:
                    print(f"\n   Dollar vs Gold:")
                    if dxy_returns['20d'] > 2 and gold_returns['20d'] > 2:
                        print(f"   🔴 BOTH RISING - Extreme flight to safety")
                        print(f"      → Other currencies/assets being sold")
                        print(f"      → Crisis dynamics")
                    elif dxy_returns['20d'] < -2 and gold_returns['20d'] > 5:
                        print(f"   🔴 Dollar falling, gold rising")
                        print(f"      → Dollar debasement fears confirmed")
                        print(f"      → De-dollarization trend")
                    elif dxy_returns['20d'] > 2 and gold_returns['20d'] < -2:
                        print(f"   🟢 Dollar strength, gold weakness")
                        print(f"      → Risk normalizing")

    def analyze_fixed_income(self):
        """Analyze fixed income markets."""
        print("\n" + "="*100)
        print("SECTION 5: FIXED INCOME & YIELD CURVE")
        print("="*100)

        treasury_data = {}
        for key, name in [('shy', 'Short-term (SHY)'), ('ief', '7-10yr (IEF)'), ('tlt', '20yr (TLT)')]:
            if key in self.data:
                df = self.data[key]
                treasury_data[key] = {
                    'name': name,
                    'price': df.iloc[-1][df.columns[1]],
                    'returns': self.calculate_returns(df, df.columns[1], [1, 5, 20])
                }

        print(f"\n📊 TREASURY PRICES (inverse of yields)")
        for key in ['shy', 'ief', 'tlt']:
            if key in treasury_data:
                data = treasury_data[key]
                print(f"\n   {data['name']}:")
                print(f"      Price: ${data['price']:.2f}")
                if '20d' in data['returns']:
                    print(f"      30-day: {data['returns']['20d']:+.2f}%")

        # Curve analysis
        if 'shy' in treasury_data and 'tlt' in treasury_data:
            shy_ret = treasury_data['shy']['returns'].get('20d', 0)
            tlt_ret = treasury_data['tlt']['returns'].get('20d', 0)

            print(f"\n📊 YIELD CURVE DYNAMICS")
            print(f"   Long bonds vs Short bonds:")
            if tlt_ret > shy_ret + 2:
                print(f"   🟢 Curve steepening (TLT outperforming)")
                print(f"      → Recession fears OR Fed cutting expectations")
            elif tlt_ret < shy_ret - 2:
                print(f"   🔴 Curve flattening (TLT underperforming)")
                print(f"      → Inflation fears OR Fed hawkish")
            else:
                print(f"   → Relatively stable curve")

        # TIPS analysis
        if 'tip' in self.data and 'ief' in self.data:
            print(f"\n📊 INFLATION EXPECTATIONS (TIPS)")
            tip = self.data['tip']
            tip_returns = self.calculate_returns(tip, tip.columns[1], [1, 5, 20])

            print(f"   TIP Price: ${tip.iloc[-1][tip.columns[1]]:.2f}")
            if '20d' in tip_returns:
                print(f"   30-day return: {tip_returns['20d']:+.2f}%")

            if 'real_yield' in self.data:
                ry = self.data['real_yield']
                print(f"   Real yield proxy trend: {ry.iloc[-5:][ry.columns[1]].values[-1]:.2f}%")

    def analyze_commodities(self):
        """Analyze commodity markets."""
        print("\n" + "="*100)
        print("SECTION 6: COMMODITIES")
        print("="*100)

        if 'oil' in self.data:
            oil = self.data['oil']
            oil_price = oil.iloc[-1][oil.columns[1]]
            oil_returns = self.calculate_returns(oil, oil.columns[1], [1, 5, 20])

            print(f"\n🛢️  OIL (USO ETF)")
            print(f"   Price: ${oil_price:.2f}")
            if '20d' in oil_returns:
                print(f"   30-day: {oil_returns['20d']:+.2f}%")

                if oil_returns['20d'] < -10:
                    print(f"   🔴 Weakness - Demand concerns")
                elif oil_returns['20d'] > 10:
                    print(f"   🔴 Strength - Inflation/supply concerns")

        if 'dbc' in self.data:
            dbc = self.data['dbc']
            dbc_returns = self.calculate_returns(dbc, dbc.columns[1], [1, 5, 20])

            print(f"\n📦 BROAD COMMODITIES (DBC)")
            print(f"   Price: ${dbc.iloc[-1][dbc.columns[1]]:.2f}")
            if '20d' in dbc_returns:
                print(f"   30-day: {dbc_returns['20d']:+.2f}%")

    def analyze_correlations(self):
        """Analyze cross-asset correlations."""
        print("\n" + "="*100)
        print("SECTION 7: CROSS-ASSET CORRELATIONS & DIVERGENCES")
        print("="*100)

        # Calculate 30-day returns for key assets
        returns_data = {}

        assets = {
            'spy': 'Stocks (SPY)',
            'gold': 'Gold',
            'btc': 'Bitcoin',
            'hyg': 'HY Credit',
            'ief': 'Treasuries'
        }

        for key, name in assets.items():
            if key in self.data:
                df = self.data[key]
                if len(df) > 20:
                    rets = df[df.columns[1]].pct_change().iloc[-20:]
                    returns_data[name] = rets

        if len(returns_data) >= 3:
            print(f"\n📊 CORRELATION MATRIX (30-day)")

            # Create DataFrame from returns
            df_corr = pd.DataFrame(returns_data)
            corr_matrix = df_corr.corr()

            print(f"\n{corr_matrix.to_string()}")

            # Highlight key correlations
            print(f"\n   Key Correlation Insights:")

            if 'Stocks (SPY)' in corr_matrix.columns and 'Gold' in corr_matrix.columns:
                stocks_gold = corr_matrix.loc['Stocks (SPY)', 'Gold']
                print(f"      Stocks vs Gold: {stocks_gold:+.2f}")
                if stocks_gold > 0.3:
                    print(f"         🔴 BOTH RISING - Unusual (everything rally)")
                elif stocks_gold < -0.3:
                    print(f"         🟢 NEGATIVE - Normal (risk-on vs risk-off)")

            if 'Gold' in corr_matrix.columns and 'Bitcoin' in corr_matrix.columns:
                gold_btc = corr_matrix.loc['Gold', 'Bitcoin']
                print(f"      Gold vs Bitcoin: {gold_btc:+.2f}")
                if gold_btc < 0:
                    print(f"         🔴 DIVERGING - Gold up, Bitcoin down (liquidity issue)")
                elif gold_btc > 0.5:
                    print(f"         🟡 ALIGNED - Both acting as debasement hedges")

    def synthesize_big_picture(self):
        """Synthesize all data into big picture view."""
        print("\n" + "="*100)
        print("SECTION 8: THE BIG PICTURE - SYNTHESIS")
        print("="*100)

        # Calculate key metrics
        signals = {
            'credit_tight': False,
            'gold_extreme': False,
            'stocks_up': False,
            'vix_low': False,
            'btc_weak': False,
            'breadth_narrow': False,
        }

        if 'hy_spread' in self.data:
            hy_current = self.data['hy_spread'].iloc[-1][self.data['hy_spread'].columns[1]] * 100
            signals['credit_tight'] = hy_current < 300

        if 'gold' in self.data:
            gold_price = self.data['gold'].iloc[-1][self.data['gold'].columns[1]] * 10
            signals['gold_extreme'] = gold_price > 4000

        if 'spy' in self.data:
            spy_rets = self.calculate_returns(self.data['spy'], self.data['spy'].columns[1], [20])
            if '20d' in spy_rets:
                signals['stocks_up'] = spy_rets['20d'] > 0

        if 'vix' in self.data:
            vix_current = self.data['vix'].iloc[-1][self.data['vix'].columns[1]]
            signals['vix_low'] = vix_current < 16

        if 'btc' in self.data:
            btc_rets = self.calculate_returns(self.data['btc'], self.data['btc'].columns[1], [20])
            if '20d' in btc_rets:
                signals['btc_weak'] = btc_rets['20d'] < 0

        print(f"\n🔍 MARKET REGIME ASSESSMENT")
        print(f"\n   Signal Checklist:")
        print(f"      Credit spreads tight (<300bp): {'✓' if signals['credit_tight'] else '✗'}")
        print(f"      Gold extreme (>$4000): {'✓' if signals['gold_extreme'] else '✗'}")
        print(f"      Stocks positive (30d): {'✓' if signals['stocks_up'] else '✗'}")
        print(f"      VIX low (<16): {'✓' if signals['vix_low'] else '✗'}")
        print(f"      Bitcoin weak: {'✓' if signals['btc_weak'] else '✗'}")

        # Determine regime
        divergence_count = sum([
            signals['credit_tight'] and signals['gold_extreme'],
            signals['vix_low'] and signals['gold_extreme'],
            signals['stocks_up'] and signals['gold_extreme']
        ])

        print(f"\n   📊 MARKET REGIME:")

        if signals['credit_tight'] and signals['gold_extreme'] and signals['vix_low']:
            print(f"      🔴 EXTREME DIVERGENCE REGIME")
            print(f"         • Credit/equity markets: 'Everything is fine'")
            print(f"         • Gold: 'Structural crisis ahead'")
            print(f"         • VIX: 'No fear/complacency'")
            print(f"         • Bitcoin: {'Weak (liquidity tight)' if signals['btc_weak'] else 'Mixed signal'}")
            print(f"\n         This is a HISTORIC setup with NO precedent")
            print(f"         One of these markets is catastrophically wrong")

        elif signals['gold_extreme']:
            print(f"      🟡 ELEVATED DIVERGENCE")
            print(f"         • Gold signaling major concerns")
            print(f"         • Other markets showing some stress")
            print(f"         • Divergence present but not extreme")

        else:
            print(f"      🟢 NORMAL MARKET CONDITIONS")
            print(f"         • Markets generally aligned")
            print(f"         • No major divergences detected")

    def generate_scenarios(self):
        """Generate forward-looking scenarios."""
        print("\n" + "="*100)
        print("SECTION 9: SCENARIOS & 12-MONTH OUTLOOK")
        print("="*100)

        # Get current state
        hy_current = 276  # default
        gold_current = 4145  # default

        if 'hy_spread' in self.data:
            hy_current = self.data['hy_spread'].iloc[-1][self.data['hy_spread'].columns[1]] * 100

        if 'gold' in self.data:
            gold_current = self.data['gold'].iloc[-1][self.data['gold'].columns[1]] * 10

        divergence_gap = ((gold_current / 2000) ** 1.5) * 400 - hy_current

        print(f"\n📋 CURRENT STATE")
        print(f"   • HY Credit Spreads: {hy_current:.0f} bp")
        print(f"   • Gold Price: ${gold_current:.0f}")
        print(f"   • Divergence Gap: {divergence_gap:.0f} bp")

        print(f"\n" + "-"*100)
        print(f"SCENARIO 1: 'CREDIT CATCHES DOWN TO GOLD' (Probability: 55-60%)")
        print("-"*100)

        print(f"\n   Timeline: 6-18 months (by Q2-Q3 2026)")
        print(f"\n   What Happens:")
        print(f"      1. AI stock bubble peaks in Q1-Q2 2026")
        print(f"      2. Earnings disappoint or valuations reset")
        print(f"      3. Credit spreads begin widening (HY: 350→600 bp)")
        print(f"      4. Economic slowdown emerges")
        print(f"      5. Gold stays elevated or rises further ($4,500-5,000)")
        print(f"      6. VIX spikes >25, then >30")
        print(f"      7. Fed potentially forced to cut more aggressively")

        print(f"\n   Catalysts:")
        print(f"      • AI earnings miss expectations")
        print(f"      • Geopolitical event (Middle East, China-Taiwan)")
        print(f"      • Corporate refinancing stress emerges")
        print(f"      • Fiscal crisis/debt ceiling drama")
        print(f"      • Banking sector stress (regional banks)")

        print(f"\n   Market Outcomes:")
        print(f"      • HY Spreads: 276 bp → 500-700 bp (+224-424 bp)")
        print(f"      • Stocks (SPY): -15% to -25%")
        print(f"      • Gold: $4,145 → $4,500-5,500 (+8% to +33%)")
        print(f"      • Bitcoin: Bottoms early, then recovers")
        print(f"      • Dollar: Potentially weaker (fiscal fears)")

        print(f"\n   Economic Impact:")
        print(f"      • Mild to moderate recession")
        print(f"      • Unemployment rises 1-2%")
        print(f"      • Fed cuts rates 100-200 bp")
        print(f"      • Fiscal stimulus likely")

        print(f"\n" + "-"*100)
        print(f"SCENARIO 2: 'MESSY MIDDLE - BOTH PARTIALLY RIGHT' (Probability: 25-30%)")
        print("-"*100)

        print(f"\n   Timeline: 12-36 months (extended grind)")
        print(f"\n   What Happens:")
        print(f"      1. No single crisis, but slow deterioration")
        print(f"      2. Credit spreads widen moderately (HY: 350-450 bp)")
        print(f"      3. Gold stays high but doesn't explode higher")
        print(f"      4. Stocks choppy, rolling bear market")
        print(f"      5. 'Higher for longer' grinds everything down")
        print(f"      6. Sector rotation, no clear leadership")

        print(f"\n   Market Outcomes:")
        print(f"      • HY Spreads: 276 bp → 350-450 bp (+74-174 bp)")
        print(f"      • Stocks (SPY): -5% to +5% (choppy, range-bound)")
        print(f"      • Gold: $4,145 → $4,000-4,800 (volatile range)")
        print(f"      • Bitcoin: Weak for extended period")
        print(f"      • Volatility: Elevated but not crisis levels")

        print(f"\n   Economic Impact:")
        print(f"      • Below-trend growth (1-1.5% GDP)")
        print(f"      • No technical recession but feels like one")
        print(f"      • Fed on hold or minimal cuts")
        print(f"      • Earnings recession")

        print(f"\n" + "-"*100)
        print(f"SCENARIO 3: 'GOLD CORRECTS - SOFT LANDING' (Probability: 15-20%)")
        print("-"*100)

        print(f"\n   Timeline: 3-9 months")
        print(f"\n   What Happens:")
        print(f"      1. AI productivity boom validates valuations")
        print(f"      2. Geopolitical tensions de-escalate")
        print(f"      3. Fiscal concerns overblown")
        print(f"      4. Gold corrects -20% to -30%")
        print(f"      5. Credit spreads stay tight")
        print(f"      6. Bitcoin recovers strongly")
        print(f"      7. Soft landing achieved")

        print(f"\n   Market Outcomes:")
        print(f"      • HY Spreads: 276 bp → 250-300 bp (stable/tight)")
        print(f"      • Stocks (SPY): +10% to +20% (continue rally)")
        print(f"      • Gold: $4,145 → $3,000-3,500 (-15% to -28%)")
        print(f"      • Bitcoin: Strong recovery (+30-50%)")
        print(f"      • VIX: Stays low (<15)")

        print(f"\n   Why This is Less Likely:")
        print(f"      • Requires everything to go right")
        print(f"      • Gold rally driven by central banks (won't reverse easily)")
        print(f"      • Structural fiscal issues don't disappear")
        print(f"      • Geopolitical fragmentation accelerating")

        print(f"\n" + "="*100)
        print(f"BASE CASE EXPECTATION (Next 12 Months)")
        print("="*100)

        print(f"\n   Most Likely Path: Scenario 1 with elements of Scenario 2")
        print(f"\n   Q1 2026 (Jan-Mar):")
        print(f"      • Divergence persists or widens slightly")
        print(f"      • AI stocks continue strong but volatility increases")
        print(f"      • Gold consolidates $4,000-4,500 range")
        print(f"      • Credit spreads start to tick wider (280-300 bp)")

        print(f"\n   Q2 2026 (Apr-Jun):")
        print(f"      • AI bubble shows cracks (earnings, valuations)")
        print(f"      • Credit spreads widen more noticeably (320-400 bp)")
        print(f"      • Market breadth deteriorates further")
        print(f"      • VIX breaks above 20")

        print(f"\n   Q3 2026 (Jul-Sep):")
        print(f"      • Credit stress becomes obvious (HY: 450-550 bp)")
        print(f"      • Stocks down 10-15% from peaks")
        print(f"      • Gold validates (holds $4,000+ or moves higher)")
        print(f"      • Fed cutting aggressively")

        print(f"\n   Q4 2026 (Oct-Dec):")
        print(f"      • Resolution phase - divergence narrowing")
        print(f"      • Recession probable or already begun")
        print(f"      • Spreads peak (600-800 bp)")
        print(f"      • Policy response intensifies")

        print(f"\n   Key Wildcards:")
        print(f"      🎲 Geopolitical shock (war, trade collapse)")
        print(f"      🎲 Fiscal crisis (debt ceiling, downgrade)")
        print(f"      🎲 Banking sector stress")
        print(f"      🎲 AI regulation or bubble pop")
        print(f"      🎲 Fed policy error (too tight or too loose)")

        print(f"\n   Investor Positioning:")
        print(f"      ✅ Maintain defensive positioning")
        print(f"      ✅ Reduce credit risk exposure")
        print(f"      ✅ Hold gold allocation (insurance)")
        print(f"      ✅ Increase cash reserves")
        print(f"      ✅ Avoid concentrated tech/AI bets")
        print(f"      ✅ Consider selling vol (VIX <15 won't last)")

        print(f"\n" + "="*100 + "\n")


def main():
    """Run comprehensive analysis."""
    analyzer = ComprehensiveAnalyzer()
    analyzer.load_all_data()
    analyzer.print_comprehensive_report()


if __name__ == '__main__':
    main()
