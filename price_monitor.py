from app import scrape_amazon_price, append_row, PRODUCT_URL

if __name__ == "__main__":
    row = scrape_amazon_price(PRODUCT_URL)
    append_row(row)
    print(row)
