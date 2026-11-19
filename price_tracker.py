
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

# Leta efter strukturerad produktinformation
scripts = soup.find_all(
    "script",
    type="application/ld+json"
)

print("Antal JSON-LD-block:", len(scripts))

for i, script in enumerate(scripts, start=1):
    print(f"\nJSON-LD-block {i}:")
    print(script.get_text(strip=True)[:2000])
