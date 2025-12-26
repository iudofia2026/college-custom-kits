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
import ast

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

        try:
            # Try to extract from JSON-LD first (more reliable)
            ld_json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in ld_json_scripts:
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'Product':
                        info['title'] = data.get('name', '')
                        info['item_number'] = data.get('mpn') or data.get('sku', '')
                        if data.get('brand'):
                            info['brand'] = data['brand'].get('name', '')
                        break
                except (json.JSONDecodeError, TypeError):
                    pass

            # If not found in JSON-LD, fall back to HTML parsing
            if not info.get('title'):
                title = soup.find('h1')
                if title:
                    title_text = title.get_text(strip=True)
                    # Title might include item number, extract both
                    info['title'] = title_text
                    # Try to extract item number from title
                    item_match = re.search(r'Item\s*NO\.?:?\s*(\d+)', title_text, re.IGNORECASE)
                    if item_match:
                        info['item_number'] = item_match.group(1)

            # Look for item number in page if not found yet
            if not info.get('item_number'):
                item_script = soup.find('script', string=re.compile(r'goods_id'))
                if item_script:
                    match = re.search(r'"goods_id":"(\d+)"', item_script.string)
                    if match:
                        info['item_number'] = match.group(1)

            # Brand - try to find in page data
            if not info.get('brand'):
                brand_link = soup.find('a', href=re.compile(r'-b\d+\.html'))
                if brand_link:
                    info['brand'] = brand_link.get_text(strip=True)

            # Weight - look for it in text
            weight_text = soup.find(text=re.compile(r'Weight', re.IGNORECASE))
            if weight_text:
                parent = weight_text.parent
                if parent:
                    next_sibling = parent.find_next_sibling()
                    if next_sibling:
                        info['weight'] = next_sibling.get_text(strip=True)

            # Sold count - look for sales info
            sold_text = soup.find(text=re.compile(r'Sold|Sales', re.IGNORECASE))
            if sold_text:
                sold_full_text = sold_text.parent.get_text() if sold_text.parent else sold_text
                numbers = re.findall(r'\d+', sold_full_text)
                info['sold_count'] = int(numbers[0]) if numbers else 0

            return info
        except Exception as e:
            print(f"Error extracting basic info: {e}")
            return info
    
    def _extract_images(self, soup):
        """Extract all product images"""
        images = []
        seen_urls = set()

        try:
            # Try to extract from JSON-LD first
            ld_json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in ld_json_scripts:
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'Product' and data.get('image'):
                        image_urls = data['image']
                        if isinstance(image_urls, list):
                            for url in image_urls:
                                if url and url not in seen_urls:
                                    seen_urls.add(url)
                                    images.append({
                                        'url': url,
                                        'thumbnail': url,
                                        'alt': data.get('name', 'Product image')
                                    })
                        break
                except (json.JSONDecodeError, TypeError):
                    pass

            # Supplement with images from HTML if needed
            img_tags = soup.find_all('img', src=re.compile(r'ssl\.images-ssl-mars\.com'))

            for img in img_tags:
                src = img.get('src')
                if src:
                    # Get full resolution by removing size parameters
                    full_src = re.sub(r'\?x-oss-process=.*$', '', src)
                    if full_src not in seen_urls:
                        seen_urls.add(full_src)
                        images.append({
                            'url': full_src,
                            'thumbnail': src,
                            'alt': img.get('alt', 'Product image')
                        })

            # Remove duplicates while preserving order
            unique_images = []
            seen = set()
            for img in images:
                url = img['url']
                if url not in seen:
                    seen.add(url)
                    unique_images.append(img)

            return unique_images
        except Exception as e:
            print(f"Error extracting images: {e}")
            return images
    
    def _extract_options(self, soup):
        """Extract all product options with their variations"""
        options = {}

        try:
            # Look for goods_sale_prop_str JavaScript variable which contains all options
            scripts = soup.find_all('script')
            options_data = None

            for script in scripts:
                if script.string and 'goods_sale_prop_str' in script.string:
                    # Extract JSON from variable assignment
                    match = re.search(r"goods_sale_prop_str='({.*?})';", script.string, re.DOTALL)
                    if match:
                        try:
                            json_str = match.group(1)
                            # The JSON is escaped with backslashes inside single quotes
                            # Use ast.literal_eval to parse it as a Python dict string
                            # First convert the escaped string to a Python dict literal
                            try:
                                options_data = ast.literal_eval(json_str)
                            except (ValueError, SyntaxError):
                                # If literal_eval fails, try json.loads after unescaping
                                # Replace escaped quotes with proper quotes
                                json_str = json_str.replace('\\"', '"')
                                options_data = json.loads(json_str)
                            break
                        except (json.JSONDecodeError, ValueError, SyntaxError) as e:
                            print(f"Error parsing options JSON: {e}")
                            pass

            if options_data:
                # Parse the options structure
                # The data is organized by parent_id relationships
                # parent_id=0 means it's a category (Size, Badge, Customized)
                # parent_id!=0 means it's an option within that category

                categories = {}  # id -> category info
                items_by_category = {}  # category_id -> list of items

                # First pass: separate categories and organize items
                for item_id, item in options_data.items():
                    parent_id = item.get('parent_id')

                    if parent_id == '0':
                        # This is a category
                        categories[item_id] = item
                        items_by_category[item_id] = []
                    else:
                        # This is an item within a category
                        if parent_id not in items_by_category:
                            items_by_category[parent_id] = []
                        items_by_category[parent_id].append((item_id, item))

                # Second pass: organize items by category type
                for cat_id, category in categories.items():
                    category_name = category.get('base_name', '').lower()
                    items_in_category = items_by_category.get(cat_id, [])

                    # Sort items by listorder
                    items_in_category.sort(key=lambda x: int(x[1].get('listorder', 0)))

                    if 'size' in category_name:
                        if 'sizes' not in options:
                            options['sizes'] = []
                        for item_id, item in items_in_category:
                            options['sizes'].append({
                                'value': item.get('base_name', ''),
                                'additional_cost': float(item.get('price', 0))
                            })

                    elif 'badge' in category_name:
                        if 'badges' not in options:
                            options['badges'] = []
                        for item_id, item in items_in_category:
                            img_url = item.get('image')
                            # Clean up escaped slashes in image URLs
                            if img_url:
                                img_url = img_url.replace('\\/', '/')
                            options['badges'].append({
                                'name': item.get('base_name', ''),
                                'image': img_url if img_url else None,
                                'additional_cost': float(item.get('price', 0))
                            })

                    elif 'custom' in category_name:
                        if 'customization' not in options:
                            options['customization'] = []
                        for item_id, item in items_in_category:
                            # Clean up the type name (remove escape sequences)
                            type_name = item.get('base_name', '')
                            if type_name:
                                type_name = type_name.replace('\\/', '/')
                                # Handle unicode escape sequences that came from ast.literal_eval
                                try:
                                    type_name = type_name.encode().decode('unicode_escape')
                                except:
                                    pass
                            options['customization'].append({
                                'type': type_name,
                                'additional_cost': float(item.get('price', 0))
                            })

            return options
        except Exception as e:
            print(f"Error extracting options: {e}")
            return options
    
    def _extract_pricing(self, soup):
        """Extract all pricing information"""
        pricing = {}

        try:
            # Try to extract from JSON-LD first
            ld_json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in ld_json_scripts:
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'Product' and data.get('offers'):
                        offer = data['offers']
                        if isinstance(offer, dict):
                            pricing['base_price'] = float(offer.get('price', 0))
                            pricing['currency'] = offer.get('priceCurrency', 'USD')
                            return pricing
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

            # Fall back to HTML parsing
            price_tag = soup.find(text=re.compile(r'US\$\s*[\d.]+'))
            if price_tag:
                price_match = re.search(r'US\$\s*([\d.]+)', price_tag)
                if price_match:
                    pricing['base_price'] = float(price_match.group(1))
                    pricing['currency'] = 'USD'

            return pricing
        except Exception as e:
            print(f"Error extracting pricing: {e}")
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

        try:
            # Try to extract from JSON-LD BreadcrumbList first
            ld_json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in ld_json_scripts:
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'BreadcrumbList':
                        items = data.get('itemListElement', [])
                        for item in items:
                            if item.get('@type') == 'ListItem':
                                breadcrumb.append({
                                    'name': item.get('name', ''),
                                    'url': item.get('item', '')
                                })
                        if breadcrumb:
                            return breadcrumb
                except (json.JSONDecodeError, TypeError):
                    pass

            # Fall back to HTML parsing
            breadcrumb_links = soup.find_all('a', href=re.compile(r'-c\d+\.html'))
            for link in breadcrumb_links:
                breadcrumb.append({
                    'name': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link.get('href'))
                })

            return breadcrumb
        except Exception as e:
            print(f"Error extracting breadcrumb: {e}")
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
