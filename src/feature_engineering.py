import numpy as np
import pandas as pd

NUMERIC_FEATURES = [
    "log_amt", "hour", "quiet_hour_flag", "card_age_days", "dist1", "addr_missing",
    "C1", "C13", "C14", "has_identity", "email_mismatch",
    "uid_txn_count_prior", "uid_txn_count_24h", "log_secs_since_last_txn",
    "amt_to_uid_avg", "is_new_uid", "high_value_flag", "rapid_txn_flag",
]

CATEGORICAL_FEATURES = ["ProductCD", "card4", "card6", "DeviceType", "email_group"]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Used when a customer has no earlier transaction: "last transaction was ~6 months ago",
# roughly the full span of the dataset.
NO_PREVIOUS_TXN_SECONDS = 183 * 86400


def group_email(domain):
    if domain == "missing":
        return "missing"
    if domain.startswith("gmail"):
        return "gmail"
    if domain.startswith("yahoo") or domain.startswith("ymail"):
        return "yahoo"
    if domain.startswith(("hotmail", "outlook", "live", "msn")):
        return "microsoft"
    if domain == "anonymous.com":
        return "anonymous"
    if domain.startswith("aol"):
        return "aol"
    return "other"


def add_customer_id(df):
    # The dataset has no customer ID. D1 is "days since the card was first used", so
    # (day - D1) is the card's start day. card1 + billing address + start day is a
    # widely used proxy for "same customer" in this dataset.
    # Missing parts are filled with -1 so they still form a valid key.
    df["card_start_day"] = df["day"] - df["D1"]
    df["uid"] = (
        df["card1"].astype(str) + "_"
        + df["addr1"].fillna(-1).astype(int).astype(str) + "_"
        + df["card_start_day"].fillna(-1).astype(int).astype(str)
    )
    return df


def count_previous_24h(times):
    # For each transaction, count the same customer's transactions in the 24 hours
    # BEFORE it. searchsorted finds where "24 hours ago" sits in the sorted times.
    times = times.values
    window_start = np.searchsorted(times, times - 86400, side="left")
    return pd.Series(np.arange(len(times)) - window_start)


def add_history_features(df):
    # Every feature here only looks at the customer's EARLIER transactions.
    # The data must be sorted by time for cumcount / diff / cumsum to mean "before".
    df = df.sort_values("TransactionDT").reset_index(drop=True)
    by_customer = df.groupby("uid")

    df["uid_txn_count_prior"] = by_customer.cumcount()
    df["is_new_uid"] = (df["uid_txn_count_prior"] == 0).astype(int)

    secs_since_last = by_customer["TransactionDT"].diff().fillna(NO_PREVIOUS_TXN_SECONDS)
    df["secs_since_last_txn"] = secs_since_last
    df["log_secs_since_last_txn"] = np.log1p(secs_since_last)

    counts_24h = by_customer["TransactionDT"].transform(lambda t: count_previous_24h(t).values)
    df["uid_txn_count_24h"] = counts_24h

    # Subtract the current amount so the average only uses past transactions
    prior_total = by_customer["TransactionAmt"].cumsum() - df["TransactionAmt"]
    df["uid_avg_amt_prior"] = prior_total / df["uid_txn_count_prior"]
    # No history -> treat the amount as "normal for this customer" (ratio 1).
    # is_new_uid already tells the model there is no history.
    df["uid_avg_amt_prior"] = df["uid_avg_amt_prior"].fillna(df["TransactionAmt"])
    df["amt_to_uid_avg"] = df["TransactionAmt"] / df["uid_avg_amt_prior"]

    return df


def add_transaction_features(df, quiet_hours, high_value_cutoff, rapid_seconds=300):
    df["log_amt"] = np.log1p(df["TransactionAmt"])
    df["quiet_hour_flag"] = df["hour"].isin(quiet_hours).astype(int)
    df["card_age_days"] = df["D1"]
    df["addr_missing"] = df["addr1"].isna().astype(int)

    df["email_group"] = df["P_emaildomain"].apply(group_email)
    both_present = (df["P_emaildomain"] != "missing") & (df["R_emaildomain"] != "missing")
    df["email_mismatch"] = (both_present & (df["P_emaildomain"] != df["R_emaildomain"])).astype(int)

    df["high_value_flag"] = (df["TransactionAmt"] >= high_value_cutoff).astype(int)
    df["rapid_txn_flag"] = (df["secs_since_last_txn"] < rapid_seconds).astype(int)
    return df


def build_features(df, quiet_hours, high_value_cutoff):
    df = add_customer_id(df.copy())
    df = add_history_features(df)
    df = add_transaction_features(df, quiet_hours, high_value_cutoff)
    return df
