
import csv
from datetime import datetime, timezone
from pathlib import Path

import requests
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

# Hitta produktens aktuella pris
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

# Skapa dagens prisregistrering
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

file_path = Path("price_history.csv")
fieldnames = list(price_record.keys())

# Las in tidigare prishistorik
history = []

if file_path.exists():
    with file_path.open(
        "r", newline="", encoding="utf-8"
    ) as file:
        reader = csv.DictReader(file)
        history = list(reader)

# Ta bort eventuella tidigare registreringar
# for samma produkt, butik och datum
history = [
    row for row in history
    if not (
        row["date"] == price_record["date"]
        and row["sku"] == price_record["sku"]
        and row["retailer"] == price_record["retailer"]
    )
]

# Lagg till den senaste prisregistreringen
history.append(price_record)

# Sortera historiken efter datum
history.sort(
    key=lambda row: (
        row["date"],
        row["sku"],
        row["retailer"]
    )
)

# Spara hela historiken
with file_path.open(
    "w", newline="", encoding="utf-8"
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )
    writer.writeheader()
    writer.writerows(history)

print("-----------------------------")
print("MOXA PRICE TRACKER")
print("-----------------------------")
print("Produkt:", price_record["product"])
print("Butik:", price_record["retailer"])
print("Pris:", price_record["price"], "EUR")
print("Datum:", price_record["date"])
print("Sparat i:", file_path)
print("Antal prisregistreringar:", len(history))
print("-----------------------------")
