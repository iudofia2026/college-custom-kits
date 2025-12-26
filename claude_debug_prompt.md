# Context for Claude: E-commerce Scraper Debugging

## Project Overview
I'm building a web scraper to extract product data from kkgool1.com (sports jersey e-commerce site) to replicate their product catalog on my own site. The scraper needs to extract:
- Product details (title, price, item number, etc.)
- All product images
- Product options (sizes, badges, customizations with additional costs)
- Category paths
- Specifications

## Current Situation

### What's Working ✅
- Virtual environment is set up (Python 3.9.6)
- All dependencies installed (requests, beautifulsoup4, lxml, psycopg2-binary)
- The target website is accessible
- HTML content is loading correctly
- The page contains JSON-LD structured data which could be useful

### The Problem ❌
The scraper in `ecommerce_scraper.py` has parsing errors. When running:
```python
python test_single_product.py
```

It fails with:
```
AttributeError: 'NoneType' object has no attribute 'get_text'
```

The issue is that the CSS selectors in the scraper don't match the actual HTML structure of the website. The selectors were written generically but don't match the specific structure of kkgool1.com.

### Test Product URL
```
https://www.kkgool1.com/25-26-Man-City-Special-Edition-Fans-Soccer-Jersey-%E9%A9%AC%E5%B9%B4-p2793324.html
```

## What I Need Help With

### Primary Goal
Fix the `ecommerce_scraper.py` file so it correctly extracts data from kkgool1.com product pages.

### Specific Requirements

1. **Extract Basic Product Info:**
   - Product title: "25-26 Man City Special Edition Fans Soccer Jersey (马年)"
   - Item number: "28510089"
   - Brand: "zkhd"
   - Weight: "0.25 kg"
   - Sold count: 9
   - Base price: $14.50

2. **Extract All Images:**
   - Multiple product images (10+ images per product)
   - Full resolution URLs (removing query parameters)
   - Thumbnail URLs
   - Alt text

3. **Extract Product Options** (this is critical - each option has pricing):
   - **Sizes**: S, M, L, XL, XXL, 3XL (+$1.00), 4XL (+$1.00)
   - **Badges**: 
     - OKX (左袖广告) - base
     - PreL +OKX (34英超普+左袖广告) - +$1.00
     - PreL +NO..for +OKX (34英超普/章下字+左袖广告) - +$2.00
     - UCL +OKX (欧冠新章+左袖广告) - +$2.00
     - Carabao Cup +OKX (英联赛杯+左袖广告) - +$1.00
   - **Customization**:
     - No Name No Number - base
     - Name / Number (Horse Year Fonts)马年字体 - +$4.00
     - Name / Number (Pre League Fonts)联赛字体 - +$3.00

4. **Extract Category Path/Breadcrumb:**
   - Home > Premier League > Man City > Kits

5. **Extract Product Specifications:**
   - Any table data showing product specs

## Files in Repository

```
college-custom-kits/
├── ecommerce_scraper.py          # The scraper that needs fixing
├── database_schema.sql           # PostgreSQL schema (working)
├── requirements.txt              # Dependencies (installed)
├── test_single_product.py        # Test script (created)
├── diagnose_product_page.py      # HTML diagnostic script
├── product_page_debug.html       # Downloaded HTML for reference
└── venv/                         # Virtual environment (set up)
```

## Key Observations

From the diagnostic script, we know:
- The page loads successfully
- The page contains JSON-LD structured data in `<script type="application/ld+json">` tags
- The actual HTML structure differs from what the generic scraper expects
- Product options are likely in JavaScript/dynamic elements or specific HTML patterns

## What I Need from Claude

Please analyze the scraper code and the actual HTML structure, then:

1. **Fix the parsing methods** in `ecommerce_scraper.py`:
   - `_extract_basic_info()` - Fix selectors to match actual HTML
   - `_extract_images()` - Ensure it gets all images
   - `_extract_options()` - This is CRITICAL - must extract all option types and their prices
   - `_extract_pricing()` - Get base price correctly
   - `_extract_breadcrumb()` - Get category path
   - `_extract_specifications()` - Get product specs

2. **Add robust error handling:**
   - Check if elements exist before calling methods
   - Log missing elements for debugging
   - Don't crash if some data is missing

3. **Consider using JSON-LD data** if available:
   - The page might have structured data that's easier to parse
   - Fall back to HTML parsing if JSON-LD doesn't have all data

4. **Maintain the same output structure:**
   - The JSON output format should remain the same
   - Database schema expects specific field names
   - Don't break the existing API

## Testing Instructions

After fixing, I should be able to run:
```bash
source venv/bin/activate
python test_single_product.py
```

And get a `test_product.json` file with complete, accurate data like:
```json
{
  "url": "https://...",
  "basic_info": {
    "title": "25-26 Man City Special Edition Fans Soccer Jersey (马年)",
    "item_number": "28510089",
    "brand": "zkhd",
    "weight": "0.25 kg",
    "sold_count": 9
  },
  "images": [
    {"url": "https://...", "thumbnail": "https://...", "alt": "..."}
  ],
  "options": {
    "sizes": [
      {"value": "S", "additional_cost": 0},
      {"value": "3XL", "additional_cost": 1.0}
    ],
    "badges": [...],
    "customization": [...]
  },
  "pricing": {
    "base_price": 14.50,
    "currency": "USD"
  },
  "category_path": [...]
}
```

## Additional Context

- **Rate limiting**: Already included in code (good)
- **Legal considerations**: I'll handle this separately
- **Database import**: Working, just needs correct JSON structure
- **Full site scrape**: Will test after single product works

## Questions to Consider

1. Should we parse JSON-LD data first, then fall back to HTML parsing?
2. How do we handle dynamic JavaScript-rendered options?
3. Should we validate extracted data (e.g., check if prices are numbers)?
4. What should happen if critical data (like item_number) is missing?

## Expected Deliverable

A corrected version of `ecommerce_scraper.py` that:
- Successfully scrapes the test product URL
- Extracts ALL data accurately (especially options with pricing)
- Has proper error handling
- Works with the existing test script
- Maintains compatibility with the database schema

Please help me fix this scraper so I can proceed with scraping the full catalog!
