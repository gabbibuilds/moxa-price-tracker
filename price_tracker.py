
import requests
import csv
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup

# Produkten vi bevakar
url = "https://moxa.distry.shop/dispositivi-server-e-seriali/nport-5110-moxa/"

response = requests.get(
    url,
    headers={"User-Agent": "MoxaPriceTracker/0.1"},
    timeout=20
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Hitta aktuellt produktpris
price_wrapper = soup.select_one(".mds_price_wrapper")

if not price_wrapper:
    raise ValueError("Kunde inte hitta prisomradet.")

price_element = price_wrapper.select_one(
    "#mds_price_value .woocommerce-Price-amount"
)

if not price_element:
    raise ValueError("Kunde inte hitta aktuellt pris.")

# Omvandla priset till ett tal
price_text = price_element.get_text(strip=True)
price_text = price_text.replace("€", "").replace(",", ".").strip()
price = float(price_text)

# Skapa en prispost med dagens datum
date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

price_record = {
    "date": date,
    "product": "Moxa NPort 5110",
    "sku": "NPORT-5110",
    "retailer": "Moxa Distry Shop",
    "price": price,
    "currency": "EUR",
    "vat": "excluded",
    "url": url
}

# Spara prisposten i en CSV-fil
file_path = Path("price_history.csv")
file_exists = file_path.exists()

with file_path.open("a", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=price_record.keys()
    )

    if not file_exists:
        writer.writeheader()

    writer.writerow(price_record)

print("-----------------------------")
print("MOXA PRICE TRACKER")
print("-----------------------------")
print("Produkt:", price_record["product"])
print("Butik:", price_record["retailer"])
print("Pris:", price_record["price"], "EUR")
print("Datum:", price_record["date"])
print("Sparat i:", file_path)
print("-----------------------------")
