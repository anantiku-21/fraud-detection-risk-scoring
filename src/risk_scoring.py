import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

from feature_engineering import ALL_FEATURES, NUMERIC_FEATURES

# Illustrative workflow for this project, not a real institution's policy
RISK_ACTIONS = {
    "Low": "Approve automatically",
    "Medium": "Approve, but monitor the account",
    "High": "Step-up verification (OTP / call-back)",
    "Critical": "Hold transaction for manual review",
}


def expected_cost(y_true, scores, amounts, threshold, review_cost):
    """Cost of fraud we miss (we lose the amount) + cost of reviewing every alert."""
    flagged = scores >= threshold
    missed_fraud = (y_true == 1) & ~flagged

    fraud_loss = amounts[missed_fraud].sum()
    review_spend = flagged.sum() * review_cost
    return fraud_loss + review_spend


def cost_curve(y_true, scores, amounts, review_cost, thresholds=None):
    if thresholds is None:
        thresholds = np.arange(1, 100) / 100

    rows = []
    for threshold in thresholds:
        flagged = scores >= threshold
        caught = ((y_true == 1) & flagged).sum()
        rows.append({
            "threshold": threshold,
            "alerts": flagged.sum(),
            "alert_rate": flagged.mean(),
            "recall": caught / (y_true == 1).sum(),
            "precision": caught / flagged.sum() if flagged.sum() > 0 else np.nan,
            "total_cost": expected_cost(y_true, scores, amounts, threshold, review_cost),
        })
    return pd.DataFrame(rows)


def choose_tier_thresholds(y_true, scores, amounts, review_cost,
                           medium_recall=0.80, critical_precision=0.80):
    """Derive the three tier cut-offs from validation data instead of picking round numbers."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    # precision/recall have one more element than thresholds; drop the last point
    precision, recall = precision[:-1], recall[:-1]

    # Medium: the highest threshold that still catches `medium_recall` of fraud
    meets_recall = thresholds[recall >= medium_recall]
    medium = meets_recall.max() if len(meets_recall) > 0 else thresholds.min()

    # High: the threshold with the lowest total business cost
    costs = cost_curve(y_true, scores, amounts, review_cost)
    high = costs.loc[costs["total_cost"].idxmin(), "threshold"]

    # Critical: the lowest threshold where alerts are mostly real fraud.
    # If the model never gets that precise, fall back to the top 0.5% of scores.
    meets_precision = thresholds[precision >= critical_precision]
    if len(meets_precision) > 0:
        critical = meets_precision.min()
    else:
        critical = np.quantile(scores, 0.995)

    # Keep the tiers in order even if the rules above overlap
    medium = min(medium, high)
    critical = max(critical, high)

    return {"medium": float(medium), "high": float(high), "critical": float(critical)}


def assign_tier(score, tier_thresholds):
    if score >= tier_thresholds["critical"]:
        return "Critical"
    if score >= tier_thresholds["high"]:
        return "High"
    if score >= tier_thresholds["medium"]:
        return "Medium"
    return "Low"


def typical_values(train_df):
    """What a 'normal' legitimate transaction looks like: median for numbers, most common category."""
    legit = train_df[train_df["isFraud"] == 0]
    typical = {}
    for col in ALL_FEATURES:
        if col in NUMERIC_FEATURES:
            typical[col] = legit[col].median()
        else:
            typical[col] = legit[col].mode()[0]
    return typical


def explain_transaction(model, transaction, typical, top_n=3):
    """
    Reason codes: replace one feature at a time with its typical value and see how much
    the model score drops. The biggest drops are the factors driving this transaction's risk.
    """
    base_score = model.predict_proba(transaction[ALL_FEATURES])[0, 1]

    what_if_rows = []
    for col in ALL_FEATURES:
        changed = transaction[ALL_FEATURES].copy()
        changed[col] = typical[col]
        what_if_rows.append(changed)
    what_if = pd.concat(what_if_rows, ignore_index=True)
    what_if_scores = model.predict_proba(what_if)[:, 1]

    reasons = pd.DataFrame({
        "feature": ALL_FEATURES,
        "value": [transaction[col].iloc[0] for col in ALL_FEATURES],
        "typical_value": [typical[col] for col in ALL_FEATURES],
        "score_drop": base_score - what_if_scores,
    })
    # Ignore features whose effect is negligible
    reasons = reasons[reasons["score_drop"] > 0.001]
    return reasons.sort_values("score_drop", ascending=False).head(top_n)
