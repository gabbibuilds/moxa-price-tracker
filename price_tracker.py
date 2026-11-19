
import requests
from bs4 import BeautifulSoup

url = "https://moxa.distry.shop/dispositivi-server-e-seriali/nport-5110-moxa/"

response = requests.get(
    url,
    headers={"User-Agent": "MoxaPriceTracker/0.1"},
    timeout=20
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Hitta prisområdet
price_wrapper = soup.select_one(".mds_price_wrapper")

if price_wrapper:
    print("Prisområdets HTML:", str(price_wrapper)[:1500])

    # Hitta aktuellt pris
    price_element = price_wrapper.select_one(
        ".mds_price_value .woocommerce-Price-amount, .mds_price_value .amount"
    )

    if price_element:
        price = price_element.get_text(strip=True)
        print("Produkt: Moxa NPort 5110")
        print("Butik: Moxa Distry Shop")
        print("Pris:", price)
    else:
        print("Kunde inte hitta aktuellt pris.")
else:
    print("Kunde inte hitta prisområdet.")
