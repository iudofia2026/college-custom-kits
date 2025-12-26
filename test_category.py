#!/usr/bin/env python3
"""Test script for scraping a single category"""

from ecommerce_scraper import ProductScraper
import json

# Initialize scraper
scraper = ProductScraper()

# Get products from one category
category_url = "https://www.kkgool1.com/Man-City-c58021.html"

print("Starting category test...")
print(f"Testing category URL: {category_url}")

# Get product URLs from category
print("\nFetching product URLs from category...")
product_urls = scraper.get_product_urls_from_category(category_url)
print(f"Found {len(product_urls)} products in category")

# Scrape first 5 products
print("\nScraping first 5 products...")
products_scraped = 0
for i, url in enumerate(product_urls[:5], 1):
    print(f"\n  {i}. Scraping: {url}")
    product_data = scraper.scrape_product_page(url)
    if product_data:
        scraper.products_data.append(product_data)
        scraper.download_images(product_data)
        products_scraped += 1
        print(f"     ✓ Success - {len(product_data['images'])} images")
    else:
        print(f"     ✗ Failed to scrape")

# Save results
scraper.save_to_json('category_test.json')
print(f"\n✓ Scraped {products_scraped}/5 products successfully")
print(f"✓ Saved to category_test.json")

# Show sample data
if scraper.products_data:
    print(f"\nSample product data (first product):")
    sample = scraper.products_data[0]
    print(f"  Title: {sample['basic_info'].get('title', 'N/A')[:60]}...")
    print(f"  Price: ${sample['pricing'].get('base_price', 'N/A')}")
    print(f"  Images: {len(sample['images'])}")
    print(f"  Options: {len(sample['options'].get('sizes', []))} sizes, {len(sample['options'].get('badges', []))} badges")
