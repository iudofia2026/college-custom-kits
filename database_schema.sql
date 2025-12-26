-- Database Schema for E-commerce Product Data
-- This schema stores all scraped product information with proper relationships

-- Products table (main product information)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    item_number VARCHAR(50) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title VARCHAR(500) NOT NULL,
    brand VARCHAR(100),
    weight VARCHAR(50),
    sold_count INTEGER DEFAULT 0,
    base_price DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'USD',
    description TEXT,
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product images table
CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    alt_text VARCHAR(500),
    local_path VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    url TEXT,
    parent_id INTEGER REFERENCES categories(id),
    level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product-Category relationship (many-to-many)
CREATE TABLE product_categories (
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, category_id)
);

-- Option types table (e.g., Size, Badge, Customization)
CREATE TABLE option_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product options table
CREATE TABLE product_options (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    option_type_id INTEGER REFERENCES option_types(id),
    value VARCHAR(200) NOT NULL,
    additional_cost DECIMAL(10,2) DEFAULT 0,
    image_url TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product specifications table
CREATE TABLE product_specifications (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    spec_key VARCHAR(200) NOT NULL,
    spec_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_products_item_number ON products(item_number);
CREATE INDEX idx_products_title ON products(title);
CREATE INDEX idx_product_images_product_id ON product_images(product_id);
CREATE INDEX idx_product_categories_product_id ON product_categories(product_id);
CREATE INDEX idx_product_categories_category_id ON product_categories(category_id);
CREATE INDEX idx_product_options_product_id ON product_options(product_id);
CREATE INDEX idx_product_specifications_product_id ON product_specifications(product_id);

-- Python script to import JSON data into PostgreSQL database
/*
import json
import psycopg2
from psycopg2.extras import execute_values

class ProductDatabaseImporter:
    def __init__(self, db_config):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()
    
    def import_from_json(self, json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        for product in products:
            self.import_product(product)
        
        self.conn.commit()
        print(f"Imported {len(products)} products")
    
    def import_product(self, product_data):
        try:
            # Insert main product
            product_id = self._insert_product(product_data)
            
            # Insert images
            self._insert_images(product_id, product_data.get('images', []))
            
            # Insert categories
            self._insert_categories(product_id, product_data.get('category_path', []))
            
            # Insert options
            self._insert_options(product_id, product_data.get('options', {}))
            
            # Insert specifications
            self._insert_specifications(product_id, product_data.get('specifications', {}))
            
        except Exception as e:
            print(f"Error importing product: {e}")
            self.conn.rollback()
    
    def _insert_product(self, data):
        basic_info = data.get('basic_info', {})
        pricing = data.get('pricing', {})
        
        self.cursor.execute('''
            INSERT INTO products 
            (item_number, url, title, brand, weight, sold_count, base_price, currency, description, scraped_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (item_number) DO UPDATE SET
                url = EXCLUDED.url,
                title = EXCLUDED.title,
                base_price = EXCLUDED.base_price,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        ''', (
            basic_info.get('item_number'),
            data.get('url'),
            basic_info.get('title'),
            basic_info.get('brand'),
            basic_info.get('weight'),
            basic_info.get('sold_count', 0),
            pricing.get('base_price'),
            pricing.get('currency', 'USD'),
            data.get('description'),
            data.get('scraped_at')
        ))
        
        return self.cursor.fetchone()[0]
    
    def _insert_images(self, product_id, images):
        if not images:
            return
        
        # Delete existing images
        self.cursor.execute('DELETE FROM product_images WHERE product_id = %s', (product_id,))
        
        image_data = [
            (product_id, img['url'], img.get('thumbnail'), img.get('alt'), 
             img.get('local_path'), idx)
            for idx, img in enumerate(images)
        ]
        
        execute_values(self.cursor, '''
            INSERT INTO product_images 
            (product_id, url, thumbnail_url, alt_text, local_path, display_order)
            VALUES %s
        ''', image_data)
    
    def _insert_categories(self, product_id, category_path):
        if not category_path:
            return
        
        parent_id = None
        for level, cat in enumerate(category_path):
            # Insert or get category
            self.cursor.execute('''
                INSERT INTO categories (name, url, parent_id, level)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            ''', (cat['name'], cat.get('url'), parent_id, level))
            
            result = self.cursor.fetchone()
            if result:
                category_id = result[0]
            else:
                self.cursor.execute(
                    'SELECT id FROM categories WHERE name = %s AND level = %s',
                    (cat['name'], level)
                )
                category_id = self.cursor.fetchone()[0]
            
            parent_id = category_id
        
        # Link product to final category
        if parent_id:
            self.cursor.execute('''
                INSERT INTO product_categories (product_id, category_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            ''', (product_id, parent_id))
    
    def _insert_options(self, product_id, options):
        if not options:
            return
        
        for option_type_name, option_values in options.items():
            # Get or create option type
            self.cursor.execute('''
                INSERT INTO option_types (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            ''', (option_type_name,))
            
            result = self.cursor.fetchone()
            if result:
                option_type_id = result[0]
            else:
                self.cursor.execute(
                    'SELECT id FROM option_types WHERE name = %s',
                    (option_type_name,)
                )
                option_type_id = self.cursor.fetchone()[0]
            
            # Insert option values
            for idx, opt in enumerate(option_values):
                value = opt.get('value') or opt.get('name') or opt.get('type')
                if value:
                    self.cursor.execute('''
                        INSERT INTO product_options 
                        (product_id, option_type_id, value, additional_cost, image_url, display_order)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (
                        product_id,
                        option_type_id,
                        value,
                        opt.get('additional_cost', 0),
                        opt.get('image'),
                        idx
                    ))
    
    def _insert_specifications(self, product_id, specifications):
        if not specifications:
            return
        
        spec_data = [
            (product_id, key, value)
            for key, value in specifications.items()
        ]
        
        execute_values(self.cursor, '''
            INSERT INTO product_specifications (product_id, spec_key, spec_value)
            VALUES %s
        ''', spec_data)
    
    def close(self):
        self.cursor.close()
        self.conn.close()

# Usage example
if __name__ == "__main__":
    db_config = {
        'dbname': 'your_database',
        'user': 'your_user',
        'password': 'your_password',
        'host': 'localhost',
        'port': 5432
    }
    
    importer = ProductDatabaseImporter(db_config)
    importer.import_from_json('products_data_final.json')
    importer.close()
*/
