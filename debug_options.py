#!/usr/bin/env python3
"""Debug script to extract product options"""

from ecommerce_scraper import ProductScraper
from bs4 import BeautifulSoup
import re
import json

# Initialize scraper
scraper = ProductScraper()

# Test URL
test_url = "https://www.kkgool1.com/25-26-Man-City-Special-Edition-Fans-Soccer-Jersey-%E9%A9%AC%E5%B9%B4-p2793324.html"

print("Fetching product page...")
response = scraper.session.get(test_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Try to find goods_sale_prop_str
scripts = soup.find_all('script')
print(f"Found {len(scripts)} script tags")

for i, script in enumerate(scripts):
    if script.string and 'goods_sale_prop_str' in script.string:
        print(f"\nFound goods_sale_prop_str in script {i}")
        print(f"Script content length: {len(script.string)}")

        # Try to extract with the regex
        match = re.search(r"goods_sale_prop_str='({.*?})';", script.string, re.DOTALL)
        if match:
            print(f"Regex match found, length: {len(match.group(1))}")
            json_str = match.group(1)
            # Unescape the JSON
            json_str = json_str.replace("\\/", "/")

            # Print first 500 chars to debug
            print(f"\nFirst 500 chars of extracted JSON:")
            print(json_str[:500])

            try:
                data = json.loads(json_str)
                print(f"\nSuccessfully parsed JSON with {len(data)} items")
                print(f"\nFirst 3 items:")
                for i, (key, val) in enumerate(data.items()):
                    if i < 3:
                        print(f"\n  Key: {key}")
                        print(f"  Value: {val}")
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
        else:
            print("Regex match NOT found")
            # Print snippet to see what's there
            idx = script.string.find('goods_sale_prop_str=')
            if idx >= 0:
                print(f"Context around goods_sale_prop_str:")
                print(script.string[idx:idx+200])
