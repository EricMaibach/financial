# Regime Detection Backtest & Optimization Strategy

## Goal

Automatically generate, test, and validate new macro regime detection methods to find approaches that genuinely outperform the current k-means classifier — without overfitting to historical data.

## Current State

- **Current method**: K-means clustering (k=4) on 5 FRED indicators with a 60-month rolling window
- **Current score**: 50.4/100 composite on single-pass historical backtest
- **Scoring assets**: S&P 500 (37.5%), Treasuries/TLT (31.25%), Gold (31.25%) — Bitcoin excluded (see below)
- **Regime labels**: Bull, Neutral, Bear, Recession Watch
- **Backtest script**: `signaltrackers/backtesting/regime_backtest.py`
- **Results**: `signaltrackers/backtesting/results/`

## Data Availability

| Asset / Indicator | CSV File | Data Starts | Data Ends |
|---|---|---|---|
| S&P 500 | `sp500_price.csv` | 1993-01 | Present |
| Treasuries (TLT) | `treasury_20yr_price.csv` | 2002-07 | Present |
| Gold | `gold_price.csv` | 2004-11 | Present |
| ~~Bitcoin~~ | ~~`bitcoin_price.csv`~~ | ~~2014-09~~ | ~~Excluded from scoring~~ |
| HY Spread | `high_yield_spread.csv` | 1996-12 | Present |
| Yield Curve 10Y-2Y | `yield_curve_10y2y.csv` | 1991-02 | Present |
| NFCI | `nfci.csv` | 1991-02 | Present |
| Initial Claims | `initial_claims.csv` | 1991-02 | Present |
| Fed Funds Rate | `fed_funds_rate.csv` | 1991-02 | Present |

---

## Three-Layer Validation Architecture

### Why Three Layers?

Running many automated iterations against the same historical data creates a **multiple hypothesis testing** problem. Even if every method is pure noise, the best-scoring one will look good by chance. Three layers of defense prevent this:

1. **Walk-forward expanding window** — tests generalization across different economic eras
2. **Combinatorial Purged Cross-Validation (CPCV)** — detects overfitting via probability analysis
3. **Deflated Sharpe Ratio (DSR)** — corrects for the number of methods tested

### Layer 1: Walk-Forward Expanding Window (Primary Scoring)

This is how each method gets scored during the automated loop.

**How it works:**

```
Train: [1993 -------- 2005]  Test: [2005-2007]  → score_1
Train: [1993 ----------- 2007]  Test: [2007-2009]  → score_2
Train: [1993 -------------- 2009]  Test: [2009-2011]  → score_3
Train: [1993 ----------------- 2011]  Test: [2011-2013]  → score_4
Train: [1993 -------------------- 2013]  Test: [2013-2015]  → score_5
Train: [1993 ----------------------- 2015]  Test: [2015-2017]  → score_6
Train: [1993 -------------------------- 2017]  Test: [2017-2019]  → score_7
Train: [1993 ----------------------------- 2019]  Test: [2019-2021]  → score_8
Train: [1993 -------------------------------- 2021]  Test: [2021-2023]  → score_9
Train: [1993 ----------------------------------- 2023]  Test: [2023-2025]  → score_10
```

**Parameters:**

- Minimum training window: **120 months (10 years)** — must capture at least one full business cycle
- Test window: **24 months** — enough data for ~16 usable monthly evaluation points after accounting for the 90-day forward look-ahead
- Step size: **24 months** (non-overlapping test windows)
- Yields approximately **8-10 folds**

**Handling assets with different data availability:**

For each fold, only score assets that have data in that fold's test period. Renormalize weights to sum to 1.0 for available assets only.

Example:
- Fold 1 (test: 2005-2007): Only S&P 500 available (Treasuries starts 2002, Gold starts 2004 — may have partial data) → weights renormalized for available assets
- Fold 3+ (test: 2009+): All 3 assets available → weights stay 37.5% / 31.25% / 31.25%

**Per-fold scoring:**

For each monthly evaluation point in the test window:
1. Classify regime using the method (trained only on training data)
2. Compute 90-day forward returns for each available asset
3. Check if each asset moved in the expected direction for that regime
4. Compute weighted accuracy across available assets

**Expected directions per regime:**

| Regime | S&P 500 | Treasuries | Gold |
|--------|---------|------------|------|
| Bull | positive | negative | negative |
| Neutral | neutral (±5%) | neutral (±5%) | neutral (±5%) |
| Bear | negative | positive | positive |
| Recession Watch | negative | positive | positive |

> **Why no Bitcoin?** Research (NY Fed Staff Report No. 1052) shows Bitcoin is
> driven by liquidity conditions and its own halving cycle, not macro regimes.
> Backtesting showed 34.8% accuracy under risk-on/risk-off assumptions —
> including it adds noise that obscures regime detection accuracy. See GitHub
> issue #292 for the dashboard-facing implications.

**Method's overall score = mean of all fold scores.**

Also record:
- Standard deviation across folds (consistency matters)
- Sharpe-like ratio: mean / std (higher = more consistent)
- Individual fold scores (for later CPCV analysis)

### Layer 2: Combinatorial Purged Cross-Validation (Robustness Check)

Applied **post-loop** to the **top 5 methods** only.

**What it does:**

CPCV generates many more train/test combinations than walk-forward, producing a **distribution** of out-of-sample performance. From this distribution, we compute the **Probability of Backtest Overfitting (PBO)**.

**Parameters:**

- k = 6 groups (time-ordered partitions of the full dataset)
- p = 2 test groups per split
- This gives C(6,2) = **15 backtest paths** per method
- **Purge window: 3 months** — remove any training observations within 3 months of a test boundary (critical because our labels use 90-day forward returns, so an observation at time t depends on returns through t+90 days)
- **Embargo: 1 month** after each test fold boundary (prevents serial correlation leakage)

**Output per method:**

- Distribution of 15 out-of-sample scores
- PBO = fraction of paths where out-of-sample performance is worse than in-sample
- **Decision rule: PBO > 0.5 → method is likely overfit → flag/eliminate**

**Libraries:**

- `skfolio.model_selection.CombinatorialPurgedCV` (production-ready)
- `timeseriescv` PyPI package (`CombPurgedKFoldCV`, lightweight alternative)

### Layer 3: Deflated Sharpe Ratio (Final Selection Correction)

Applied to the **winning method** after CPCV filtering.

**What it does:**

Answers: "Given that I tested N methods and picked the best, what is the probability this score is genuine and not just luck from multiple testing?"

**Inputs:**

- Observed Sharpe ratio of the best method (mean score / std across folds)
- Std of Sharpe ratios across ALL tested methods
- N = total number of methods tested (every iteration counts, even discarded ones)
- T = number of independent observations (folds)
- Skewness and kurtosis of the score distribution

**Decision rule: p-value > 0.05 → result is suspect, likely a statistical fluke.**

**Reference:** Bailey & Lopez de Prado, "The Deflated Sharpe Ratio" (2014), SSRN 2460551.

---

## Additional Guardrails

### Regime Stability Check

A method that flip-flops between regimes monthly is useless for investors regardless of its backtest score.

**Requirement:** Average regime duration must be **3+ months** for macro regimes.

**Measurement:** Count regime transitions in the backtest, divide total months by number of transitions. If < 3, flag the method.

### Economic Plausibility Filter

Before scoring, verify each method's regime assignments against known economic events.

**Hard failures (discard the method):**

- March 2020 classified as Bull
- 2017 classified as Recession Watch
- 2008-2009 classified as Bull
- 2003-2006 classified as Recession Watch

This reduces effective trial count (good for DSR calculation).

### Final Sanity Check (6-Month Holdout)

Reserve the **most recent 6 months** of data as a true holdout, never touched during the loop.

- Not the primary validation (walk-forward is)
- One-time reality check on the final winner only
- Short enough that Bitcoin data loss is negligible
- Recent enough to reflect current market dynamics

---

## Automated Loop Design

### Architecture Overview

The loop consists of two components:

1. **Claude command file** (`.claude/commands/regime-research.md`) — A detailed prompt telling Claude exactly what to do in one iteration: read the scoreboard, research a new approach, implement it, run the walk-forward scorer, update the scoreboard.

2. **Shell script** (`scripts/regime-research-loop.sh`) — Runs the command in a loop with a configurable wait between iterations. Invokes Claude headlessly via `claude --dangerously-skip-permissions -p "/regime-research"`.

The shell script handles scheduling. Claude handles the research, coding, and scoring. Each invocation is a fresh Claude session — context comes from reading the scoreboard and strategy doc, not from prior sessions.

### Shell Script Design

```bash
#!/bin/bash
# scripts/regime-research-loop.sh
#
# Runs the regime research command in a loop.
# Usage: bash scripts/regime-research-loop.sh [iterations] [wait_minutes]
#   iterations:   number of iterations to run (default: 10)
#   wait_minutes: minutes to wait between iterations (default: 60)

ITERATIONS=${1:-10}
WAIT_MINUTES=${2:-60}
LOG_DIR="$HOME/.claude/projects/financial/logs"
LOG_FILE="$LOG_DIR/regime-research.log"

mkdir -p "$LOG_DIR"

for i in $(seq 1 $ITERATIONS); do
    echo "[$(date)] Starting iteration $i/$ITERATIONS" | tee -a "$LOG_FILE"
    cd /home/eric/Documents/repos/financial
    claude --dangerously-skip-permissions -p "/regime-research" 2>&1 | tee -a "$LOG_FILE"
    echo "[$(date)] Iteration $i complete" | tee -a "$LOG_FILE"

    if [ $i -lt $ITERATIONS ]; then
        echo "[$(date)] Waiting $WAIT_MINUTES minutes..." | tee -a "$LOG_FILE"
        sleep "${WAIT_MINUTES}m"
    fi
done

echo "[$(date)] All $ITERATIONS iterations complete" | tee -a "$LOG_FILE"
```

### Claude Command File Design

File: `.claude/commands/regime-research.md`

The command file instructs Claude to perform one complete iteration. It must:

1. **Read context** — Read `docs/REGIME-BACKTEST-STRATEGY.md` for the full approach, `signaltrackers/backtesting/scoreboard.md` for what's been tried, and the current baseline `signaltrackers/regime_detection.py`.

2. **Choose what to try** — Based on what prior iterations explored (from the scoreboard), pick a different dimension to explore. Avoid repeating approaches already on the scoreboard.

3. **Research** — Use web search to find academic papers, implementations, and ideas related to the chosen approach.

4. **Implement** — Write a new method script to `signaltrackers/backtesting/methods/method_NNN_description.py` implementing the standard `classify_regime()` interface.

5. **Score** — Run the walk-forward scoring harness against the new method: `PYTHONPATH=signaltrackers python3 signaltrackers/backtesting/walk_forward_scorer.py methods/method_NNN_description.py`

6. **Record** — Append the results to `signaltrackers/backtesting/scoreboard.md`.

7. **No cleanup** — Keep the method script regardless of score. Never delete prior methods or modify the scorer.

### Loop Iteration Flow (Detailed)

```
Shell script starts Claude with "/regime-research" command
  │
  ├─ Claude reads docs/REGIME-BACKTEST-STRATEGY.md (this file)
  ├─ Claude reads signaltrackers/backtesting/scoreboard.md
  ├─ Claude reads signaltrackers/regime_detection.py (baseline)
  │
  ├─ Claude reviews scoreboard to see what's been tried
  │   └─ Picks a dimension NOT yet explored (algorithm, features, window, etc.)
  │
  ├─ Claude does web research on the chosen approach
  │
  ├─ Claude writes: signaltrackers/backtesting/methods/method_NNN_description.py
  │   └─ Must implement classify_regime(df_monthly, as_of_date) → dict | None
  │
  ├─ Claude runs: PYTHONPATH=signaltrackers python3 \
  │     signaltrackers/backtesting/walk_forward_scorer.py \
  │     signaltrackers/backtesting/methods/method_NNN_description.py
  │
  ├─ Claude reads the scorer output (JSON with mean, std, sharpe, fold scores, etc.)
  │
  ├─ Claude appends a new row to signaltrackers/backtesting/scoreboard.md
  │
  └─ Claude session ends
      │
Shell script waits N minutes, then starts next iteration
```

### What the Loop Can Try

Each iteration should explore a different dimension. The command file tells Claude to avoid repeating what's already on the scoreboard.

- **Different algorithms**: HMM (Hidden Markov Model), Gaussian Mixture Models, DBSCAN, spectral clustering, random forests on regime labels, logistic regression, neural nets
- **Different input features**: Add VIX, gold, dollar index, M2 money supply, CPI, consumer confidence. Remove features. Change feature engineering (momentum, rate of change, z-scores)
- **Different lookback windows**: 36 months, 48 months, 72 months, 120 months
- **Different number of regimes**: 3 instead of 4, or 5
- **Ensemble methods**: Combine multiple classifiers, voting systems
- **Different stress score formulations**: Change the centroid-to-regime mapping weights

### Scoreboard Format

File: `signaltrackers/backtesting/scoreboard.md`

```markdown
# Regime Detection Method Scoreboard

| # | Method | Walk-Forward Mean | Walk-Forward Std | Sharpe | Stability (avg months) | Plausibility | Script |
|---|--------|-------------------|------------------|--------|----------------------|--------------|--------|
| 0 | K-means baseline (5 FRED, 60mo window) | XX.X% | X.X% | X.XX | X.X | PASS | regime_detection.py |
| 1 | HMM 4-state | XX.X% | X.X% | X.XX | X.X | PASS | methods/method_001_hmm.py |
| 2 | ... | ... | ... | ... | ... | ... | ... |
```

### Method Script Location

All generated methods stored in: `signaltrackers/backtesting/methods/`

Naming: `method_NNN_short_description.py` (NNN is zero-padded, e.g., 001, 002)

Each script must implement a standard interface:

```python
def classify_regime(df_monthly: pd.DataFrame, as_of_date: pd.Timestamp) -> dict | None:
    """
    Classify the macro regime using only data available up to as_of_date.

    Args:
        df_monthly: DataFrame with all feature columns, monthly frequency,
                    indexed by date. Contains the full history — the method
                    MUST filter to only use data up to as_of_date.
        as_of_date: The "current" date for this evaluation. Only data on or
                    before this date may be used.

    Returns: {'regime': str, 'confidence': str, 'confidence_ratio': float}
    or None if insufficient data.

    Regime must be one of: 'Bull', 'Neutral', 'Bear', 'Recession Watch'
    Confidence must be one of: 'High', 'Medium', 'Low'
    """
```

**Critical rule:** Methods must NOT use any data after `as_of_date`. The walk-forward scorer passes the full DataFrame for efficiency, but the method must self-enforce the date boundary. Using future data would invalidate all results.

---

## Post-Loop Evaluation Pipeline

### Step-by-Step

```
1. Load scoreboard — all methods and walk-forward scores
2. Rank by walk-forward Sharpe ratio (mean / std)
3. Select top 5 methods
4. For each of top 5:
   a. Run CPCV (k=6, p=2, purge=3mo, embargo=1mo)
   b. Compute PBO
   c. If PBO > 0.5, flag as likely overfit
5. From surviving methods, select the winner (highest walk-forward Sharpe)
6. Apply Deflated Sharpe Ratio:
   - n_trials = total number of methods tested across ALL iterations
   - If p-value > 0.05, flag as potentially a statistical fluke
7. Run winner against 6-month holdout as final sanity check
8. Produce final comparison report
```

### Final Report

File: `signaltrackers/backtesting/results/final_evaluation.md`

Contents:
- Summary of all methods tested
- Top 5 candidates with walk-forward scores
- CPCV results and PBO for each
- DSR result for the winner
- Holdout performance
- Recommendation: adopt, investigate further, or stick with baseline

---

## Implementation Checklist

### Phase 1: Scoring Infrastructure

Build the walk-forward scoring harness that can evaluate any method implementing the standard interface.

- [ ] Create `signaltrackers/backtesting/walk_forward_scorer.py` — standalone script that:
  - Accepts a method script path as a CLI argument
  - Loads all feature data and scoring asset data
  - Runs the walk-forward expanding window (10 folds, 24-month test windows)
  - Handles per-fold asset availability and weight renormalization
  - Computes per-fold multi-asset accuracy scores
  - Applies regime stability check (avg regime duration ≥ 3 months)
  - Applies economic plausibility filter (hard-coded event checks)
  - Outputs results as JSON to stdout (mean, std, sharpe, fold scores, stability, plausibility)
  - Usage: `PYTHONPATH=signaltrackers python3 signaltrackers/backtesting/walk_forward_scorer.py path/to/method.py`
- [ ] Extract baseline k-means classifier from `regime_detection.py` into `signaltrackers/backtesting/methods/method_000_kmeans_baseline.py` using the standard interface
- [ ] Run baseline through the walk-forward scorer to establish the baseline score
- [ ] Create `signaltrackers/backtesting/scoreboard.md` with baseline entry
- [ ] Create `signaltrackers/backtesting/methods/` directory

### Phase 2: Automated Loop

Build the command file and shell script that drive the research loop.

- [ ] Create `.claude/commands/regime-research.md` — Claude command file that instructs one iteration:
  - Read this strategy doc, the scoreboard, and the baseline method
  - Review what's been tried, pick a new dimension to explore
  - Web search for research on the chosen approach
  - Implement as `signaltrackers/backtesting/methods/method_NNN_description.py`
  - Run the walk-forward scorer against it
  - Append results to the scoreboard
  - Keep the script regardless of score
- [ ] Create `scripts/regime-research-loop.sh` — Shell script that:
  - Accepts iteration count and wait time as arguments
  - Runs `claude --dangerously-skip-permissions -p "/regime-research"` in a loop
  - Logs output to `~/.claude/projects/financial/logs/regime-research.log`
  - Sleeps between iterations
- [ ] Test with 2-3 manual runs of `/regime-research` before running the loop
- [ ] Run the loop for 10-20 iterations

### Phase 3: Post-Loop Evaluation

Build the evaluation pipeline that applies CPCV and DSR to the top methods.

- [ ] Create `signaltrackers/backtesting/evaluate_top_methods.py` — script that:
  - Reads the scoreboard, ranks by walk-forward Sharpe ratio
  - Runs CPCV (k=6, p=2, purge=3mo, embargo=1mo) on top 5 methods
  - Computes PBO for each, flags any with PBO > 0.5
  - Applies Deflated Sharpe Ratio to the surviving winner (n_trials = total methods tested)
  - Runs winner against 6-month holdout as final sanity check
  - Outputs `signaltrackers/backtesting/results/final_evaluation.md`
- [ ] Install dependencies if needed (`pip install skfolio` or `timeseriescv`)
- [ ] Run the evaluation pipeline on all accumulated methods

### Phase 4: Decision

Review results and decide next steps. This phase is human-driven.

- [ ] Review `signaltrackers/backtesting/results/final_evaluation.md`
- [ ] Decide whether to adopt a new method or keep the baseline
- [ ] If adopting: replace classifier logic in `signaltrackers/regime_detection.py`
- [ ] Update any dependencies or configuration

---

## References

- Bailey & Lopez de Prado, "The Deflated Sharpe Ratio" (2014) — SSRN 2460551
- Bailey et al., "The Probability of Backtest Overfitting" (2015) — SSRN 2326253
- Lopez de Prado, "Advances in Financial Machine Learning" (2018) — Chapter 7 (Cross-Validation), Chapter 11 (Backtesting)
- Oliveira et al., arXiv 2503.11499 — Original k-means regime approach inspiration
- `skfolio` — CombinatorialPurgedCV implementation
- `timeseriescv` — CombPurgedKFoldCV implementation
