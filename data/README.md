# Data

Raw data is not committed because of its size.

**Source:** [IEEE-CIS Fraud Detection](https://www.kaggle.com/competitions/ieee-fraud-detection/data) (Kaggle competition, data provided by Vesta Corporation).
These are real card-not-present e-commerce transactions. You need a Kaggle account and must accept the competition rules before downloading.

Download these two files into this folder:

```
data/
├── train_transaction.csv   (~590k rows, 394 columns, includes the isFraud label)
└── train_identity.csv      (~144k rows, device and identity details, joined on TransactionID)
```

`test_transaction.csv` and `test_identity.csv` are not used: they have no fraud labels.

Only 20 columns are loaded (see `src/data_preparation.py`). The masked V1–V339, id_01–id_38 and most C/D/M columns are deliberately left out so every model input can be explained.
