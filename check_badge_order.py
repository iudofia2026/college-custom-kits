#!/usr/bin/env python3
"""Check badge order in extracted data"""

from ecommerce_scraper import ProductScraper
from bs4 import BeautifulSoup
import re
import json
import ast

# Initialize scraper
scraper = ProductScraper()

# Test URL
test_url = "https://www.kkgool1.com/25-26-Man-City-Special-Edition-Fans-Soccer-Jersey-%E9%A9%AC%E5%B9%B4-p2793324.html"

print("Fetching product page...")
response = scraper.session.get(test_url)
soup = BeautifulSoup(response.content, 'html.parser')

# Try to find goods_sale_prop_str
scripts = soup.find_all('script')

for script in scripts:
    if script.string and 'goods_sale_prop_str' in script.string:
        match = re.search(r"goods_sale_prop_str='({.*?})';", script.string, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                options_data = ast.literal_eval(json_str)
            except:
                json_str = json_str.replace('\\"', '"')
                options_data = json.loads(json_str)

            # Find badge category and its items
            for item_id, item in options_data.items():
                if item.get('base_name') == 'Badge':
                    print(f"\nFound Badge category: {item_id}")
                    badge_category_id = item_id

                    # Find all badges (items with parent_id = badge_category_id)
                    badges = []
                    for iid, iitem in options_data.items():
                        if iitem.get('parent_id') == badge_category_id:
                            badges.append((iid, iitem))

                    # Sort by listorder
                    badges.sort(key=lambda x: int(x[1].get('listorder', 0)))

                    print(f"\nFound {len(badges)} badges (in listorder):")
                    for iid, iitem in badges:
                        print(f"  {iid}: {iitem.get('base_name')} (listorder: {iitem.get('listorder')}, price: {iitem.get('price')})")
        break
