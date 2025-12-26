#!/usr/bin/env python3
"""Test script for single product scraping"""

from ecommerce_scraper import ProductScraper
import json

# Initialize scraper
scraper = ProductScraper()

# Test URL (Man City Special Edition Jersey)
test_url = "https://www.kkgool1.com/25-26-Man-City-Special-Edition-Fans-Soccer-Jersey-%E9%A9%AC%E5%B9%B4-p2793324.html"

print("Starting single product test...")
print(f"Testing URL: {test_url}")

# Scrape single product
product_data = scraper.scrape_product_page(test_url)

if product_data:
    # Check the data
    print("\n=== Product Data ===")
    print(json.dumps(product_data, indent=2))

    # Save test result
    scraper.products_data.append(product_data)
    scraper.save_to_json('test_product.json')
    print("\n✓ Saved to test_product.json")

    # Download images for this product
    print("\nDownloading product images...")
    scraper.download_images(product_data)
    print("✓ Images downloaded successfully!")
else:
    print("✗ Failed to scrape product data")
