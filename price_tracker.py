
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PRODUCT_FILE = Path("products_to_track.json")
HISTORY_FILE = Path("price_history.csv")

FIELDS = [
    "date", "product", "sku", "retailer",
    "price", "currency", "vat", "url"
]

RETAILERS = {
    "distry": "Moxa Distry Shop",
    "rs_distrelec": "RS / Distrelec"
}


def fetch_page(url):
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8"
        },
        timeout=25
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_price(text):
    value = re.sub(r"[^\d,.]", "", str(text))

    if not value:
        raise ValueError("Priset saknar siffror.")

    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        value = value.replace(",", ".")

    price = float(value)

    if not 0 < price < 1000000:
        raise ValueError("Orimligt pris.")

    return price


def get_distry_price(soup, sku):
    element = soup.select_one(
        ".mds_price_wrapper "
        "#mds_price_value .woocommerce-Price-amount"
    )

    if not element:
        raise ValueError("Distry-priset hittades inte.")

    return parse_price(element.get_text(" ", strip=True)), "EUR"


def get_rs_price(soup, sku):
    # Kontrollera att rätt Moxa-artikel finns på sidan.
    page = re.sub(
        r"[^A-Z0-9]", "",
        soup.get_text(" ", strip=True).upper()
    )
    expected = re.sub(r"[^A-Z0-9]", "", sku.upper())

    if expected not in page:
        raise ValueError(
            "Artikelnumret kunde inte verifieras."
        )

    # Försök hitta produktens pris i JSON-LD.
    for script in soup.select(
        'script[type="application/ld+json"]'
    ):
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue

        objects = data if isinstance(data, list) else [data]

        for obj in objects:
            if not isinstance(obj, dict):
                continue

            if "@graph" in obj:
                objects.extend(obj["@graph"])

            offers = obj.get("offers")
            if not offers:
                continue

            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if not isinstance(offer, dict):
                    continue

                amount = offer.get("price")
                currency = offer.get("priceCurrency")

                if amount is None or currency != "SEK":
                    continue

                # JSON-LD anger inte alltid momsstatus.
                # Därför sparar vi inte priset utan
                # uttrycklig verifiering.
                vat = offer.get("valueAddedTaxIncluded")

                if vat is not False:
                    continue

                return parse_price(amount), "SEK"

    raise ValueError(
        "Inget verifierat RS-pris exkl. moms hittades."
    )


def collect(retailer, url, sku):
    soup = fetch_page(url)

    if retailer == "distry":
        return get_distry_price(soup, sku)

    if retailer == "rs_distrelec":
        return get_rs_price(soup, sku)

    raise ValueError(
        f"Prisavläsare saknas för {retailer}."
    )


def main():
    with PRODUCT_FILE.open(encoding="utf-8") as file:
        products = json.load(file)["products"]

    history = []

    if HISTORY_FILE.exists():
        with HISTORY_FILE.open(
            newline="", encoding="utf-8"
        ) as file:
            history = list(csv.DictReader(file))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    successful = 0
    failed = 0

    for product in products:
        for retailer, url in product.get("urls", {}).items():
            try:
                price, currency = collect(
                    retailer, url, product["sku"]
                )

                record = {
                    "date": today,
                    "product": product["name"],
                    "sku": product["sku"],
                    "retailer": RETAILERS.get(
                        retailer, retailer
                    ),
                    "price": price,
                    "currency": currency,
                    "vat": "excluded",
                    "url": url
                }

                history = [
                    row for row in history
                    if not (
                        row["date"] == today
                        and row["sku"] == record["sku"]
                        and row["retailer"] == record["retailer"]
                    )
                ]

                history.append(record)
                successful += 1

                print(
                    f"OK: {record['sku']} | "
                    f"{record['retailer']} | "
                    f"{price:.2f} {currency}"
                )

            except (
                requests.RequestException,
                ValueError,
                TypeError
            ) as error:
                failed += 1
                print(
                    f"FEL: {product['sku']} | "
                    f"{retailer} | {error}"
                )

    if successful == 0:
        raise RuntimeError(
            "Inga priser kunde hämtas."
        )

    history.sort(
        key=lambda row: (
            row["date"], row["sku"], row["retailer"]
        )
    )

    with HISTORY_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=FIELDS
        )
        writer.writeheader()
        writer.writerows(history)

    print("-----------------------------")
    print("MOXA PRICE TRACKER")
    print("-----------------------------")
    print("Lyckade prisinsamlingar:", successful)
    print("Misslyckade prisinsamlingar:", failed)
    print("Totalt i prishistoriken:", len(history))
    print("-----------------------------")


if __name__ == "__main__":
    main()
