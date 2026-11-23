
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PRODUCT_FILE = Path("products_to_track.json")
HISTORY_FILE = Path("price_history.csv")

FIELDNAMES = [
    "date", "product", "sku", "retailer",
    "price", "currency", "vat", "url"
]


def get_distry_price(url):
    response = requests.get(
        url,
        headers={"User-Agent": "MoxaPriceTracker/0.1"},
        timeout=20
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    wrapper = soup.select_one(".mds_price_wrapper")

    if not wrapper:
        raise ValueError("Kunde inte hitta prisområdet.")

    element = wrapper.select_one(
        "#mds_price_value .woocommerce-Price-amount"
    )

    if not element:
        raise ValueError("Kunde inte hitta aktuellt pris.")

    price_text = element.get_text(strip=True)
    price_text = (
        price_text.replace("€", "")
        .replace("\u00a0", "")
        .replace("\u202f", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    return float(price_text)


def main():
    with PRODUCT_FILE.open(encoding="utf-8") as file:
        config = json.load(file)

    products = config["products"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    history = []

    if HISTORY_FILE.exists():
        with HISTORY_FILE.open(
            newline="", encoding="utf-8"
        ) as file:
            history = list(csv.DictReader(file))

    successful = 0
    failed = 0

    for product in products:
        for retailer, url in product.get("urls", {}).items():

            if retailer != "distry":
                print(
                    f"Hoppar över {retailer}: "
                    "prisavläsare saknas ännu."
                )
                continue

            try:
                price = get_distry_price(url)

                record = {
                    "date": today,
                    "product": product["name"],
                    "sku": product["sku"],
                    "retailer": "Moxa Distry Shop",
                    "price": price,
                    "currency": "EUR",
                    "vat": "excluded",
                    "url": url
                }

                history = [
                    row for row in history
                    if not (
                        row["date"] == record["date"]
                        and row["sku"] == record["sku"]
                        and row["retailer"] == record["retailer"]
                    )
                ]

                history.append(record)
                successful += 1

                print(
                    f"OK: {product['sku']} – "
                    f"{price:.2f} EUR – Moxa Distry Shop"
                )

            except (requests.RequestException, ValueError) as error:
                failed += 1
                print(
                    f"FEL: {product['sku']} – {error}"
                )

    if successful == 0:
        raise RuntimeError(
            "Inga priser kunde hämtas. "
            "Prishistoriken ändras inte."
        )

    history.sort(
        key=lambda row: (
            row["date"],
            row["sku"],
            row["retailer"]
        )
    )

    with HISTORY_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=FIELDNAMES
        )
        writer.writeheader()
        writer.writerows(history)

    print("-----------------------------")
    print("MOXA PRICE TRACKER")
    print("-----------------------------")
    print("Lyckade prisinsamlingar:", successful)
    print("Misslyckade prisinsamlingar:", failed)
    print("Totalt antal prisregistreringar:", len(history))
    print("-----------------------------")


if __name__ == "__main__":
    main()
