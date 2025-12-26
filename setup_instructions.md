# E-commerce Product Scraper & Database Setup

## Project Overview

This project is designed to scrape product data from kkgool1.com (a sports jersey e-commerce site) and store it in a structured database. The goal is to extract all product information including:

- Product details (title, item number, price, etc.)
- Multiple product images
- Product options (sizes, badges, customizations with pricing)
- Category hierarchies
- Product specifications

This data will then be used to replicate the product catalog on your own e-commerce site with accurate, product-specific information.

## Project Structure

```
project/
├── scraper.py                 # Main scraping script
├── database_schema.sql        # PostgreSQL database schema
├── requirements.txt           # Python dependencies
├── downloads/                 # Downloaded images (created automatically)
│   └── images/
│       └── [product_id]/
└── products_data_final.json  # Scraped data output (created after scraping)
```

## Prerequisites

### Software Requirements
- Python 3.8 or higher
- PostgreSQL 12 or higher (if using database import)
- 5-10GB free disk space (for images)

### Python Dependencies
Create a `requirements.txt` file with:
```
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
psycopg2-binary>=2.9.0
```

## Installation Steps

### 1. Clone or Setup Repository
```bash
cd your-project-directory
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -c "import requests, bs4; print('Dependencies installed successfully!')"
```

## Usage Guide

### Step 1: Test with a Single Product

Before scraping the entire site, test with one product to ensure everything works:

```python
from scraper import ProductScraper

# Initialize scraper
scraper = ProductScraper()

# Test URL (Man City Special Edition Jersey)
test_url = "https://www.kkgool1.com/25-26-Man-City-Special-Edition-Fans-Soccer-Jersey-%E9%A9%AC%E5%B9%B4-p2793324.html"

# Scrape single product
product_data = scraper.scrape_product_page(test_url)

# Check the data
import json
print(json.dumps(product_data, indent=2))

# Save test result
scraper.products_data.append(product_data)
scraper.save_to_json('test_product.json')

# Download images for this product
scraper.download_images(product_data)
```

**Expected Output:**
- `test_product.json` - JSON file with all product data
- `downloads/images/[item_number]/` - Folder with product images

### Step 2: Scrape Multiple Products from a Category

Test with a single category before going site-wide:

```python
from scraper import ProductScraper

scraper = ProductScraper()

# Get products from one category
category_url = "https://www.kkgool1.com/Man-City-c58021.html"
product_urls = scraper.get_product_urls_from_category(category_url)

print(f"Found {len(product_urls)} products in category")

# Scrape first 10 products
for url in product_urls[:10]:
    product_data = scraper.scrape_product_page(url)
    if product_data:
        scraper.products_data.append(product_data)
        scraper.download_images(product_data)

scraper.save_to_json('category_test.json')
```

### Step 3: Full Site Scrape

⚠️ **WARNING**: This will take several hours and download potentially thousands of products.

```python
from scraper import ProductScraper

scraper = ProductScraper()

# Scrape entire site
# download_imgs=True will download all product images
# download_imgs=False will only save image URLs
scraper.scrape_entire_site(download_imgs=True)
```

**What this does:**
1. Fetches all category URLs from sitemap
2. Extracts all product URLs from each category
3. Scrapes each product page individually
4. Downloads all product images
5. Saves data incrementally (every 10 products)
6. Creates final JSON file with all data

**Monitoring Progress:**
The script prints progress messages:
```
Starting site-wide scrape...
Fetching categories...
Found 156 categories
Scraping category 1/156: https://...
Found 1,234 unique products
Scraping product 1/1234: https://...
```

### Step 4: Review Scraped Data

The JSON structure looks like this:

```json
{
  "url": "https://www.kkgool1.com/...",
  "scraped_at": "2025-12-26T...",
  "basic_info": {
    "title": "25-26 Man City Special Edition Fans Soccer Jersey",
    "item_number": "28510089",
    "brand": "zkhd",
    "weight": "0.25 kg",
    "sold_count": 9
  },
  "images": [
    {
      "url": "https://ssl.images-ssl-mars.com/...",
      "thumbnail": "https://...",
      "alt": "Product image",
      "local_path": "downloads/images/28510089/image_0.jpg"
    }
  ],
  "options": {
    "sizes": [
      {"value": "S", "additional_cost": 0},
      {"value": "M", "additional_cost": 0},
      {"value": "3XL", "additional_cost": 1.0}
    ],
    "badges": [
      {"name": "OKX", "additional_cost": 0},
      {"name": "PreL +OKX", "additional_cost": 1.0}
    ],
    "customization": [
      {"type": "No Name No Number", "additional_cost": 0},
      {"type": "Name / Number (Horse Year Fonts)", "additional_cost": 4.0}
    ]
  },
  "pricing": {
    "base_price": 14.50,
    "currency": "USD"
  },
  "category_path": [
    {"name": "Premier League", "url": "..."},
    {"name": "Man City", "url": "..."},
    {"name": "Kits", "url": "..."}
  ]
}
```

## Database Import (Optional)

### Step 1: Setup PostgreSQL Database

```bash
# Create database
createdb ecommerce_products

# Import schema
psql ecommerce_products < database_schema.sql
```

### Step 2: Configure Database Connection

Edit the database configuration in your import script:

```python
db_config = {
    'dbname': 'ecommerce_products',
    'user': 'your_username',
    'password': 'your_password',
    'host': 'localhost',
    'port': 5432
}
```

### Step 3: Import JSON to Database

The SQL file includes a Python importer class. Extract and use it:

```python
from database_importer import ProductDatabaseImporter

db_config = {
    'dbname': 'ecommerce_products',
    'user': 'postgres',
    'password': 'your_password',
    'host': 'localhost',
    'port': 5432
}

importer = ProductDatabaseImporter(db_config)
importer.import_from_json('products_data_final.json')
importer.close()

print("Database import complete!")
```

### Step 4: Query Your Data

```sql
-- Get all products with their categories
SELECT p.title, p.base_price, c.name as category
FROM products p
JOIN product_categories pc ON p.id = pc.product_id
JOIN categories c ON pc.category_id = c.id;

-- Get product with all options
SELECT p.title, ot.name as option_type, po.value, po.additional_cost
FROM products p
JOIN product_options po ON p.id = po.product_id
JOIN option_types ot ON po.option_type_id = ot.id
WHERE p.item_number = '28510089';

-- Get products by price range
SELECT title, base_price
FROM products
WHERE base_price BETWEEN 10.00 AND 20.00
ORDER BY base_price;
```

## Customization Options

### Adjust Rate Limiting

In `scraper.py`, modify sleep times:

```python
time.sleep(2)  # Change from 2 seconds to your preferred delay
```

### Change Output Directory

```python
scraper = ProductScraper()
# Modify in the download_images method
scraper.download_images(product_data, output_dir='custom/path/images')
```

### Scrape Specific Categories Only

```python
scraper = ProductScraper()

# Define specific categories
target_categories = [
    "https://www.kkgool1.com/Man-City-c58021.html",
    "https://www.kkgool1.com/LIV-c57989.html"
]

for category_url in target_categories:
    product_urls = scraper.get_product_urls_from_category(category_url)
    for url in product_urls:
        product_data = scraper.scrape_product_page(url)
        if product_data:
            scraper.products_data.append(product_data)
            scraper.download_images(product_data)

scraper.save_to_json('specific_categories.json')
```

## Troubleshooting

### Issue: "Connection refused" or "Timeout"
**Solution**: The site might be blocking requests. Increase delays between requests or add random delays.

### Issue: "No products found"
**Solution**: The site's HTML structure may have changed. Check the actual HTML and update CSS selectors in the scraper.

### Issue: Images not downloading
**Solution**: Check your internet connection and verify image URLs are accessible. Some images may require authentication.

### Issue: Database import fails
**Solution**: Ensure PostgreSQL is running and credentials are correct. Check for unique constraint violations.

## Important Notes

### Legal & Ethical Considerations
1. **Check robots.txt**: Visit `https://www.kkgool1.com/robots.txt` to see scraping rules
2. **Terms of Service**: Review the site's Terms of Service
3. **Rate Limiting**: Be respectful - don't overload their servers
4. **Permission**: Consider contacting the site owner for permission
5. **Data Usage**: Ensure your use case complies with copyright and data protection laws

### Performance Tips
1. Run during off-peak hours
2. Use a stable internet connection
3. Monitor disk space (images can be large)
4. Save incrementally to prevent data loss
5. Consider using a VPS if running for extended periods

### Data Accuracy
- The scraper is based on current HTML structure (as of Dec 2025)
- If the site updates, you may need to adjust selectors
- Always verify a sample of scraped data for accuracy
- Test thoroughly before using in production

## Next Steps

After scraping and importing data:

1. **Build API**: Create REST API endpoints to serve product data
2. **Frontend Integration**: Connect your e-commerce frontend to the database
3. **Image Optimization**: Compress and optimize downloaded images
4. **Search Indexing**: Add Elasticsearch for fast product search
5. **Sync Strategy**: Set up periodic re-scraping to keep data fresh

## Support

If you encounter issues:
1. Check the HTML structure hasn't changed
2. Verify all dependencies are installed
3. Review error messages in console output
4. Check `products_data_backup_*.json` files for partial data

## License

This scraper is for educational purposes. Ensure you have proper authorization before scraping any website.
