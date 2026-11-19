
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

print("HTTP-status:", response.status_code)

# Leta efter HTML-element med "price" i klassnamnet
price_elements = soup.select('[class*="price"]')

print("Antal priselement:", len(price_elements))

# Visa de första 10 träffarna
for i, element in enumerate(price_elements[:10], start=1):
    print(f"\nPriselement {i}:")
    print("HTML:", str(element)[:500])
    print("Text:", element.get_text(" ", strip=True)[:200])
