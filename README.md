# Olist E-Commerce Analytics

This project analyses the Brazilian e-commerce dataset from Olist. It uses Python, SQLite, SQL, and Power BI to explore sales, products, customers, payments, delivery performance, and reviews.

## Dataset

The project uses the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Download the nine CSV files and place them in `data/raw/`.

## Tech stack

- Python (Pandas and NumPy)
- SQLite and SQL
- Power BI
- Jupyter Notebook
- unittest

## Project structure

- `data/` - raw and processed data files
- `preprocessing/` - data ingestion, cleaning, and validation scripts
- `database/` - database setup, loading scripts, views, and analysis queries
- `notebooks/` - exploratory analysis
- `powerbi/` - Power BI report
- `docs/` - supporting project documentation
- `tests/` - automated tests

## Main analyses

- Monthly sales trends
- Product category performance and Pareto analysis
- Customer repeat purchases and RFM segments
- Regional sales and freight costs
- Payment methods and instalments
- Delivery times and review scores

## Power BI dashboard

The report has five pages:

1. Executive Overview
2. Product Performance
3. Customer Analytics & RFM
4. Regional Geography & Logistics
5. Delivery Performance & Satisfaction

Open `powerbi/Olist_Ecommerce_Analytics.pbix` with Power BI Desktop to view it.

## How to run

1. Clone the repository and open the project folder.

2. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Download the Olist CSV files and place them in `data/raw/`.

4. Run the preprocessing scripts:

   ```bash
   python preprocessing/ingest_data.py
   python preprocessing/clean_data.py
   python preprocessing/validate_data.py
   ```

5. Create and load the database, then run the SQL analysis:

   ```bash
   python database/create_database.py
   python database/load_data.py
   python database/run_queries.py
   python database/export_powerbi_data.py
   ```

6. Run the tests if needed:

   ```bash
   python -m unittest discover tests -v
   ```

## Limitations

The dataset does not include cost of goods sold, marketing costs, or operating expenses, so the project reports sales and freight values rather than profit. Delivery delays are associated with lower review scores, but the dataset does not prove that delays are the only cause of negative reviews.

## Attribution

Dataset: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). The dataset is published under the [CC BY-NC-SA 4.0 license](https://creativecommons.org/licenses/by-nc-sa/4.0/).
