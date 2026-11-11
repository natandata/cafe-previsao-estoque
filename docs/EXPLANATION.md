# Café forecasting and perishable stock

Implementation and study document, published version dated 11 November 2026. Project 8 of the guide. Independent code with AI assistance and original synthetic data. This is neither a reproduction of the reference author's results nor a real café deployment. Project 10, the operations platform, is separate.

## 1. The implemented decision

A sales forecast becomes operational only after conversion to a purchasable unit and a replenishment rule. This project forecasts two drinks, converts their quantities to milk ml, then compares fixed purchases with a reorder-point policy under lead time, expiry, in-transit stock and lost demand.

The question is which simple method predicts better and what follows when it drives an explicit policy, not which model is most sophisticated. There is no neural network, financial optimum or claim of waste reduction. Weekly seasonal naive wins the constructed dataset; this is reported rather than hidden.

The history covers 600 calendar days,1 January 2024 to 22 August 2025, with two drinks and 1,200 day/item records. It is historical simulation, not current November 2026 trading.460 initial days precede 84 validation days and 56 final test days. Data seed is 20261111.

## 2. Measured results

Validation MAE for café com leite is 5.02 units for seasonal 7,19.54 for moving 7 and 19.16 for ses 025. Cappuccino validation errors are 4.67,12.72 and 12.59. A winner is selected for each item on validation and frozen before the final test.

Final test MAE is 5.18 units and WAPE 8.05% for café com leite;4.43 units and 11.41% for cappuccino. These errors describe fictional demand with weekly seasonality, noise and mild trend, not real restaurant performance or universal superiority of the weekly baseline.

Simulation uses 200 paths per scenario,90 days per path, leads of 2 and 5 days, nominal services 90% and 97.5%, and two policies: eight scenarios and 1,600 stock simulations. Policies receive the same demand paths, keeping policy differences separate from random-demand differences.

At lead 2/service 97.5%, replenishment serves 98.05% of demand with 13.26 L average stock; fixed purchasing serves 99.64% with 18.92 L. Replenishment holds less but loses more demand. It does not dominate all metrics.

At lead 5/service 97.5%, replenishment serves 96.55%, below its nominal input, with 17.71 L average stock. Cycle service, fill rate, weekly seasonality and discrete review are different concepts. The formula's service input must not be sold as an achieved guarantee.

## 3. Module map

`generate()` creates data, `validate_daily()` enforces observation contracts, `forecast()` implements three methods and `backtest()` materializes predictions by temporal origin. `Policy` validates stock parameters, `levels()` computes levels and `simulate()` runs a path. `run()` coordinates selection, final testing, next-week forecast and scenarios.

`src/common.py` writes artifacts and plots. `app.py` provides local controls for language, drink, method, lead, shelf life, nominal service and seed. The notebook reuses source functions.38 automated tests include manual calculations, invariants and edge cases.

Separation keeps prediction, evaluation and display from changing one another silently. Stock can be tested against a handwritten demand list without the entire generator, and a forecast against seven values without opening Streamlit.

## 4. Data contract

Each row has `date`, `item`, `quantity`, `is_open` and `observed`. The key is date/item. Quantity represents demanded and served drink units in the synthetic history. Historical sales equal demand by assumption: real stockouts can censor sales and would require another approach.

`observed=True` means collection occurred; `is_open=False` means a known closure. Sundays are closed and therefore explicitly zero. Missing rows are not zero-filled. Validation rejects missing day/item records, unobserved data, duplicates, absent recipes, negative/fractional/nonfinite quantities and sales on known closed days.

The full calendar is required between minimum and maximum dates present for both items. If both drinks were cut together before the minimum date, the function cannot infer the missing external period. Expected extraction boundaries would need a separate source contract. Internal consistency is not knowledge of an unspecified external dataset.

No customers, addresses, couriers, reviews or third-party operational exports are used. The reference project's Cafe Sales Dataset and CSVs were neither downloaded nor redistributed. Original generators avoid relying on permission over somebody else's business data.

## 5. Generation assumptions

A local NumPy Generator produces each drink's level, weekly multiplier, small trend, smooth 90-day cycle and rounded normal noise. Friday and Saturday multipliers are larger, Sundays close and negative counts are clipped to zero. The design deliberately gives methods different behaviors.

Weekly structure favors the weekly baseline. That is an educational choice, not a claim about all cafés. Real evaluation would need holidays, promotions, price changes, weather forecasts available at issue time, capacity and stockout periods. A seed repeats draws under a declared environment; it does not establish the assumptions as facts.

The implementation ran on Python 3.10.12 and 3.12.15 with NumPy 2.2.6, pandas 2.3.3 and matplotlib 3.10.9. Runtime performs no network requests. A network may be needed only to install missing dependencies.

## 6. Forecast formulas

`seasonal7` repeats the final seven observations in order. History ending `[10,20,30,40,50,60,0]` forecasts the same next week. A ten-day horizon repeats the first three entries after that week. It never substitutes real future values inside the issued forecast.

`moving7` repeats the mean of the last seven known observations. It removes the Saturday/Sunday contrast and therefore performs poorly on this generator. It does not recompute using tomorrow's actual sale during today's seven-day forecast.

`ses025` initializes level with the first observation, then updates `level = 0.25 * actual + 0.75 * previous_level`. The horizon is constant. Alpha 0.25 was fixed as part of the experiment, not tuned on final test. The method follows level but does not explicitly model weekly seasonality.

All methods require a one-dimensional finite, nonnegative history of at least seven values and a positive integer horizon. Output is nonnegative. A new item with insufficient history fails explicitly; a cold-start fallback would need its own business rule and tests.

## 7. Temporal evaluation

`backtest(values,start,stop,method,horizon=7)` creates nonoverlapping forecast origins. At each origin it passes only `values[:origin]` to the method and issues the entire next block. Only at the next origin can observations that have now become past enter the history. Output stores origin, target index, actual, forecast and method.

There are 12 validation weeks and 8 test weeks. Later test origins can use actuals from earlier test weeks, as operational weekly updates would. This is not a 56-day forecast issued on the first test day. Documentation and chart labels preserve that distinction.

A test dramatically changes future values and verifies the previous origin's forecasts remain unchanged. Other tests check origin/target ordering, unique target coverage, partial horizons and boundaries. These are concrete leakage checks rather than only a declaration that the model is temporal.

Validation selects minimum MAE with deterministic name tie-breaking. Only the selected method is evaluated on final test. Once evaluation is complete, that already chosen method uses all completed history for a next-week demonstration. That updated projection is not passed off as another evaluated test.

## 8. Metrics

MAE is mean absolute observed-minus-predicted error. It is measured in drink units:5.18 means around five units of average daily absolute error, not 5.18% or a maximum error. Individual days may be worse.

WAPE divides total absolute error by total absolute observed volume. MAPE is avoided because closed Sundays have zero quantity. If the whole denominator is zero, WAPE returns no percentage rather than dividing by zero; JSON output rejects silent NaN.

Forecast metrics do not encode asymmetric shortage and excess costs. Equal-MAE models could yield different stock behavior if one consistently underpredicts peaks. The simulation studies that decision layer, still under simplified assumptions.

## 9. Drinks to ingredient

Recipes specify 80 ml per café com leite and 180 ml per cappuccino. Daily milk forecast is `80 * cafes + 180 * cappuccinos`. One drink is not treated as one unit of purchased ingredient. Simulation uses integer ml and display divides by 1,000 for liters.

Ten cafés com leite plus five cappuccinos require 1,700 ml, or 1.7 L. Changing a drink recipe changes milk purchasing even if the drink forecast stays unchanged. This is why the recipe is separate from demand forecasting.

Only milk is modeled. There are no beans, sugar, packaging, multiple suppliers or fridge capacity. Shelf life is fixed from arrival and does not distinguish open from sealed milk. This is not a complete procurement system.

## 10. Reorder point and target

Mean daily milk comes from the aggregated next-week forecast. Uncertainty is the standard deviation of aggregated validation errors, preserving drink co-movement. For leadL and normal quantilez from the nominal service input, safety stock is `z * std * sqrt(L)`. Reorder point is `mean * L + safety`, rounded up to ml.

The order-up-to target covers lead plus review intervalR: `mean * (L+R) + z * std * sqrt(L+R)`. Review is daily. When inventory position is at or below the reorder point, purchasing fills to target. Position includes stock on hand plus pipeline; ignoring pipeline would repeatedly purchase the same requirement.

Manual zero-uncertainty case:100 ml daily mean, two-day lead and daily review yield 200 ml reorder point and 300 ml target. Tests verify exact values and increasing protection with higher service or longer lead.

The normal approximation simplifies accumulated error. It does not exactly capture weekly closure, autocorrelation or discrete review. Cycle-service input is not the fraction of volume served. Simulation measures resulting behavior rather than assuming the input percentage was achieved.

## 11. Event sequence and balance

Each day receives scheduled arrivals, expires lots, serves demand by earliest expiry, calculates position and orders. Today's purchase arrives only after lead time. There is no instant delivery or negative stock.

A lot arriving on daya expires at the beginning of day `a+shelf_days`. One-day shelf life permits consumption on arrival day and expires next morning. This convention is explicit and tested; changing it changes waste.

FEFO means first expired, first out. Lots are sorted by expiry before consumption. Unserved demand is lost sales, not backlog. The simulator does not promise tomorrow's delivery for a drink not bought today.

Initial stock equals target, has expiry and counts as purchased. It is not free inventory used to favor a policy. Final on-hand and pipeline quantities are also counted. The exact invariant is purchased = consumed + expired + ending on-hand + ending pipeline.

## 12. Demand paths

After model selection, each drink's validation errors are multiplied by its recipe and summed by index. This preserves observed error co-movement.84 aggregated daily errors form 12 weekly blocks. Each 90-day path samples whole error weeks and adds them to a repeated next-week forecast; results are rounded and clipped to zero.

Block bootstrap preserves some within-week dependence, not all cross-week behavior or unseen extremes. The 90-day scenario repeats one week's profile rather than forecasting a 90-day future trend. Its percentiles describe 200 synthetic paths, not externally validated confidence guarantees.

Path seed is 20261119. Paths are sampled once and shared by all policies for paired comparison. Final-test errors do not calibrate uncertainty: residuals come only from validation, although the deployment demonstration can use the entire completed history for its forecast.

## 13. Fixed policy and fair comparison

The fixed policy buys mean forecast demand at every review with no extra protection in order quantity. Within each scenario it starts with the same target, lead, expiry and demand as replenishment. Initial target changes with service across scenarios, so comparisons across different service settings change more than the policy.

Metrics include fill rate, stockout days, lost ml, waste, average end-of-day stock, purchased ml and ending on-hand/pipeline. Fill rate is `1-lost/demand`. A zero-demand path returns 1 by convention. Stockout days count days, not customers or lost drinks.

The 5 th/95 thfill-rate percentiles describe spread among simulated paths. They are not nominal service or a validated real-world probability interval. Real decisions would need more seeds, distribution changes and recent operational data.

Illustrative purchase cost is 1 cent/ml, or BRL 10/L, and lost margin is 2 cents/ml, or BRL 20/L. Holding cost, order fees, tax, salvage and post-opening shelf life are absent. Expired milk is not charged again on top of purchase cost, avoiding double-counting. No profit or economic optimum is asserted.

## 14. Interactive exploration

Offline HTML is the frozen report. Streamlit allows drink and method selection followed by 50-path simulation with configurable lead, shelf life, service and seed. Interactive exploration is separate from the versioned 200-path evaluation. A selector does not rewrite the validation winner.

Labels distinguish drink units, milk ml in traces, liters in summaries and days for lead/expiry. The default 50-path interface result of 97.7% is not interchangeable with the 200-path table at 97.5% nominal service. Parameters and seed must match when comparing outputs.

The app downloads local results but issues no supplier order. It uses no account, payment, GitHub publication or remote prediction service. It binds to localhost with Streamlit usage statistics disabled. Exposing the port would require a separate security and privacy review.

## 15. The 38 tests

Generation/contract tests cover seed, complete calendar, duplicates, collection, negative/fractional values, closure and missing recipes. Forecast tests cover small exact formulas, short histories, invalid methods, future invariance, origins, partial horizons and evaluation boundaries.

Policy tests cover manual levels, larger safety with service/lead and invalid settings. Simulation tests cover zero demand, nonnegative stock, mass balance, lost sales, delayed arrival, expiry, served-plus-lost identity, repetition, invalid ml, FEFO, empty paths, identical demand between policies, pipeline and purchase cost.

A real first-version bug appeared on empty demand: an empty DataFrame had no declared columns and failed before reporting initial stock. Declaring output columns even when there are no rows fixed it and the regression test passes.

Tests ran on Python 3.10.12 and 3.12.15. UI checks exercised PT/EN, lead 5/shelf 3 and method changes, with pixel inspection at 320/390/1280. This project was not installed on the Dell and has no real-data, native-Windows, load, accessibility or sanitary validation.

## 16. Reproduction

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.pipeline
```

On PowerShell, use `.venv\Scripts\python.exe` if activation is blocked rather than changing global execution policy. Native Windows is untested; Linux Python 3.10 and 3.12 were executed.

Install `requirements-app.txt` and run `python -m streamlit run app.py` for the app. Install `requirements-notebook.txt` and execute notebook cells in a new session; it imports source rather than loading a third-party model binary. Pipeline outputs include synthetic daily data, validation/test predictions, scenarios, metrics, plots and HTML.

`forecast_next7.csv` projects 23 to 29 August 2025 after synthetic history, not current-date purchasing. `simulation_trace_path0.csv` contains path 0 for each scenario. Other simulation files contain the 200 path summaries; source and seed regenerate additional traces if needed.

## 17. Changing the implementation

Change `RECIPES_ML` to alter a recipe, verify the unit conversion and rerun tests/pipeline. New drinks need a complete daily series and aligned error dates. A drink without milk should not be assigned invented milk consumption just to fill a column.

Changing horizon means revisiting the temporal issue protocol and metric meaning. Daily issue with daily actual updates differs from this weekly experiment. If tuning smoothing alpha, use train/validation, never the final test for search.

Variable lead time needs explicit arrival modeling using only information available when ordering. Fridge capacity needs purchase delay/rejection and recorded waste, not silent stock clipping. Pack sizes need rounding to purchase multiples and renewed balance checks.

Multiple ingredients require recipe vectors and separate units, shelf lives, costs and suppliers; drink availability then depends on all required ingredients. That is a larger operations problem and is not quietly claimed as finished here.

## 18. Explaining it in an FDE interview

Start with keeping material available without excessive perishables. Show why sales forecasts need recipes, missing collection is not zero, and stock event order matters. Open a manual test, a three-day trace and the balance identity.

Report that the baseline won and lower inventory came with more lost demand. This measured trade-off is more defensible than selecting a convenient metric. A real pilot needs source contracts, stockout observation, real costs/lead/expiry, owners and limits on automatic decisions.

Do not claim real waste reduction or production purchasing deployment. Describe a reproducible assisted implementation whose limitations you can explain. Documentation supports understanding rather than replacing code review.

## 19. Credits and publication

Thematic inspiration: https://github.com/AmirhosseinHonardoust/Cafe-Demand-Forecasting-Reorder-Simulator . No author files, dataset, implementation or results were copied. Concept names do not imply literal software reproduction. Dependencies keep separate licenses; Inter's SIL OFL is bundled.

Public repository `natandata/cafe-previsao-estoque`, published after name and content approval on 11 November 2026. No original-code reuse license has been added. The private manual is not bundled and this work made no changes to the owner's Dell.

Technical sources: https://numpy.org/doc/stable/reference/random/generator.html ; https://pandas.pydata.org/docs/reference/api/pandas.date_range.html ; https://docs.python.org/3/library/statistics.html#statistics.NormalDist . Leakage guidance also follows https://scikit-learn.org/stable/common_pitfalls.html , although these baselines do not require scikit-learn.
