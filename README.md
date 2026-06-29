# Amazon.sg Price Monitor

Tracks the public price visible for:

**Clorox ToiletWand Disinfecting Refills, Disposable Wand Heads - Rainforest Rush - 10 Count**  
ASIN: `B010SJR5SM`  
URL: `https://www.amazon.sg/Clorox-ToiletWand-Disinfecting-Refills-Disposable/dp/B010SJR5SM`

## Important limitation

Amazon.sg may hide the price, show "add to cart to see product details", or block automated requests.  
This free script records `None` when the price is not publicly visible.

For stable current-price access, use Amazon's official affiliate/Creators API if you qualify.  
For 3-month historical prices, you need a historical price provider or your own CSV built over time.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run once from terminal

```bash
python price_monitor.py
```

## GitHub Actions daily monitor

Upload these files to a GitHub repository.  
The workflow in `.github/workflows/price_monitor.yml` runs daily at 9am Singapore time and commits the updated CSV.
