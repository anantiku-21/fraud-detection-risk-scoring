# Fraud Detection & Transaction Risk Scoring

An end-to-end fraud detection and transaction risk scoring project built on the **IEEE-CIS Fraud Detection** dataset.

The project focuses on an operational risk workflow rather than only binary fraud classification:

**Transaction Data → Feature Engineering → Model Comparison → Fraud Probability/Score → Risk Tiers → Cost Analysis → Dashboard**

---

## 1. Project Overview

Financial institutions process large numbers of transactions where only a small fraction may be fraudulent. A useful fraud-risk system therefore needs to:

- identify suspicious transactions despite severe class imbalance,
- prioritize transactions for investigation,
- compare multiple classification models,
- convert model scores into operational risk tiers,
- evaluate the financial impact of fraud detection,
- provide an analyst-friendly dashboard.

This project implements that workflow using Python, SQL and Streamlit.

---

## 2. Dataset

The project uses the **IEEE-CIS Fraud Detection** dataset.

### Dataset Summary

| Metric | Value |
|---|---:|
| Total transactions | 590,540 |
| Fraud rate | 3.50% |
| Customer proxy | 217,779 |
| Features used | 23 |
| Training transactions | 413,378 |
| Validation transactions | 88,581 |
| Test transactions | 88,581 |

The dataset contains transaction-level and identity-related information. The modelling pipeline uses a selected subset of engineered features rather than all available raw columns.

---

## 3. Objectives

1. Build a fraud classification model under severe class imbalance.
2. Compare multiple machine-learning approaches.
3. Use **PR-AUC** as an important model-selection metric because fraud is the minority class.
4. Evaluate performance on an untouched test set.
5. Convert model outputs into operational risk tiers.
6. Identify high-priority transactions for investigation.
7. Estimate the financial impact of applying the risk model.
8. Provide an interactive Streamlit dashboard for analysts.

---

## 4. Key Features

The modelling pipeline uses transaction-level and engineered behavioural features, including:

- Transaction amount
- Time-related transaction features
- Product/card-related attributes
- Email/domain information
- Device/browser information
- Identity-related variables
- Historical/rolling behavioural features where available
- Missing-value indicators
- Encoded categorical information

The final modelling dataset contains **23 selected features**.

---

## 5. Exploratory & Statistical Analysis

The project examines:

- overall fraud prevalence,
- transaction amount distributions,
- fraud behaviour across categorical variables,
- missing-value patterns,
- temporal transaction behaviour,
- relationships between transaction characteristics and fraud,
- model feature importance.

Because fraudulent transactions represent only a small fraction of all observations, accuracy alone is not treated as a sufficient evaluation metric.

---

## 6. Machine Learning Models

Five models were evaluated:

1. Logistic Regression
2. Logistic Regression with class balancing
3. Decision Tree with class balancing
4. Random Forest with class balancing
5. Gradient Boosting with class balancing

The models were evaluated using metrics such as:

- PR-AUC
- ROC-AUC
- Precision
- Recall
- F1-score

**PR-AUC was emphasized during model selection because the fraud class is highly imbalanced.**

---

## 7. Model Comparison

The validation comparison used the project's model evaluation outputs.

| Model | Validation PR-AUC | ROC-AUC | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.2646 | 0.7956 | 89.52% | 7.30% | 0.1350 |
| Logistic Regression (Balanced) | 0.1836 | 0.8012 | 10.09% | 67.85% | 0.1757 |
| Decision Tree (Balanced) | 0.3512 | 0.8125 | 15.30% | 55.16% | 0.2395 |
| Random Forest (Balanced) | 0.3886 | 0.8629 | 17.50% | 65.35% | 0.2761 |
| Gradient Boosting (Balanced) | **0.4266** | 0.8747 | 17.34% | 68.15% | 0.2764 |

The selected model was **Gradient Boosting (balanced)** based on the validation evaluation used in this project. Its validation PR-AUC was **0.4266**. fileciteturn1file0

---

## 8. Final Test Performance

The selected model was evaluated on **88,581 test transactions**.

| Metric | Test Result |
|---|---:|
| PR-AUC | **0.4451** |
| ROC-AUC | **0.8645** |
| Precision | **15.68%** |
| Recall | **69.51%** |
| F1-score | **0.2559** |
| Test fraud rate | **3.48%** |
| Decision threshold | **0.50** |

These results come from the project's final `key_results.json` output. fileciteturn1file0

### Why PR-AUC Matters

With a fraud rate of approximately 3.5%, a model can achieve high accuracy while still missing many fraudulent transactions.

PR-AUC focuses on the precision-recall trade-off for the positive class and is therefore particularly useful for evaluating this fraud-detection problem.

---

## 9. Risk Scoring Framework

The model output is converted into a **0–100 risk score** and divided into four operational tiers.

| Risk Tier | Score Range |
|---|---:|
| Low | < 35.09 |
| Medium | 35.09 – 49.99 |
| High | 50.00 – 94.20 |
| Critical | ≥ 94.21 |

The thresholds are based on the project's generated risk-tier configuration. fileciteturn1file0

### Operational Interpretation

| Tier | Example Action |
|---|---|
| Low | Normal transaction processing |
| Medium | Additional monitoring |
| High | Priority review / additional verification |
| Critical | Immediate investigation or stronger controls |

The risk score is intended primarily for **transaction prioritization**, not as a claim that the score represents a perfectly calibrated probability of fraud.

---

## 10. Fraud Prioritization Results

On the held-out test set:

- **15.42%** of transactions were classified as High or Critical.
- These transactions contained **69.51%** of the observed fraud cases.
- Approximately **64.49% of fraudulent transaction value** was captured within the evaluated prioritization framework.

This illustrates the operational idea behind risk scoring: concentrate limited investigation capacity on a smaller subset of transactions containing a large share of observed fraud. fileciteturn1file0

---

## 11. Cost-Sensitive Evaluation

The project also estimates the financial impact of using the fraud-risk model.

| Scenario | Estimated Cost |
|---|---:|
| No model | 469,608.52 |
| With model | 303,395.67 |

Under the project's stated cost assumptions, the model scenario represents an estimated **35.4% reduction in the evaluated cost**.

These figures are project-level estimates based on the defined cost assumptions; they should not be interpreted as real-world financial savings or production results. fileciteturn1file0

---

## 12. SQL Analytics

SQL analysis is included to demonstrate analyst-oriented transaction investigation.

Example analyses include:

- fraud rate by transaction category,
- transaction-volume analysis,
- customer/transaction aggregation,
- high-risk transaction counts,
- fraud concentration,
- transaction amount analysis,
- risk-tier summaries.

SQL is used as a complementary analytics layer alongside the machine-learning pipeline.

---

## 13. Streamlit Dashboard

The project includes an interactive Streamlit dashboard for risk analysis.

### Dashboard Sections

### Overview
Provides high-level portfolio metrics such as:

- total transactions,
- fraud rate,
- model performance,
- transaction risk distribution.

### Fraud Analysis
Provides analysis of:

- fraud patterns,
- transaction behaviour,
- fraud concentration,
- model performance.

### Risk Monitoring
Focuses on:

- risk-tier distribution,
- High/Critical transaction concentration,
- fraud capture,
- operational prioritization.

### Transaction Scoring
Allows analysts to enter transaction information and obtain a model-based risk score and risk tier.

---

## 14. Project Structure

```text
fraud-detection-risk-scoring/
│
├── data/
│   └── README.md
│
├── notebooks/
│   └── fraud_detection.ipynb
│
├── sql/
│   └── fraud_analysis.sql
│
├── dashboard/
│   └── app.py
│
├── outputs/
│   └── model_results/
│       ├── key_results.json
│       ├── model_comparison.csv
│       ├── cost_sensitivity.csv
│       ├── permutation_importance.csv
│       ├── tier_summary_test.csv
│       └── .gitkeep
│
├── requirements.txt
├── README.md
└── .gitignore
```

Large raw datasets and local virtual-environment files are intentionally excluded from version control.

---

## 15. Installation

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 16. Running the Project

### Run the notebook

```bash
jupyter notebook
```

Open:

```text
notebooks/fraud_detection.ipynb
```

Run the notebook to reproduce the modelling workflow and generated outputs.

### Run the dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard will open in the browser.

---

## 17. Generated Outputs

The modelling pipeline produces:

| File | Purpose |
|---|---|
| `key_results.json` | Main project metrics and selected-model results |
| `model_comparison.csv` | Model comparison results |
| `cost_sensitivity.csv` | Cost-based evaluation |
| `permutation_importance.csv` | Feature importance analysis |
| `tier_summary_test.csv` | Risk-tier distribution and fraud capture |
| `scored_test_transactions.csv` | Test transactions with model scores |
| `test_features.csv` | Test feature data |
| `model_bundle.joblib` | Saved model pipeline |

Large generated files may be excluded from GitHub to keep the repository lightweight.

---

## 18. Business / Risk Interpretation

From a risk-analyst perspective, the project demonstrates how a fraud model can support:

- transaction screening,
- investigation prioritization,
- risk-tier monitoring,
- fraud-loss reduction analysis,
- resource allocation,
- threshold analysis,
- operational decision support.

The important business question is not only:

> "Can the model predict fraud?"

but also:

> "Can the model help prioritize a manageable set of transactions for investigation?"

---

## 19. Limitations

This is a portfolio project and should not be treated as a production fraud system.

Important limitations include:

- IEEE-CIS is a competition dataset rather than live institutional transaction data.
- Model performance can change under distribution shift.
- Fraud patterns evolve over time.
- Cost assumptions are project-defined estimates.
- The risk score is used for prioritization and has not been presented as a fully calibrated production probability.
- Production deployment would require monitoring, model governance, threshold review and retraining procedures.
- Additional fairness, explainability, privacy and regulatory checks would be required before real-world deployment.

---

## 20. Future Improvements

Possible extensions include:

- probability calibration,
- advanced time-based validation,
- hyperparameter optimization,
- LightGBM/XGBoost comparison,
- SHAP-based explanations,
- automated threshold optimization,
- drift monitoring,
- real-time scoring API,
- model monitoring,
- alert management,
- investigator feedback loops,
- production database integration.

---

## 21. Interview Focus

This project can be discussed through four major areas:

### Machine Learning
- Why PR-AUC instead of accuracy?
- Why class balancing?
- Why compare multiple models?
- How was the final model selected?

### Risk Analytics
- How are transactions prioritized?
- Why use risk tiers?
- How does threshold selection affect recall and precision?
- How can limited investigation capacity be allocated?

### Business Analytics
- How was cost impact estimated?
- What does fraud value captured mean?
- How can the model reduce investigation workload?

### Technical Implementation
- Python
- Pandas
- NumPy
- Scikit-learn
- SQL
- Streamlit
- Jupyter
- Git/GitHub

---

## 22. Key Takeaway

This project combines **machine learning, transaction analytics, risk scoring and business-oriented cost analysis** into an end-to-end fraud-risk workflow.

The final evaluation covers **590,540 transactions**, with a selected Gradient Boosting model achieving **0.4451 PR-AUC, 0.8645 ROC-AUC and 69.51% recall on the held-out test set**. The risk-tier framework concentrated **69.51% of observed fraud in 15.42% of test transactions**, while the project's cost assumptions produced an estimated reduction from **469,608.52 to 303,395.67**. fileciteturn1file0

---

## Disclaimer

This repository is an educational/portfolio project. Results are specific to the dataset, feature engineering, validation strategy and cost assumptions used in this implementation and should not be interpreted as production performance or guaranteed financial savings.
