import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR / "src"))

from feature_engineering import ALL_FEATURES
from risk_scoring import RISK_ACTIONS, assign_tier, explain_transaction, cost_curve

RESULTS_DIR = PROJECT_DIR / "outputs" / "model_results"
TIER_ORDER = ["Low", "Medium", "High", "Critical"]

st.set_page_config(page_title="Fraud Risk Monitor", layout="wide")


@st.cache_resource
def load_model():
    return joblib.load(RESULTS_DIR / "model_bundle.joblib")


@st.cache_data
def load_data():
    scored = pd.read_csv(RESULTS_DIR / "scored_test_transactions.csv")
    features = pd.read_csv(RESULTS_DIR / "test_features.csv")
    with open(RESULTS_DIR / "key_results.json") as f:
        key_results = json.load(f)
    return scored, features, key_results


bundle = load_model()
scored, features, key_results = load_data()
model = bundle["model"]
tiers = bundle["tier_thresholds"]

st.title("Fraud Detection & Transaction Risk Scoring")
st.caption(
    f"Test period: {len(scored):,} transactions (last 15% of the timeline, never used for training). "
    f"Model: {bundle['model_name']}."
)

page = st.sidebar.radio("Section", ["Overview", "Fraud Analysis", "Risk Monitoring", "Transaction Scoring"])

# ------------------------------------------------------------------ Overview
if page == "Overview":
    flagged = scored["risk_tier"].isin(["High", "Critical"])
    fraud = scored["isFraud"] == 1

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Transactions", f"{len(scored):,}")
    col2.metric("Fraud transactions", f"{fraud.sum():,}")
    col3.metric("Fraud rate", f"{fraud.mean():.2%}")
    col4.metric("Total amount", f"${scored['TransactionAmt'].sum():,.0f}")
    col5.metric("Flagged (High + Critical)", f"{flagged.sum():,}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Test PR-AUC", f"{key_results['test_pr_auc']:.3f}")
    col2.metric("Recall at Decision Threshold", f"{key_results['test_recall']:.1%}")
    col3.metric("Precision at Decision Threshold", f"{key_results['test_precision']:.1%}")
    col4.metric("Fraud value caught", f"{key_results['test_fraud_value_caught_pct']:.1%}")

    st.subheader("Model comparison (validation period)")
    comparison = pd.read_csv(RESULTS_DIR / "model_comparison.csv", index_col="model")
    st.dataframe(comparison[["train_pr_auc", "val_pr_auc", "val_roc_auc", "overfit_gap"]].round(4))

# ------------------------------------------------------------------ Fraud Analysis
elif page == "Fraud Analysis":
    scored["week"] = scored["day"] // 7
    scored["amount_band"] = pd.cut(scored["TransactionAmt"], bins=[0, 25, 100, 500, 1000, np.inf],
                                   labels=["<25", "25-100", "100-500", "500-1000", "1000+"])

    st.subheader("Weekly fraud rate")
    st.line_chart(scored.groupby("week")["isFraud"].mean())

    col1, col2 = st.columns(2)
    col1.subheader("Fraud rate by product")
    col1.bar_chart(scored.groupby("ProductCD")["isFraud"].mean())
    col2.subheader("Fraud rate by amount band")
    col2.bar_chart(scored.groupby("amount_band", observed=True)["isFraud"].mean())

    col1, col2 = st.columns(2)
    col1.subheader("Fraud rate by hour (relative)")
    col1.bar_chart(scored.groupby("hour")["isFraud"].mean())
    col2.subheader("Fraud rate by email provider")
    col2.bar_chart(scored.groupby("email_group")["isFraud"].mean())

# ------------------------------------------------------------------ Risk Monitoring
elif page == "Risk Monitoring":
    st.subheader("Risk score distribution")
    score_bins = pd.cut(scored["risk_score"], bins=np.arange(0, 105, 5), include_lowest=True)
    st.bar_chart(scored.groupby(score_bins, observed=False).size().rename(index=str))

    st.subheader("Risk tiers")
    tier_table = scored.groupby("risk_tier").agg(
        transactions=("isFraud", "size"),
        actual_fraud=("isFraud", "sum"),
        fraud_rate=("isFraud", "mean"),
    ).reindex(TIER_ORDER)
    tier_table["action"] = [RISK_ACTIONS[t] for t in TIER_ORDER]
    tier_table["score_from"] = [0, tiers["medium"] * 100, tiers["high"] * 100, tiers["critical"] * 100]
    st.dataframe(tier_table)

    st.subheader("What if we change the alert threshold?")
    threshold = st.slider("Alert when risk score is at least", 1, 99, int(round(tiers["high"] * 100)))
    review_cost = st.number_input("Review cost per alert (USD)", value=float(bundle["review_cost"]), step=1.0)
    result = cost_curve(scored["isFraud"].values, scored["risk_score"].values / 100,
                        scored["TransactionAmt"].values, review_cost, thresholds=[threshold / 100]).iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Alerts", f"{int(result['alerts']):,}")
    col2.metric("Recall", f"{result['recall']:.1%}")
    col3.metric("Precision", f"{result['precision']:.1%}")
    col4.metric("Total cost", f"${result['total_cost']:,.0f}")

    st.subheader("Alert queue")
    alerts = scored[scored["risk_score"] >= threshold].sort_values("risk_score", ascending=False)
    st.dataframe(alerts[["TransactionID", "TransactionAmt", "ProductCD", "email_group", "DeviceType",
                         "risk_score", "risk_tier", "recommended_action", "isFraud"]].head(200))

# ------------------------------------------------------------------ Transaction Scoring
else:
    st.subheader("Score a transaction")
    st.write(
        "Most features depend on the customer's history, so start from a real test-period transaction "
        "and change the details you want to test."
    )

    top_risk_ids = scored.nlargest(50, "risk_score")["TransactionID"]
    random_ids = scored.sample(150, random_state=1)["TransactionID"]
    choices = pd.concat([top_risk_ids, random_ids]).drop_duplicates().tolist()
    txn_id = st.selectbox("Transaction ID (first 50 are the highest-risk ones)", choices)

    row = features[features["TransactionID"] == txn_id].copy()
    original = row.iloc[0]

    col1, col2, col3 = st.columns(3)
    amount = col1.number_input("Amount (USD)", min_value=0.01, value=float(original["TransactionAmt"]))
    hour = col2.slider("Hour (relative)", 0, 23, int(original["hour"]))
    product_options = ["W", "C", "R", "H", "S"]
    product = col3.selectbox("Product", product_options, index=product_options.index(original["ProductCD"]))

    col1, col2, col3 = st.columns(3)
    device_options = ["missing", "desktop", "mobile"]
    device = col1.selectbox("Device type", device_options, index=device_options.index(original["DeviceType"]))
    email_options = ["gmail", "yahoo", "microsoft", "anonymous", "aol", "other", "missing"]
    email = col2.selectbox("Purchaser email provider", email_options, index=email_options.index(original["email_group"]))
    mismatch = col3.checkbox("Purchaser and recipient emails differ", value=bool(original["email_mismatch"]))

    # Recompute only the features that depend on what the user changed
    row["TransactionAmt"] = amount
    row["log_amt"] = np.log1p(amount)
    row["amt_to_uid_avg"] = amount / original["uid_avg_amt_prior"]
    row["high_value_flag"] = int(amount >= bundle["high_value_cutoff"])
    row["hour"] = hour
    row["quiet_hour_flag"] = int(hour in bundle["quiet_hours"])
    row["ProductCD"] = product
    row["DeviceType"] = device
    row["has_identity"] = int(device != "missing")
    row["email_group"] = email
    row["email_mismatch"] = int(mismatch)

    score = model.predict_proba(row[ALL_FEATURES])[0, 1]
    tier = assign_tier(score, tiers)

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk score", f"{score * 100:.1f} / 100")
    col2.metric("Risk tier", tier)
    col3.metric("Recommended action", RISK_ACTIONS[tier])
    st.caption("The score is a ranking score from a class-weighted model, not a calibrated probability.")

    st.write("**Customer history used by the model**")
    st.write(
        f"Earlier transactions: {int(original['uid_txn_count_prior'])} · "
        f"in last 24h: {int(original['uid_txn_count_24h'])} · "
        f"average earlier amount: ${original['uid_avg_amt_prior']:,.2f} · "
        f"this amount is {row['amt_to_uid_avg'].iloc[0]:.1f}x their average"
    )

    st.write("**Main risk factors** (how much the score falls if this factor looked like a typical legitimate transaction)")
    reasons = explain_transaction(model, row, bundle["typical_values"], top_n=5)
    if reasons.empty:
        st.write("No single factor stands out; the score is driven by the combination of features.")
    else:
        reasons["score_drop"] = (reasons["score_drop"] * 100).round(1)
        st.dataframe(reasons.rename(columns={"score_drop": "score points"}), hide_index=True)

    st.caption(f"Actual outcome in the data: {'FRAUD' if original['isFraud'] == 1 else 'legitimate'}")
