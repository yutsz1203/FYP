# Robo-advisor and Portfolio Tracking System
The Robo-Advisor and Portfolio Tracking System project aims to develop an automated investment advice platform that utilizes data science techniques to provide personalized investment recommendations to users. The system considers factors such as users' risk preferences, cash flows, financial goals, and market conditions to create recommendation on an investment portfolio. By implementing portfolio allocation and leveraging historical market data, the robo-advisor system aims to assist users in making informed investment decisions. The project consists of two main components.

## Getting Started
`$ pip install -r requirements.txt`

## Usage
Before starting anything, get the latest prices, rates, and corporate actions by running `$ python update_db`

1. Latest price: `Updater()`
2. Latest rates: `update_rates()`

Then, start the app with this command:
`$ streamlit run app.py`


## Repo Structure
```
├── README.md
├── app.py
├── const.py
├── data
│   └── F-F_Research_Data_5_Factors_2x3.csv
├── helpers.py
├── pages
│   ├── home_page.py
│   ├── portfolio_overview.py
│   ├── portfolio_returns.py
│   ├── risk_analysis.py
│   ├── robo_advisor.py
│   └── transactions.py
├── report.html
├── requirements.txt
├── scripts.py
├── src
│   ├── db.py
│   ├── fx.py
│   ├── holding.py
│   ├── mpt.py
│   ├── risk_analysis_src.py
│   └── transaction_src.py
└── update_db.py
```

