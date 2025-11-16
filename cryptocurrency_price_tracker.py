from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from datetime import datetime

# -------------------- SETTINGS --------------------
HEADLESS = True                   # Run Chrome in background (False = visible)
TOP_COINS = 10                     # Number of coins to scrape
CSV_FILE = "crypto_prices.csv"     # CSV output file
PRICE_CHANGE_THRESHOLD = 5         # Show coins with >5% 24h change
PORTFOLIO = ["Bitcoin", "Ethereum", "Cardano"]  # Coins to track
# --------------------------------------------------

def setup_driver(headless=True):
    """Initialize Chrome WebDriver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver


def scrape_top_coins(driver, top_n=10):
    """Scrape top N cryptocurrencies from CoinMarketCap"""
    url = "https://coinmarketcap.com/"
    driver.get(url)
    time.sleep(5)  # wait for page to load

    coins = []
    rows = driver.find_elements(By.XPATH, '//table[contains(@class, "cmc-table")]/tbody//tr')[:top_n]

    for row in rows:
        try:
            # Using <td> instead of class names
            rank = row.find_element(By.XPATH, './td[2]').text
            name = row.find_element(By.XPATH, './td[3]//p').text
            price = row.find_element(By.XPATH, './td[4]').text
            change_24h = row.find_element(By.XPATH, './td[6]').text
            market_cap = row.find_element(By.XPATH, './td[8]').text

            coins.append({
                "Rank": rank,
                "Name": f"{name}",
                "Price": price,
                "24h Change": change_24h,
                "Market Cap": market_cap
            })
        except Exception as e:
            print("Error parsing row:", e)

    return coins


def save_to_csv(data, filename):
    """Save scraped data to CSV with timestamp"""
    df = pd.DataFrame(data)
    df["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        old_df = pd.read_csv(filename)
        new_df = pd.concat([old_df, df], ignore_index=True)
    except FileNotFoundError:
        new_df = df

    new_df.to_csv(filename, index=False)
    print(f" Data saved to {filename}")


def filter_by_change(data, threshold=5):
    """Filter coins with 24h change greater than the given threshold"""
    filtered = []
    for coin in data:
        try:
            change_str = coin["24h Change"].replace('%', '').replace('+', '').replace('−', '-')
            change = float(change_str)
            if abs(change) > threshold:
                filtered.append(coin)
        except ValueError:
            continue
    return filtered


def portfolio_tracking(data, portfolio_list):
    """Track specific coins from the user-defined portfolio"""
    results = []
    for coin in portfolio_list:
        for data_coin in data:
            if coin.lower() in data_coin["Name"].lower():
                results.append(data_coin)
    return results


# -------------------- MAIN SCRIPT --------------------
if __name__ == "__main__":
    print(" Starting Cryptocurrency Price Tracker...\n")
    driver = setup_driver(HEADLESS)

    crypto_data = scrape_top_coins(driver, TOP_COINS)
    driver.quit()

    if crypto_data:
        save_to_csv(crypto_data, CSV_FILE)

        print(f"\n Coins with 24h Change > {PRICE_CHANGE_THRESHOLD}%:")
        filtered = filter_by_change(crypto_data, PRICE_CHANGE_THRESHOLD)
        if filtered:
            for coin in filtered:
                print(f"{coin['Name']}: {coin['24h Change']} | {coin['Price']}")
        else:
            print("No coins exceeded the change threshold today.")

        print("\n Portfolio Tracking:")
        portfolio_data = portfolio_tracking(crypto_data, PORTFOLIO)
        if portfolio_data:
            for coin in portfolio_data:
                print(f"{coin['Name']}: {coin['Price']} | 24h Change: {coin['24h Change']}")
        else:
            print("No portfolio coins found in the top list today.")

        print("\n Scraping and analysis completed successfully.")
    else:
        print("\n No data scraped. Please check the site or XPaths.")