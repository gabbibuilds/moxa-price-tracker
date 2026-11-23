
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


def fetch_page(url, retailer):
    # Distry: samma User-Agent som fungerade tidigare.
    if retailer == "distry":
        headers = {
            "User-Agent": "MoxaPriceTracker/0.1"
        }
    else:
        headers = {
            "User-Agent": "MoxaPriceTracker/1.0",
            "Accept-Language": "sv-SE,sv;q=0.9"
        }

    response = requests.get(
        url,
        headers=headers,
        timeout=25
    )
    response.raise_for_status()

    return BeautifulSoup(
        response.text, "html.parser"
    )


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


def get_distry_price(soup):
    element = soup.select_one(
        ".mds_price_wrapper "
        "#mds_price_value .woocommerce-Price-amount"
    )

    if element is None:
        raise ValueError(
            "Distry-priset hittades inte."
        )

    return parse_price(
        element.get_text(" ", strip=True)
    ), "EUR"


def get_rs_price(soup, sku):
    # Verifiera att rätt artikel finns på sidan.
    page_text = re.sub(
        r"[^A-Z0-9]", "",
        soup.get_text(" ", strip=True).upper()
    )
    expected = re.sub(
        r"[^A-Z0-9]", "", sku.upper()
    )

    if expected not in page_text:
        raise ValueError(
            "Artikelnumret kunde inte verifieras."
        )

    # Läs strukturerad produktdata.
    for script in soup.select(
        'script[type="application/ld+json"]'
    ):
        try:
            data = json.loads(
                script.string or script.get_text()
            )
        except (ValueError, TypeError):
            continue

        objects = data if isinstance(data, list) else [data]
        queue = list(objects)

        while queue:
            obj = queue.pop(0)

            if not isinstance(obj, dict):
                continue

            graph = obj.get("@graph", [])
            if isinstance(graph, list):
                queue.extend(graph)

            offers = obj.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]

            if not isinstance(offers, list):
                continue

            for offer in offers:
                if not isinstance(offer, dict):
                    continue

                amount = offer.get("price")
                currency = offer.get("priceCurrency")
                vat_included = offer.get(
                    "valueAddedTaxIncluded"
                )

                if (
                    amount is not None
                    and currency == "SEK"
                    and vat_included is False
                ):
                    return parse_price(amount), "SEK"

    raise ValueError(
        "Inget verifierat RS-pris exkl. moms hittades."
    )


def collect_price(retailer, url, sku):
    if retailer not in RETAILERS:
        raise ValueError(
            f"Prisavläsare saknas för {retailer}."
        )

    soup = fetch_page(url, retailer)

    if retailer == "distry":
        return get_distry_price(soup)

    if retailer == "rs_distrelec":
        return get_rs_price(soup, sku)


def main():
    with PRODUCT_FILE.open(
        encoding="utf-8"
    ) as file:
        products = json.load(file)["products"]

    history = []

    if HISTORY_FILE.exists():
        with HISTORY_FILE.open(
            newline="", encoding="utf-8"
        ) as file:
            history = list(csv.DictReader(file))

    today = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    successful = 0
    failed = 0
    skipped = 0

    for product in products:
        for retailer, url in product.get(
            "urls", {}
        ).items():

            if retailer not in RETAILERS:
                print(
                    f"HOPPAS ÖVER: {product['sku']} | "
                    f"{retailer} | Prisavläsare saknas"
                )
                skipped += 1
                continue

            try:
                price, currency = collect_price(
                    retailer,
                    url,
                    product["sku"]
                )

                record = {
                    "date": today,
                    "product": product["name"],
                    "sku": product["sku"],
                    "retailer": RETAILERS[retailer],
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

            except requests.HTTPError as error:
                failed += 1
                status = error.response.status_code

                if status == 403:
                    reason = "403 - Webbplatsen nekar åtkomst"
                else:
                    reason = f"HTTP-fel {status}"

                print(
                    f"FEL: {product['sku']} | "
                    f"{retailer} | {reason}"
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

    if successful > 0:
        history.sort(
            key=lambda row: (
                row["date"],
                row["sku"],
                row["retailer"]
            )
        )

        with HISTORY_FILE.open(
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=FIELDS
            )
            writer.writeheader()
            writer.writerows(history)

    else:
        print(
            "VARNING: Inga nya priser hämtades. "
            "Befintlig prishistorik lämnas oförändrad."
        )

    print("-----------------------------")
    print("MOXA PRICE TRACKER")
    print("-----------------------------")
    print("Lyckade prisinsamlingar:", successful)
    print("Misslyckade prisinsamlingar:", failed)
    print("Överhoppade:", skipped)
    print("Totalt i prishistoriken:", len(history))
    print("-----------------------------")


if __name__ == "__main__":
    main()
