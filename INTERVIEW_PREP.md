# Interview Preparation — Fraud Detection & Transaction Risk Scoring

Answers are written to be said out loud. Wherever a number is needed, quote it from `outputs/model_results/key_results.json`. Never quote a number you didn't get from the project.

---

## Basic

**What problem does this project solve?**
It ranks every transaction by fraud risk and turns that ranking into a decision: approve, monitor, verify or hold. The thresholds are chosen to minimise the total cost of missed fraud plus reviews, not to maximise a textbook metric.

**Why fraud detection?**
It is a core risk-management problem for any lender or payments business. It also brings together everything a risk analytics role needs: messy real data, severe imbalance, time effects, a cost trade-off and a need to explain decisions.

**Why is fraud detection difficult?**
- Fraud is rare (about 3.5% here), so there are few positive examples.
- Fraudsters change behaviour over time, so patterns drift.
- The two types of error have very different costs.
- Labels arrive late and are sometimes wrong.
- Decisions have to be explainable to operations teams, customers and regulators.

**Why is accuracy misleading?**
A model that never predicts fraud is about 96.5% accurate on this data and catches nothing. Accuracy is dominated by the easy majority class. I use PR-AUC, recall and precision instead, and finally cost.

---

## Technical

**Why Logistic Regression?**
It is the standard, interpretable baseline in credit and fraud risk. Every coefficient shows direction and strength. It is fast and stable, and it tells me how much the more complex models actually add.

**Why Random Forest?**
It captures non-linear effects and interactions, such as "new card AND high amount AND anonymous email", without manual feature crosses. It is also robust to outliers and needs little tuning. Averaging many trees reduces the instability of a single tree.

**Why Gradient Boosting as a fourth model?**
It is what most fraud and credit teams use on large tabular data. It is fast and usually the most accurate. I only keep it if it beats Random Forest on validation PR-AUC.

**Why class weights?**
Without weights the model minimises overall error. That means it barely tries on the rare class, so recall at the default threshold is very low. `class_weight="balanced"` makes each fraud count as much as many legitimate transactions during training. It mainly shifts scores upwards; the ranking (PR-AUC) changes much less. That is why I still tune the threshold afterwards.

**Why PR-AUC?**
It summarises precision and recall across all thresholds, and it focuses on the positive class. ROC-AUC uses the false positive rate, which stays tiny because there are so many legitimate transactions. So ROC-AUC can look excellent while most alerts are false. PR-AUC exposes that. The baseline for PR-AUC is the fraud rate (~0.035), not 0.5.

**Why not SMOTE?**
SMOTE creates synthetic fraud by interpolating between two real fraud rows. My features describe a specific customer's past behaviour at a specific time. A point halfway between two customers' histories is a transaction that could never exist. With about 20k real fraud cases, I don't lack examples. Class weights plus threshold tuning achieve the same goal without inventing data.

**How did you avoid data leakage?**
1. **Time-based split.** Train on earlier months, validate on the next period, test on the last period.
2. **Past-only history features.** Data is sorted by time. Counts use `cumcount`, average amount subtracts the current amount from the running sum, and the 24-hour window looks only backwards. A customer's first transaction always has count 0, and the notebook checks this.
3. **Cut-offs from training only.** Quiet hours and the high-value threshold are computed from the training period.
4. **Labels are never used in features.** Thresholds are chosen on validation, and test is used once.

**How did you choose the threshold?**
On the validation period I calculated, for every threshold, the total cost: fraud amount missed plus alerts × review cost. The High threshold is the one with the lowest cost. The other tiers use a recall target (Medium catches 80% of fraud) and a precision target (Critical alerts are ≥80% fraud).

**How is the risk score calculated?**
Risk score = model score × 100, and the tier depends on which cut-off it crosses. Because of class weighting, it is a ranking score, not a true probability. That is why every cut-off was set on validation data.

**How do you explain a single decision?**
With reason codes. For the flagged transaction I replace each feature, one at a time, with its typical legitimate value and see how much the score falls. The largest drops are the reasons, for example "email mismatch", "new card" or "3 transactions in the last 24 hours". This works for any model. It mirrors adverse-action reason codes in lending.

---

## Business

**What happens if recall is increased?**
The threshold goes down. More fraud is caught and fraud losses fall, but alerts rise, precision falls, more genuine customers are interrupted and the review team needs more capacity.

**What happens if precision is increased?**
The threshold goes up. Fewer false alerts mean a better customer experience and lower review cost, but more fraud slips through and the loss is the full transaction amount.

**What is the cost of a false positive?**
Analyst time or an OTP/call-back, customer friction, abandoned purchases and possible churn. In the project it is a flat assumed $10 per alert, with sensitivity from $2 to $50.

**What is the cost of a false negative?**
The transaction amount is lost, plus chargeback fees, investigation cost and reputational or regulatory exposure. In the project it is the transaction amount, which is a conservative estimate.

**How would a bank actually use this model?**
It would score each transaction in real time and route it by tier: auto-approve, monitor, step-up authentication, or hold. Analysts would work an alert queue sorted by score, using reason codes to investigate faster. Thresholds would be reviewed with the risk team as costs, capacity and risk appetite change.

**How would you monitor it after deployment?**
- **Weekly:** PSI (population stability) on the score and key features to detect drift.
- **Alert volume and precision:** investigators confirm fraud quickly, so these can be tracked early.
- **Monthly, once chargebacks arrive:** recall and PR-AUC on matured labels.
- **Cost against the baseline.**
- **Retraining:** on a schedule, or when PSI or performance crosses a trigger.

---

## Project defence — hard follow-up questions

**"Your customer ID is made up. Isn't everything built on it wrong?"**
It's a proxy, and I say so. Card, billing address and card start date together identify a card-holder quite well. If the proxy merges two people, their history features become noisier, which weakens the model rather than inflating results. The time-based test still measures honest performance.

**"You dropped 390+ columns. Aren't you leaving accuracy on the table?"**
Yes, knowingly. The V columns are masked, and I couldn't explain them to a risk committee. Adding them is listed as a future experiment, measured as accuracy gained versus interpretability lost.

**"Why is validation performance different from test?"**
The test period is later, and fraud patterns drift. The time-based split shows that honestly; a random split would hide it. A gap is a finding: it means the model needs monitoring and periodic retraining.

**"How do you know the model isn't overfitting?"**
I compare train and validation PR-AUC for every model in the comparison table. I also limit tree depth and minimum leaf size, and I keep test untouched until the very end.

**"Why $10 per review?"**
It's an assumption, and I show what happens from $2 to $50. The point is the method: a real team would plug in their actual review cost and loss data.

**"Would this work for loan fraud at an NBFC?"**
The framework transfers directly: ranking model, cost-based threshold, tiers and reason codes. The features would change to application data: identity mismatches, velocity of applications from the same device, phone or address, bureau inconsistencies and income-document signals. The time-based validation and leakage rules stay the same.

**"Why not deep learning or an LLM?"**
On structured tabular data, tree ensembles are usually as good or better, faster and easier to explain. There is no text or image data here that would justify them. I'd rather add explainability and monitoring than complexity.

**"Your scores near 100 all look the same. How do you rank them?"**
At the extreme top the model saturates. Those cases go straight to manual review anyway, so their order matters less. The reason codes can also be weak there, because changing one feature isn't enough to lower a saturated score. That's a known limitation of one-at-a-time explanations.

**"Why SQL if you already have pandas?"**
In practice the data lives in a warehouse, and analysts answer most monitoring questions in SQL. The queries mirror the Python analysis, including a window function that computes the customer's average of earlier transactions only, the same no-leakage rule written in SQL.

**"Why is PR-AUC for a random model equal to the fraud rate?"**
A random model's precision at every recall level equals the share of positives in the data, so its PR curve is a flat line at the fraud rate.
