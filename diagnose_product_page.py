#!/usr/bin/env python3
"""Diagnose product page structure to understand HTML layout"""

import requests
from bs4 import BeautifulSoup

# Test URL
test_url = "https://www.kkgool1.com/25-26-Man-City-Special-Edition-Fans-Soccer-Jersey-%E9%A9%AC%E5%B9%B4-p2793324.html"

print(f"Fetching: {test_url}")
print("-" * 80)

try:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    response = session.get(test_url, timeout=10)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Check for title
        title = soup.find('h1')
        print(f"\nH1 Title found: {title is not None}")
        if title:
            print(f"Title text: {title.get_text(strip=True)[:100]}")

        # Check page length
        print(f"\nHTML content length: {len(response.content)} bytes")

        # Look for common selectors
        print(f"\nSearching for common product elements:")
        print(f"- All <a> tags: {len(soup.find_all('a'))}")
        print(f"- All <img> tags: {len(soup.find_all('img'))}")
        print(f"- All <table> rows: {len(soup.find_all('tr'))}")

        # Save page for inspection
        with open('product_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"\n✓ Full HTML saved to product_page_debug.html for inspection")

    else:
        print(f"✗ Failed to fetch page. Status: {response.status_code}")

except Exception as e:
    print(f"✗ Error: {e}")
