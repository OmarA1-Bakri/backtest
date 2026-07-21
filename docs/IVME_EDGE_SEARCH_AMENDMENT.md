# IVME Edge Search Amendment

## Purpose

The objective is not limited to validating the previous strict IVME engine and the three frozen candidate mechanisms. The research program may explore additional bounded, causally valid strategy permutations where they materially improve the probability, expectancy, stability, sample size, or execution robustness of an edge.

The previous strict strategy and the three frozen candidates remain immutable benchmark families. Any expanded strategy must be recorded as a separate trial family and may not rewrite the historical primary specifications.

## Permitted feature families

Additional features may be used as context, setup, trigger, or risk-management variables when they are computable causally from completed data and demonstrate incremental walk-forward value. Permitted examples include, but are not limited to:

- confirmed higher-high, higher-low, lower-high, and lower-low sequences;
- swing slope, breakout distance, pullback depth, and structural efficiency;
- SMA, EMA, anchored VWAP, moving-average slope, and price-to-average distance;
- ATR, realized volatility, volatility expansion and contraction;
- volume, quote volume, relative volume, taker-flow fields where available;
- trend strength, range compression, close location, candle efficiency, and session context;
- BTC-to-TAO beta, lagged response, and relative-strength features;
- time-of-day or day-of-week context only when predeclared and supported by adequate samples.

These features must not be added as arbitrary confirmation stacking. Each must have a defined role and must pass an incremental-information ablation against the simpler parent strategy.

## Search methodology

1. Generate bounded, interpretable permutations from predeclared feature families and parameter grids.
2. Freeze the search space, fold schedule, cost model, seeds, and trial count before opening validation outcomes.
3. Perform selection only inside training and validation windows. Never select on the final chronological test fold.
4. Use nested or sequential walk-forward evaluation where practical.
5. Rank candidates using a composite training objective rather than win rate alone. The objective should consider:
   - net expectancy;
   - dependency-adjusted sample size;
   - profit factor;
   - win rate;
   - drawdown;
   - cost robustness;
   - fold stability;
   - concentration risk.
6. The 70% net win-rate threshold remains a qualification gate. It must not become the direct optimization target.
7. Use ablations to establish whether each added feature improves the parent mechanism after costs.
8. Apply full multiple-testing disclosure and Deflated Sharpe adjustment using every attempted primary, variant, placebo, control, and sensitivity trial.
9. Reject fragile candidates that succeed only on one asset, side, fold, regime, threshold point, or a handful of trades unless explicitly reported as such.
10. Continue iterative search until either:
    - a stable, economically viable candidate survives all predeclared gates; or
    - the bounded search space is exhausted and the evidence supports rejection.

## Permutation families

The research runner may create additional families around:

- value-migration plus directional structure;
- value-migration plus moving-average slope or distance;
- failed price discovery plus trend or range context;
- BTC-led TAO residual response plus TAO structure or volatility state;
- trend continuation using HH/HL or LH/LL state with pullback location;
- moving-average regime plus structural trigger;
- volatility compression followed by causal expansion and retest;
- mean reversion only when value location and failed continuation are explicit.

Each expanded family must retain one clear causal mechanism. Combining many weak indicators into a conjunctive rule is prohibited.

## Hard gates

A candidate is viable only when it has:

- deterministic, non-repainting implementation;
- next-minute executable semantics;
- realistic base and stress costs;
- adequate dependency-adjusted sample size;
- positive net expectancy and profit factor;
- positive clustered-bootstrap lower bound;
- corrected permutation significance;
- acceptable Deflated Sharpe probability;
- broad fold and sensitivity stability;
- no excessive best-fold or best-trade concentration;
- faithful Pine representation, or an explicit Python-only limitation.

A candidate that is profitable but fails the 70% qualification threshold must still be reported as a potentially useful development edge, not discarded or misrepresented.

## Runner discipline

All permutation code, fixtures, schema tests, causal tests, accounting tests, and reduced-data smoke tests must pass locally before a paid GitHub Actions run. Related permutations must be consolidated into as few full-data runner activations as practical.
