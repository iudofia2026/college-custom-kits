"""
Comprehensive E-commerce Product Scraper for kkgool1.com
This script scrapes product details, images, and options from the entire site.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

class ProductScraper:
    def __init__(self, base_url="https://www.kkgool1.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.products_data = []
        
    def get_all_category_urls(self):
        """Extract all category URLs from the sitemap or navigation"""
        categories = []
        try:
            response = self.session.get(f"{self.base_url}/h-sitemap-pc.html")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all category links
            category_links = soup.find_all('a', href=re.compile(r'-c\d+\.html'))
            for link in category_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    categories.append(full_url)
            
            return list(set(categories))  # Remove duplicates
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []
    
    def get_product_urls_from_category(self, category_url):
        """Get all product URLs from a category page"""
        product_urls = []
        page = 1
        
        while True:
            try:
                # Add pagination
                paginated_url = f"{category_url}?page={page}" if page > 1 else category_url
                response = self.session.get(paginated_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find product links (adjust selector based on actual HTML structure)
                product_links = soup.find_all('a', href=re.compile(r'-p\d+\.html'))
                
                if not product_links:
                    break
                
                for link in product_links:
                    href = link.get('href')
                    if href and '-p' in href:
                        full_url = urljoin(self.base_url, href)
                        product_urls.append(full_url)
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error on page {page} of {category_url}: {e}")
                break
        
        return list(set(product_urls))
    
    def scrape_product_page(self, product_url):
        """Scrape all details from a single product page"""
        try:
            response = self.session.get(product_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product_data = {
                'url': product_url,
                'scraped_at': datetime.now().isoformat(),
                'basic_info': {},
                'images': [],
                'options': {},
                'pricing': {},
                'description': '',
                'specifications': {}
            }
            
            # Extract basic info
            product_data['basic_info'] = self._extract_basic_info(soup)
            
            # Extract images
            product_data['images'] = self._extract_images(soup)
            
            # Extract product options (Size, Badge, Customization, etc.)
            product_data['options'] = self._extract_options(soup)
            
            # Extract pricing
            product_data['pricing'] = self._extract_pricing(soup)
            
            # Extract description and specifications
            product_data['description'] = self._extract_description(soup)
            product_data['specifications'] = self._extract_specifications(soup)
            
            # Extract breadcrumb/category path
            product_data['category_path'] = self._extract_breadcrumb(soup)
            
            return product_data
            
        except Exception as e:
            print(f"Error scraping {product_url}: {e}")
            return None
    
    def _extract_basic_info(self, soup):
        """Extract product name, item number, brand, etc."""
        info = {}
        
        # Product title
        title = soup.find('h1')
        if title:
            info['title'] = title.get_text(strip=True)
        
        # Item number
        item_no = soup.find(text=re.compile(r'Item NO'))
        if item_no:
            info['item_number'] = item_no.parent.find_next_sibling().get_text(strip=True)
        
        # Brand
        brand = soup.find('a', href=re.compile(r'-b\d+\.html'))
        if brand:
            info['brand'] = brand.get_text(strip=True)
        
        # Weight
        weight = soup.find(text=re.compile(r'Weight'))
        if weight:
            info['weight'] = weight.parent.find_next_sibling().get_text(strip=True)
        
        # Sold count
        sold = soup.find(text=re.compile(r'Sold'))
        if sold:
            sold_text = sold.parent.get_text()
            numbers = re.findall(r'\d+', sold_text)
            info['sold_count'] = int(numbers[0]) if numbers else 0
        
        return info
    
    def _extract_images(self, soup):
        """Extract all product images"""
        images = []
        
        # Main images
        img_tags = soup.find_all('img', src=re.compile(r'ssl\.images-ssl-mars\.com'))
        
        for img in img_tags:
            src = img.get('src')
            if src:
                # Get full resolution by removing size parameters
                full_src = re.sub(r'\?x-oss-process=.*$', '', src)
                images.append({
                    'url': full_src,
                    'thumbnail': src,
                    'alt': img.get('alt', '')
                })
        
        return images
    
    def _extract_options(self, soup):
        """Extract all product options with their variations"""
        options = {}
        
        # Find all option sections
        # Size options
        size_section = soup.find(text=re.compile(r'Size:'))
        if size_section:
            size_parent = size_section.find_parent()
            sizes = []
            for link in size_parent.find_all('a'):
                size_text = link.get_text(strip=True)
                # Extract additional cost if present
                price_match = re.search(r'\+US\$\s*([\d.]+)', size_text)
                sizes.append({
                    'value': re.sub(r'\(.*?\)', '', size_text).strip(),
                    'additional_cost': float(price_match.group(1)) if price_match else 0
                })
            options['sizes'] = sizes
        
        # Badge options
        badge_section = soup.find(text=re.compile(r'Badge:'))
        if badge_section:
            badge_parent = badge_section.find_parent()
            badges = []
            for link in badge_parent.find_all('a'):
                img = link.find('img')
                badge_text = link.get_text(strip=True) if not img else img.get('alt', '')
                price_match = re.search(r'\+US\$\s*([\d.]+)', badge_text)
                badges.append({
                    'name': re.sub(r'\(.*?\)', '', badge_text).strip(),
                    'image': img.get('src') if img else None,
                    'additional_cost': float(price_match.group(1)) if price_match else 0
                })
            options['badges'] = badges
        
        # Customization options
        custom_section = soup.find(text=re.compile(r'Customized:'))
        if custom_section:
            custom_parent = custom_section.find_parent()
            customs = []
            for link in custom_parent.find_all('a'):
                custom_text = link.get_text(strip=True)
                price_match = re.search(r'\+US\$\s*([\d.]+)', custom_text)
                customs.append({
                    'type': re.sub(r'\(.*?\)', '', custom_text).strip(),
                    'additional_cost': float(price_match.group(1)) if price_match else 0
                })
            options['customization'] = customs
        
        return options
    
    def _extract_pricing(self, soup):
        """Extract all pricing information"""
        pricing = {}
        
        # Base price
        price_tag = soup.find(text=re.compile(r'US\$\s*[\d.]+'))
        if price_tag:
            price_match = re.search(r'US\$\s*([\d.]+)', price_tag)
            if price_match:
                pricing['base_price'] = float(price_match.group(1))
                pricing['currency'] = 'USD'
        
        return pricing
    
    def _extract_description(self, soup):
        """Extract product description and details"""
        description = ""
        
        # Look for description in detail tabs or specific sections
        detail_section = soup.find('div', class_=re.compile(r'detail|description'))
        if detail_section:
            description = detail_section.get_text(strip=True)
        
        return description
    
    def _extract_specifications(self, soup):
        """Extract product specifications table"""
        specs = {}
        
        # Find specification table
        spec_rows = soup.find_all('tr')
        for row in spec_rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                specs[key] = value
        
        return specs
    
    def _extract_breadcrumb(self, soup):
        """Extract category breadcrumb"""
        breadcrumb = []
        
        # Find breadcrumb navigation
        breadcrumb_links = soup.find_all('a', href=re.compile(r'-c\d+\.html'))
        for link in breadcrumb_links:
            breadcrumb.append({
                'name': link.get_text(strip=True),
                'url': urljoin(self.base_url, link.get('href'))
            })
        
        return breadcrumb
    
    def download_images(self, product_data, output_dir='downloads/images'):
        """Download all product images"""
        os.makedirs(output_dir, exist_ok=True)
        
        product_id = product_data['basic_info'].get('item_number', 'unknown')
        product_dir = os.path.join(output_dir, product_id)
        os.makedirs(product_dir, exist_ok=True)
        
        for idx, img_data in enumerate(product_data['images']):
            try:
                img_url = img_data['url']
                response = self.session.get(img_url)
                
                # Get file extension
                ext = os.path.splitext(urlparse(img_url).path)[1] or '.jpg'
                filename = f"image_{idx}{ext}"
                filepath = os.path.join(product_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                img_data['local_path'] = filepath
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"Error downloading image {img_url}: {e}")
    
    def save_to_json(self, filepath='products_data.json'):
        """Save all scraped data to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.products_data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.products_data)} products to {filepath}")
    
    def scrape_entire_site(self, download_imgs=True):
        """Main method to scrape the entire site"""
        print("Starting site-wide scrape...")
        
        # Get all categories
        print("Fetching categories...")
        categories = self.get_all_category_urls()
        print(f"Found {len(categories)} categories")
        
        # Get all product URLs
        all_product_urls = []
        for idx, category_url in enumerate(categories, 1):
            print(f"Scraping category {idx}/{len(categories)}: {category_url}")
            product_urls = self.get_product_urls_from_category(category_url)
            all_product_urls.extend(product_urls)
            time.sleep(2)  # Rate limiting
        
        all_product_urls = list(set(all_product_urls))
        print(f"Found {len(all_product_urls)} unique products")
        
        # Scrape each product
        for idx, product_url in enumerate(all_product_urls, 1):
            print(f"Scraping product {idx}/{len(all_product_urls)}: {product_url}")
            
            product_data = self.scrape_product_page(product_url)
            if product_data:
                if download_imgs:
                    self.download_images(product_data)
                
                self.products_data.append(product_data)
                
                # Save incrementally every 10 products
                if idx % 10 == 0:
                    self.save_to_json(f'products_data_backup_{idx}.json')
            
            time.sleep(2)  # Rate limiting between products
        
        # Final save
        self.save_to_json('products_data_final.json')
        print("Scraping complete!")

# Example usage
if __name__ == "__main__":
    scraper = ProductScraper()
    
    # Test with a single product first
    test_url = "https://www.kkgool1.com/25-26-Man-City-Special-Edition-Fans-Soccer-Jersey-%E9%A9%AC%E5%B9%B4-p2793324.html"
    print("Testing with single product...")
    product_data = scraper.scrape_product_page(test_url)
    
    if product_data:
        print(json.dumps(product_data, indent=2))
        scraper.products_data.append(product_data)
        scraper.save_to_json('test_product.json')
        scraper.download_images(product_data)
    
    # Uncomment to scrape entire site (WARNING: This will take hours)
    # scraper.scrape_entire_site(download_imgs=True)
