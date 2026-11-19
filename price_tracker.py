
import requests
from bs4 import BeautifulSoup

# Produktsidan vi vill kontrollera
url = "https://moxa.distry.shop/dispositivi-server-e-seriali/nport-5110-moxa/"

# Hämta webbsidans innehåll
response = requests.get(
    url,
    headers={"User-Agent": "MoxaPriceTracker/0.1"},
    timeout=20
)

response.raise_for_status()

# Läs sidans HTML-kod
soup = BeautifulSoup(response.text, "html.parser")

# Visa sidans titel
title = soup.title.get_text(strip=True) if soup.title else "Ingen titel"

print("Produkten vi kontrollerar:")
print(title)
print("HTTP-status:", response.status_code)
