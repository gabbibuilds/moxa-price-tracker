
import requests
from bs4 import BeautifulSoup

# Produkten vi vill bevaka
url = "https://moxa.distry.shop/dispositivi-server-e-seriali/nport-5110-moxa/"

# Hamta produktsidan
response = requests.get(
    url,
    headers={"User-Agent": "MoxaPriceTracker/0.1"},
    timeout=20
)

response.raise_for_status()

# Las sidans HTML
soup = BeautifulSoup(response.text, "html.parser")

# Hitta produktens prisomrade
price_wrapper = soup.select_one(".mds_price_wrapper")

if price_wrapper:

    # Hitta det aktuella priset
    price_element = price_wrapper.select_one(
        "#mds_price_value .woocommerce-Price-amount"
    )

    if price_element:

        # Las priset
        price = price_element.get_text(strip=True)

        # Visa resultatet
        print("-----------------------------")
        print("MOXA PRICE TRACKER")
        print("-----------------------------")
        print("Produkt: Moxa NPort 5110")
        print("Butik: Moxa Distry Shop")
        print("Pris:", price)
        print("Valuta: EUR")
        print("Moms: Exkl. moms")
        print("-----------------------------")

    else:
        print("Kunde inte hitta aktuellt pris.")

else:
    print("Kunde inte hitta prisomradet.")
