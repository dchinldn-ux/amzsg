import os
import re
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

PRODUCT_URL = "https://www.amazon.sg/Clorox-ToiletWand-Disinfecting-Refills-Disposable/dp/B010SJR5SM"
ASIN = "B010SJR5SM"
CSV_PATH = Path("amazon_sg_price_history.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-SG,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def clean_price(text: str):
    """Convert strings like 'S$16.32' or '$16.32' to float."""
    if not text:
        return None
    text = text.replace(",", "").strip()
    m = re.search(r"(?:S\$|\$)?\s*(\d+(?:\.\d{1,2})?)", text)
    return float(m.group(1)) if m else None


def scrape_amazon_price(url: str = PRODUCT_URL) -> dict:
    """
    Scrapes the public Amazon.sg product page.
    Note: Amazon may hide prices, require cart/login, or block bots.
    This function records 'None' when price is not visible.
    """
    resp = requests.get(url, headers=HEADERS, timeout=20)
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.select_one("#productTitle")
    title = title_tag.get_text(" ", strip=True) if title_tag else ""

    page_text = soup.get_text(" ", strip=True).lower()
    blocked = any(x in page_text for x in ["captcha", "robot check", "enter the characters you see below"])

    availability_tag = soup.select_one("#availability")
    availability = availability_tag.get_text(" ", strip=True) if availability_tag else ""

    price_candidates = []

    # Common Amazon price selectors
    selectors = [
        "#corePrice_feature_div .a-offscreen",
        "#apex_desktop .a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "#price_inside_buybox",
        "#tp_price_block_total_price_ww .a-offscreen",
        ".a-price .a-offscreen",
    ]

    for selector in selectors:
        for tag in soup.select(selector):
            txt = tag.get_text(" ", strip=True)
            if "S$" in txt or "$" in txt:
                price_candidates.append(txt)

    # Remove obvious non-price candidates
    parsed = []
    for item in price_candidates:
        price = clean_price(item)
        if price is not None and 0 < price < 1000:
            parsed.append(price)

    price = parsed[0] if parsed else None

    notes = []
    if blocked:
        notes.append("Amazon bot/captcha page detected")
    if "to see product details, add this item to your cart" in page_text:
        notes.append("Amazon hides price/details until cart")
    if "no featured offers available" in page_text:
        notes.append("No featured offers available")
    if price is None:
        notes.append("Price not publicly visible on fetched page")

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "asin": ASIN,
        "title": title,
        "price_sgd": price,
        "availability": availability,
        "url": url,
        "notes": "; ".join(notes),
    }


def append_row(row: dict, csv_path: Path = CSV_PATH):
    is_new = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def load_history(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=["timestamp_utc", "asin", "title", "price_sgd", "availability", "url", "notes"])
    df = pd.read_csv(csv_path)
    if "timestamp_utc" in df.columns:
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], errors="coerce")
    if "price_sgd" in df.columns:
        df["price_sgd"] = pd.to_numeric(df["price_sgd"], errors="coerce")
    return df


st.set_page_config(page_title="Amazon.sg Price Monitor", layout="wide")

st.title("Amazon.sg Price Monitor")
st.caption("Product: Clorox ToiletWand Disinfecting Refills, Rainforest Rush, 10 Count")

st.write(f"ASIN: `{ASIN}`")
st.write(f"URL: {PRODUCT_URL}")

col1, col2, col3 = st.columns(3)

if col1.button("Check price now"):
    with st.spinner("Checking Amazon.sg public page..."):
        row = scrape_amazon_price(PRODUCT_URL)
        append_row(row)
    st.success("Price check recorded.")
    st.json(row)

df = load_history()

latest_price = None
if not df.empty and "price_sgd" in df.columns:
    valid_prices = df.dropna(subset=["price_sgd"])
    if not valid_prices.empty:
        latest_price = valid_prices.sort_values("timestamp_utc").iloc[-1]["price_sgd"]

col2.metric("Latest visible price", "N/A" if latest_price is None else f"S${latest_price:.2f}")

if not df.empty:
    last_check = df["timestamp_utc"].max()
    col3.metric("Last check", str(last_check)[:19])
else:
    col3.metric("Last check", "No data yet")

st.subheader("Price History")

if df.empty:
    st.info("No history yet. Press 'Check price now' or run the GitHub Action daily.")
else:
    chart_df = df.dropna(subset=["price_sgd"]).copy()
    if chart_df.empty:
        st.warning("Checks exist, but Amazon did not expose a visible price in the fetched pages.")
    else:
        chart_df = chart_df.sort_values("timestamp_utc")
        st.line_chart(chart_df, x="timestamp_utc", y="price_sgd")

    st.dataframe(df.sort_values("timestamp_utc", ascending=False), use_container_width=True)
