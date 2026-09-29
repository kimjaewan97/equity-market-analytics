# Measured results

Sample: 2023-01-03 to 2026-09-25 (936 shared sessions).
Returns are price returns on Yahoo Finance adjusted closes, in USD.
Sharpe uses a constant 4% risk-free rate. The equal-weight book is
rebalanced on the first session of each month and is gross of costs.

| Name | Ann. return | Ann. vol | Sharpe | Max DD | Beta | Alpha |
|---|---:|---:|---:|---:|---:|---:|
| Apple | 31.7% | 25.8% | 1.04 | -33.4% | 1.08 | 8.4% |
| Microsoft | 24.0% | 26.4% | 0.80 | -34.5% | 1.02 | 3.3% |
| NVIDIA | 110.3% | 48.1% | 1.70 | -36.9% | 2.06 | 58.2% |
| Amazon | 33.4% | 32.6% | 0.92 | -30.9% | 1.42 | 5.5% |
| ASML | 37.7% | 41.5% | 0.89 | -45.5% | 1.73 | 6.7% |
| SAP | 22.8% | 29.6% | 0.71 | -52.3% | 0.87 | 5.9% |
| JPMorgan Chase | 31.6% | 23.0% | 1.14 | -24.4% | 0.88 | 11.5% |
| Shell | 20.3% | 21.4% | 0.79 | -18.5% | 0.42 | 9.9% |
| Novo Nordisk | -11.9% | 41.2% | -0.19 | -74.7% | 0.75 | -18.9% |
| S&P 500 ETF | 22.5% | 14.9% | 1.17 | -18.8% | — | — |
| Equal-weight book | 34.7% | 19.3% | 1.44 | -22.1% | 1.14 | 8.4% |
| Equal-weight book, ex-NVIDIA | 26.6% | 17.7% | 1.20 | -21.5% | 1.02 | 3.7% |

Reading the table:

* The equal-weight book annualized 34.7% versus 22.5% for SPY, with a Sharpe of 1.44 versus 1.17.
* Dropping NVIDIA cuts the equal-weight annualized return to 26.6% (Sharpe 1.20). The outperformance is not a broad, balanced result.
* NVIDIA was the strongest single name at 110.3% annualized.
* The deepest single-name drawdown was Novo Nordisk at -74.7%.
* Beta and alpha are from a daily excess-return regression on SPY. Alpha is annualized and is not a claim of skill after costs or taxes.
