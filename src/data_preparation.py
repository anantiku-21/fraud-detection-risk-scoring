import pandas as pd

# The raw file has 394 columns, most of them masked (V1-V339). I only load the
# columns I can explain, which also keeps memory usage manageable on a laptop.
TRANSACTION_COLUMNS = [
    "TransactionID", "isFraud", "TransactionDT", "TransactionAmt", "ProductCD",
    "card1", "card4", "card6", "addr1", "dist1",
    "P_emaildomain", "R_emaildomain",
    "C1", "C13", "C14", "D1",
]

IDENTITY_COLUMNS = ["TransactionID", "DeviceType", "DeviceInfo"]


def load_transactions(data_dir="../data"):
    transactions = pd.read_csv(f"{data_dir}/train_transaction.csv", usecols=TRANSACTION_COLUMNS)
    identity = pd.read_csv(f"{data_dir}/train_identity.csv", usecols=IDENTITY_COLUMNS)

    # Only ~24% of transactions have an identity record, so this has to be a left join
    df = transactions.merge(identity, on="TransactionID", how="left")
    df["has_identity"] = df["DeviceType"].notna().astype(int)

    df = df.sort_values("TransactionDT").reset_index(drop=True)
    return df


def clean_transactions(df):
    df = df.copy()

    # TransactionDT is seconds from an undisclosed reference date, so I work with
    # relative day / hour rather than pretending to know real calendar dates.
    df["day"] = df["TransactionDT"] // 86400
    df["hour"] = (df["TransactionDT"] // 3600) % 24

    # Missing categories are kept as their own value because "no email / no device
    # info provided" can itself be informative for fraud.
    for col in ["ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain", "DeviceType"]:
        df[col] = df[col].fillna("missing")

    return df
