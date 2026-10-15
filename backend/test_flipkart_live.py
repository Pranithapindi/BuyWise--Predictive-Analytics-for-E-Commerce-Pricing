import requests
from bs4 import BeautifulSoup
import re

url = "https://www.flipkart.com/dravya-impex-rc-foldable-drone-dual-camera-4kaltitude-hold-one-key-take-off/p/itm6d212662ec465?pid=DNEHGZPQR3DUFXHY"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print("Status code:", resp.status_code)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    title = soup.find("title")
    print("Title:", title.string if title else "No title")

    # Look for scripts or price tags
    scripts = soup.find_all("script")
    print("Script tags found:", len(scripts))

    # Find any numbers near currency symbol or class names
    divs = soup.find_all(["div", "span"], text=re.compile(r"₹|\d{3,5}"))
    print("Divs/spans matching price pattern:")
    for d in divs[:10]:
        print(d.name, d.get("class"), d.get_text().strip())

    # Check og meta tags
    meta_price = soup.find("meta", property=re.compile(r"price", re.I)) or soup.find("meta", attrs={"name": re.compile(r"price", re.I)})
    print("Meta price:", meta_price)

except Exception as e:
    print("Error:", e)
