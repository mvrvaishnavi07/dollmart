import os
import sys
import hashlib
import sqlite3
import datetime
import random
import string
from getpass import getpass
from tabulate import tabulate

class Database:

    def __init__(self, db_name="dollmartv2.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.initialize_manager()

    def create_tables(self):
        # Users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            contact_number TEXT,
            password TEXT NOT NULL,
            user_type TEXT DEFAULT 'individual',
            registration_date TEXT ,
            coupon_counter INTEGER DEFAULT 0
        )
        ''')

        # Categories table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        ''')

        # Products table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            retail_price REAL NOT NULL,
            wholesale_price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories (category_id)
        )
        ''')

        # Cart table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        )
        ''')

        # Orders table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_date TEXT,
            total_amount REAL,
            payment_status TEXT DEFAULT 'pending',
            payment_method TEXT,
            order_status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        # Order items table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY (order_id) REFERENCES orders (order_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        )
        ''')

        # Coupons table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            coupon_id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_percentage INTEGER,
            valid_until TEXT,
            is_used INTEGER DEFAULT 0,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        self.conn.commit()

    def initialize_manager(self):
        manager_email = "dollmartManager@gmail.com"
        manager_password = "ManagerDollmart79"

        # Check if manager already exists
        self.cursor.execute("SELECT * FROM users WHERE email = ?", (manager_email,))
        if not self.cursor.fetchone():
            # Hash the password
            hashed_password = hashlib.sha256(manager_password.encode()).hexdigest()

            # Insert manager into users table
            self.cursor.execute('''
            INSERT INTO users (first_name, email, contact_number, password, user_type, registration_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', ("Manager", manager_email, "0000000000", hashed_password, "manager", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            self.conn.commit()
            print("Manager account created successfully.")

    def close(self):
        self.conn.close()


class User:

    def __init__(self, db):
        self.db = db
        self.current_user = None

    def register(self):
        print("\n===== USER REGISTRATION =====")
        first_name = input("Enter your first name: ")
        email = input("Enter your email: ")
        contact_number = input("Enter your contact number: ")
        password = getpass("Enter your password (min 4 characters): ")

        # Validate password length
        if len(password) < 4:
            print("Password should be at least 4 characters long!")
            return False

        # User type selection
        print("\nSelect user type:")
        print("1. Individual")
        print("2. Bulk ordering")
        choice = input("Enter choice (1-2): ")

        user_type = "individual" if choice == "1" else "bulk"

        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            # Insert user into database
            self.db.cursor.execute('''
            INSERT INTO users (first_name, email, contact_number, password, user_type, registration_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (first_name, email, contact_number, hashed_password, user_type, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            self.db.conn.commit()
            print("Registration successful! You can now login.")
            return True
        except sqlite3.IntegrityError:
            print("Email already exists. Please try again with a different email.")
            return False

    def login(self):
        print("\n===== USER LOGIN =====")
        email = input("Enter your email: ")
        password = getpass("Enter your password: ")

        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Check credentials
        self.db.cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, hashed_password))
        user = self.db.cursor.fetchone()

        if user:
            self.current_user = {
                "user_id": user[0],
                "first_name": user[1],
                "email": user[2],
                "contact_number": user[3],
                "user_type": user[5]
            }
            print(f"\nWelcome, {user[1]}!")
            return True
        else:
            print("Invalid email or password. Please try again.")
            return False

    def update_user_type(self):
        if not self.current_user:
            print("Please login first.")
            return

        print("\n===== UPDATE USER TYPE =====")
        print("Current user type:", self.current_user["user_type"])
        print("\nSelect new user type:")
        print("1. Individual")
        print("2. Bulk ordering")
        choice = input("Enter choice (1-2): ")

        user_type = "individual" if choice == "1" else "bulk"

        # Update user type in database
        self.db.cursor.execute("UPDATE users SET user_type = ? WHERE user_id = ?",
                            (user_type, self.current_user["user_id"]))
        self.db.conn.commit()

        # Update current user object
        self.current_user["user_type"] = user_type
        print("User type updated successfully!")

    def view_all_customers(self):
        query = '''
        SELECT user_id, first_name AS full_name, email, user_type
        FROM users
        WHERE email != 'dollmartManager@gmail.com'
        ORDER BY user_type DESC, first_name ASC
        '''

        self.db.cursor.execute(query)
        customers = self.db.cursor.fetchall()

        if not customers:
            print("No customers found.")
            return

        print("\n===== ALL CUSTOMERS =====")
        headers = ["User ID", "Full Name", "Email", "User Type"]
        print(tabulate(customers, headers=headers, tablefmt="grid"))


    def logout(self):
        if self.current_user:
            print(f"Bye, {self.current_user['first_name']}!")
            self.current_user = None
        else:
            print("No user is currently logged in.")


class Product:

    def __init__(self, db):
        self.db = db

    def add_product(self):
        print("\n===== ADD NEW PRODUCT =====")
        name = input("Enter product name: ")
        description = input("Enter product description: ")

        # Category handling
        category = input("Enter product category: ")

        # Check if category exists, if not create it
        self.db.cursor.execute("SELECT category_id FROM categories WHERE name = ?", (category.lower(),))
        category_result = self.db.cursor.fetchone()

        if category_result:
            category_id = category_result[0]
        else:
            # Create new category
            self.db.cursor.execute("INSERT INTO categories (name) VALUES (?)", (category.lower(),))
            self.db.conn.commit()
            category_id = self.db.cursor.lastrowid
            print(f"New category '{category}' created.")

        # Product pricing and stock
        retail_price = float(input("Enter retail price: "))
        wholesale_price = float(input("Enter wholesale price: "))
        stock = int(input("Enter initial stock quantity: "))

        # Insert product into database
        self.db.cursor.execute('''
        INSERT INTO products (name, description, category_id, retail_price, wholesale_price, stock)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, category_id, retail_price, wholesale_price, stock))

        self.db.conn.commit()
        print(f"Product '{name}' added successfully!")

    def list_products(self, category=None, search_term=None):
        query = '''
        SELECT p.product_id, p.name, p.description, c.name, p.retail_price, p.wholesale_price, p.stock
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        '''

        params = []

        if category and search_term:
            query += " WHERE c.name = ? AND (p.name LIKE ? OR p.description LIKE ?)"
            params = [category.lower(), f"%{search_term}%", f"%{search_term}%"]
        elif category:
            query += " WHERE c.name = ?"
            params = [category.lower()]
        elif search_term:
            query += " WHERE p.name LIKE ? OR p.description LIKE ?"
            params = [f"%{search_term}%", f"%{search_term}%"]

        self.db.cursor.execute(query, params)
        products = self.db.cursor.fetchall()

        if not products:
            print("No products found.")
            return []

        print("\n===== PRODUCT LIST =====")
        headers = ["ID", "Name", "Description", "Category", "Retail Price", "Wholesale Price", "Stock"]
        print(tabulate(products, headers=headers, tablefmt="grid"))

        return products

    def search_products(self):
        print("\n===== SEARCH PRODUCTS =====")
        print("1. Search by category")
        print("2. Search by keyword")
        # print("3. Advanced search (category + keyword)")
        choice = input("Enter choice (1-2): ")

        if choice == "1":
            # List all categories
            self.db.cursor.execute("SELECT name FROM categories ORDER BY name")
            categories = self.db.cursor.fetchall()

            print("\nAvailable categories:")
            for idx, cat in enumerate(categories, 1):
                print(f"{idx}. {cat[0]}")

            cat_idx = int(input("\nEnter category number: ")) - 1
            if 0 <= cat_idx < len(categories):
                return self.list_products(category=categories[cat_idx][0])
            else:
                print("Invalid category number.")
                return []

        elif choice == "2":
            keyword = input("Enter search keyword: ")
            return self.list_products(search_term=keyword)

    def view_categories(self):
        self.db.cursor.execute("SELECT name FROM categories ORDER BY name")
        categories = self.db.cursor.fetchall()

        if not categories:
            print("No categories found.")
            return

        print("\n===== PRODUCT CATEGORIES =====")
        for idx, cat in enumerate(categories, 1):
            print(f"{idx}. {cat[0]}")



    def update_product(self):
        product_id = input("Enter the Product ID to update: ").strip()

        # Check if product exists
        self.db.cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        product = self.db.cursor.fetchone()

        if not product:
            print("Product not found.")
            return

        # Extract product details
        product_id, name, description, category_id, retail_price, wholesale_price, stock = product

        print("\n===== Current Product Details =====")
        headers = ["Product ID", "Name", "Description", "Category", "Retail Price", "Wholesale Price", "Stock"]
        print(tabulate([[product_id, name, description, category_id, retail_price, wholesale_price, stock]],
                    headers=headers, tablefmt="grid"))

        # Manager selects what to update
        print("\nWhich field would you like to update?")
        print("1. Retail Price")
        print("2. Wholesale Price")
        print("3. Stock")
        choice = input("Enter your choice (1-3): ").strip()

        if choice == "1":
            new_value = input(f"Enter new Retail Price (or press Enter to keep {retail_price}): ").strip()
            if new_value:
                new_value = float(new_value)
                self.db.cursor.execute("UPDATE products SET retail_price = ? WHERE product_id = ?", (new_value, product_id))
                print("Retail Price updated successfully!")

        elif choice == "2":
            new_value = input(f"Enter new Wholesale Price (or press Enter to keep {wholesale_price}): ").strip()
            if new_value:
                new_value = float(new_value)
                self.db.cursor.execute("UPDATE products SET wholesale_price = ? WHERE product_id = ?", (new_value, product_id))
                print("Wholesale Price updated successfully!")

        elif choice == "3":
            new_value = input(f"Enter new Stock (or press Enter to keep {stock}): ").strip()
            if new_value:
                new_value = int(new_value)
                self.db.cursor.execute("UPDATE products SET stock = ? WHERE product_id = ?", (new_value, product_id))
                print("Stock updated successfully!")

        else:
            print("Invalid choice. No changes made.")

        # Commit changes
        self.db.conn.commit()



class Cart:
    def __init__(self, db, user):
        self.db = db
        self.user = user

    def add_to_cart(self, product_id=None, quantity=1):
        if not self.user.current_user:
            print("Please login first.")
            return

        if not product_id:
            product_id = input("Enter product ID to add to cart: ")
            quantity = int(input("Enter quantity: "))

        # Check if product exists and has enough stock
        self.db.cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        product = self.db.cursor.fetchone()

        if not product:
            print("Product not found.")
            return

        if product[6] < quantity:
            print("Not enough stock available.")
            return

        # Check if product already in cart
        self.db.cursor.execute('''
        SELECT cart_id, quantity FROM cart
        WHERE user_id = ? AND product_id = ?
        ''', (self.user.current_user["user_id"], product_id))

        cart_item = self.db.cursor.fetchone()

        if cart_item:
            # Update quantity
            new_quantity = cart_item[1] + quantity
            self.db.cursor.execute('''
            UPDATE cart SET quantity = ? WHERE cart_id = ?
            ''', (new_quantity, cart_item[0]))
        else:
            # Add new item to cart
            self.db.cursor.execute('''
            INSERT INTO cart (user_id, product_id, quantity)
            VALUES (?, ?, ?)
            ''', (self.user.current_user["user_id"], product_id, quantity))

        self.db.conn.commit()
        print(f"{quantity} item(s) added to cart.")

    def view_cart(self):
        if not self.user.current_user:
            print("Please login first.")
            return

        self.db.cursor.execute('''
        SELECT c.cart_id, p.product_id, p.name, p.description, cat.name,
               CASE WHEN u.user_type = 'bulk' THEN p.wholesale_price ELSE p.retail_price END as price,
               c.quantity,
               CASE WHEN u.user_type = 'bulk' THEN p.wholesale_price * c.quantity ELSE p.retail_price * c.quantity END as total
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        JOIN categories cat ON p.category_id = cat.category_id
        JOIN users u ON c.user_id = u.user_id
        WHERE c.user_id = ?
        ''', (self.user.current_user["user_id"],))

        cart_items = self.db.cursor.fetchall()

        if not cart_items:
            print("Your cart is empty.")
            return []

        print("\n===== YOUR CART =====")
        headers = ["Cart ID", "Product ID", "Name", "Description", "Category", "Price", "Quantity", "Total"]
        print(tabulate(cart_items, headers=headers, tablefmt="grid"))

        # Calculate total
        total = sum(item[7] for item in cart_items)
        print(f"\nTotal: ${total:.2f}")

        return cart_items

    def update_cart_item(self):
        if not self.user.current_user:
            print("Please login first.")
            return

        cart_items = self.view_cart()
        if not cart_items:
            return

        cart_id = input("\nEnter Cart ID to update (or 0 to cancel): ")
        if cart_id == "0":
            return

        # Check if cart item exists and belongs to the user
        self.db.cursor.execute('''
        SELECT c.cart_id, p.product_id, p.name, p.stock, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.cart_id = ? AND c.user_id = ?
        ''', (cart_id, self.user.current_user["user_id"]))

        cart_item = self.db.cursor.fetchone()

        if not cart_item:
            print("Cart item not found or doesn't belong to you.")
            return

        print(f"Updating {cart_item[2]} (Current quantity: {cart_item[4]}, Available stock: {cart_item[3]})")
        new_quantity = int(input("Enter new quantity (0 to remove): "))

        if new_quantity == 0:
            # Remove item from cart
            self.db.cursor.execute("DELETE FROM cart WHERE cart_id = ?", (cart_id,))
            print("Item removed from cart.")
        elif new_quantity > cart_item[3]:
            print("Not enough stock available.")
            return
        else:
            # Update quantity
            self.db.cursor.execute("UPDATE cart SET quantity = ? WHERE cart_id = ?", (new_quantity, cart_id))
            print("Cart updated successfully.")

        self.db.conn.commit()

    def clear_cart(self):
        # Check if cart is empty
        cart_items = self.cart.view_cart()
        if not cart_items:
            print("Your cart is empty. Add items before placing an order.")
            return

        if not self.user.current_user:
            print("Please login first.")
            return

        confirm = input("Are you sure you want to clear your cart? (y/n): ")
        if confirm.lower() != 'y':
            return

        self.db.cursor.execute("DELETE FROM cart WHERE user_id = ?", (self.user.current_user["user_id"],))
        self.db.conn.commit()
        print("Cart cleared successfully.")


class Order:

    def __init__(self, db, user, cart):
        self.db = db
        self.user = user
        self.cart = cart

    def place_order(self):
        if not self.user.current_user:
            print("Please login first.")
            return

        # Check if cart is empty
        cart_items = self.cart.view_cart()
        if not cart_items:
            print("Your cart is empty. Add items before placing an order.")
            return

        # Calculate total amount
        total_amount = sum(item[7] for item in cart_items)

        # Check for applicable coupons
        self.db.cursor.execute('''
        SELECT coupon_id, code, discount_percentage
        FROM coupons
        WHERE user_id = ? AND is_used = 0 AND valid_until >= date('now')
        ''', (self.user.current_user["user_id"],))

        available_coupons = self.db.cursor.fetchall()

        applied_coupon_id = None
        discount_amount = 0

        if available_coupons:
            print("\n===== AVAILABLE COUPONS =====")
            for idx, coupon in enumerate(available_coupons, 1):
                print(f"{idx}. Code: {coupon[1]} - {coupon[2]}% discount")

            use_coupon = input("\nApply a coupon? (y/n): ")
            if use_coupon.lower() == 'y':
                while True:
                    coupon_code = input("Enter the coupon code: ").strip().upper()

                    # Find the matching coupon
                    selected_coupon = next((c for c in available_coupons if c[1] == coupon_code), None)

                    if selected_coupon:
                        applied_coupon_id = selected_coupon[0]
                        discount_percentage = selected_coupon[2]
                        discount_amount = total_amount * (discount_percentage / 100)
                        total_amount -= discount_amount
                        print(f"Coupon applied! You saved: ${discount_amount:.2f}")
                        print(f"\nOrder Total after coupon (if applied): ${total_amount:.2f}")
                        break
                    else:
                        print("Invalid coupon code. Please try again.")



        print(f"\nOrder Total: ${total_amount:.2f}")

        # Payment method
        print("\n===== PAYMENT METHOD =====")
        print("1. Credit Card")
        print("2. UPI")
        print("3. Net Banking")
        payment_method = input("Select payment method (1-3): ")

        payment_methods = {
            "1": "Credit Card",
            "2": "UPI",
            "3": "Net Banking"
        }

        selected_payment = payment_methods.get(payment_method, "UPI")
        confirm = input("Are you sure you want to proceed with the payment and complete order? : ")
        if confirm.lower() != 'y':
            return

        # Process payment
        print(f"\nProcessing payment of ${total_amount:.2f} via {selected_payment}...")
        payment_status = "done"  # In a real application, this would involve a payment gateway

        # Create order
        order_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.cursor.execute('''
        INSERT INTO orders (user_id, order_date, total_amount, payment_status, payment_method, order_status)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.user.current_user["user_id"], order_date, total_amount, payment_status, selected_payment,
              "done" if payment_status == "done" else "pending"))

        order_id = self.db.cursor.lastrowid

        # Add order items
        for item in cart_items:
            product_id = item[1]
            price = item[5]
            quantity = item[6]

            # Add to order items
            self.db.cursor.execute('''
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
            ''', (order_id, product_id, quantity, price))

            # Update product stock
            self.db.cursor.execute('''
            UPDATE products SET stock = stock - ? WHERE product_id = ?
            ''', (quantity, product_id))

        # Mark coupon as used if applied
        if applied_coupon_id:
            self.db.cursor.execute("UPDATE coupons SET is_used = 1 WHERE coupon_id = ?", (applied_coupon_id,))

        # Clear cart
        self.db.cursor.execute("DELETE FROM cart WHERE user_id = ?", (self.user.current_user["user_id"],))

        # Generate new coupon for regular customers
        self.generate_coupon_for_regular_customer()

        self.db.conn.commit()
        print(f"Order placed successfully! Your order ID is: {order_id}")

        return order_id

    def generate_coupon_for_regular_customer(self):
        # Get the user's order count & coupon counter
        self.db.cursor.execute('''
        SELECT COUNT(*), coupon_counter FROM orders
        JOIN users ON orders.user_id = users.user_id
        WHERE orders.user_id = ? AND orders.order_status = 'done'
        ''', (self.user.current_user["user_id"],))

        order_count, coupon_counter = self.db.cursor.fetchone()

        # Define the threshold for coupon generation
        coupon_threshold = 2

        if coupon_counter + 1 >= coupon_threshold:  # If threshold is met, generate coupon
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            valid_until = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            discount_percentage = min(15, 5 + (order_count * 2))  # Max 15%

            # Insert the new coupon into the database
            self.db.cursor.execute('''
            INSERT INTO coupons (code, discount_percentage, valid_until, is_used, user_id)
            VALUES (?, ?, ?, ?, ?)
            ''', (code, discount_percentage, valid_until, 0, self.user.current_user["user_id"]))

            # Reset coupon_counter to 0 after issuing a coupon
            self.db.cursor.execute('''
            UPDATE users SET coupon_counter = 0 WHERE user_id = ?
            ''', (self.user.current_user["user_id"],))

            print(f"\n Congrats! You've earned a {discount_percentage}% discount coupon!")
            print(f" Coupon Code: {code} (Valid Until: {valid_until})")

        else:
            # Increment coupon_counter if no coupon is issued
            self.db.cursor.execute('''
            UPDATE users SET coupon_counter = coupon_counter + 1 WHERE user_id = ?
            ''', (self.user.current_user["user_id"],))

        self.db.conn.commit()


    def view_orders(self, status=None):
        if not self.user.current_user:
            print("Please login first.")
            return

        query = '''
        SELECT o.order_id, o.order_date, o.total_amount, o.payment_status, o.payment_method, o.order_status
        FROM orders o
        WHERE o.user_id = ?
        '''

        params = [self.user.current_user["user_id"]]

        if status:
            query += " AND o.order_status = ?"
            params.append(status)

        query += " ORDER BY o.order_date DESC"

        self.db.cursor.execute(query, params)
        orders = self.db.cursor.fetchall()

        if not orders:
            print(f"No {'pending' if status == 'pending' else ''} orders found.")
            return

        print(f"\n===== YOUR {'PENDING' if status == 'pending' else ''} ORDERS =====")
        headers = ["Order ID", "Date", "Total Amount", "Payment Status", "Payment Method", "Order Status"]
        print(tabulate(orders, headers=headers, tablefmt="grid"))

        return orders

    def view_order_details(self):
        if not self.user.current_user:
            print("Please login first.")
            return

        orders = self.view_orders()
        if not orders:
            return

        order_id = input("\nEnter Order ID to view details (or 0 to cancel): ")
        if order_id == "0":
            return

        # Check if order belongs to the user
        self.db.cursor.execute('''
        SELECT o.order_id FROM orders o
        WHERE o.order_id = ? AND o.user_id = ?
        ''', (order_id, self.user.current_user["user_id"]))

        if not self.db.cursor.fetchone():
            print("Order not found or doesn't belong to you.")
            return

        # Get order items
        self.db.cursor.execute('''
        SELECT p.name, oi.quantity, oi.price, (oi.price * oi.quantity) as item_total
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
        ''', (order_id,))

        items = self.db.cursor.fetchall()

        print(f"\n===== ORDER #{order_id} DETAILS =====")
        headers = ["Product", "Quantity", "Price", "Total"]
        print(tabulate(items, headers=headers, tablefmt="grid"))

        # Get order summary
        self.db.cursor.execute('''
        SELECT o.order_date, o.total_amount, o.payment_status, o.payment_method, o.order_status
        FROM orders o
        WHERE o.order_id = ?
        ''', (order_id,))

        order = self.db.cursor.fetchone()

        # print("\n===== ORDER SUMMARY =====")
        # print(f"Order Date: {order[0]}")
        # print(f"Payment Method: {order[3]}")
        # print(f"Payment Status: {order[1]}")
        # print(f"Order Status: {order[4]}")
        # print(f"Total Amount: ${order[1]:.2f}")
        print("\n===== ORDER SUMMARY =====")
        print(f"Order Date: {order[0]}")
        print(f"Payment Method: {order[3]}")
        print(f"Payment Status: {order[2]}")
        print(f"Order Status: {order[4]}")
        print(f"Total Amount: ${order[1]:.2f}")

    def view_all_orders(self):
        query = '''
        SELECT o.order_id, o.order_date, o.total_amount, o.payment_status, o.payment_method, o.order_status, u.user_id, u.email
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        ORDER BY o.order_date DESC
        '''

        self.db.cursor.execute(query)
        orders = self.db.cursor.fetchall()

        if not orders:
            print("No orders found.")
            return

        print("\n===== ALL ORDERS =====")
        headers = ["Order ID", "Date", "Total Amount", "Payment Status", "Payment Method", "Order Status", "User ID", "Email"]
        print(tabulate(orders, headers=headers, tablefmt="grid"))



class Coupon:

    def __init__(self, db, user):
        self.db = db
        self.user = user

    def view_coupons(self):
        if not self.user.current_user:
            print("Please login first.")
            return

        self.db.cursor.execute('''
        SELECT coupon_id, code, discount_percentage, valid_until, is_used
        FROM coupons
        WHERE user_id = ?
        ORDER BY valid_until DESC
        ''', (self.user.current_user["user_id"],))

        coupons = self.db.cursor.fetchall()

        if not coupons:
            print("You don't have any coupons.")
            return

        print("\n===== YOUR COUPONS =====")
        headers = ["ID", "Code", "Discount %", "Valid Until", "Used"]

        # Convert is_used from 0/1 to No/Yes
        formatted_coupons = []
        for coupon in coupons:
            formatted_coupon = list(coupon)
            formatted_coupon[4] = "Yes" if coupon[4] == 1 else "No"
            formatted_coupons.append(formatted_coupon)

        print(tabulate(formatted_coupons, headers=headers, tablefmt="grid"))
    def apply_coupon(self, user_id):
        if not self.user.current_user:
            print("Please login first.")
            return "Please login first."

        coupon_code = input("Enter your coupon code: ")

        self.db.cursor.execute('''
        SELECT coupon_id, discount_percentage, valid_until, is_used
        FROM coupons
        WHERE user_id = ? AND code = ?
        ''', (user_id, coupon_code))

        coupon = self.db.cursor.fetchone()


class DollmartApp:

    def __init__(self):
        self.db = Database()
        self.user = User(self.db)
        self.product = Product(self.db)
        self.cart = Cart(self.db, self.user)
        self.order = Order(self.db, self.user, self.cart)
        self.coupon = Coupon(self.db, self.user)

    def display_main_menu(self):
        print("\n===== DOLLMART E-MARKET =====")
        print("1. Login")
        print("2. Register")
        print("3. Exit")

        choice = input("Enter choice (1-3): ")

        if choice == "1":
            if self.user.login():
                if self.user.current_user["user_type"] == "manager":
                    self.manager_menu()
                else:
                    self.customer_menu()
        elif choice == "2":
            self.user.register()
        elif choice == "3":
            print("Thank you for using Dollmart E-Market.")
            self.db.close()
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

    def customer_menu(self):
        while self.user.current_user:
            print(f"\n===== CUSTOMER MENU ({self.user.current_user['first_name']}) =====")
            print("1. Browse Products")
            print("2. Search Products")
            print("3. View Cart")
            print("4. Add to Cart")
            print("5. Update Cart Item")
            print("6. Clear Cart")
            print("7. Place Order")
            print("8. View Orders")
            print("9. View Order Details")
            print("10. View Coupons")
            print("11. Update User Type")
            print("12. Logout")

            choice = input("Enter choice (1-12): ")

            if choice == "1":
                self.product.list_products()
            elif choice == "2":
                self.product.search_products()
            elif choice == "3":
                self.cart.view_cart()
            elif choice == "4":
                products = self.product.list_products()
                if products:
                    product_id = input("\nEnter product ID to add to cart (or 0 to cancel): ")
                    if product_id != "0":
                        quantity = int(input("Enter quantity: "))
                        self.cart.add_to_cart(product_id, quantity)
            elif choice == "5":
                self.cart.update_cart_item()
            elif choice == "6":
                self.cart.clear_cart()
            elif choice == "7":
                self.order.place_order()
            elif choice == "8":
                print("1. All Orders")
                print("2. Pending Orders")
                print("3. Completed Orders")
                order_choice = input("Enter choice (1-3): ")

                if order_choice == "1":
                    self.order.view_orders()
                elif order_choice == "2":
                    self.order.view_orders("pending")
                elif order_choice == "3":
                    self.order.view_orders("done")
                else:
                    print("Invalid choice.")
            elif choice == "9":
                self.order.view_order_details()
            elif choice == "10":
                self.coupon.view_coupons()
            elif choice == "11":
                self.user.update_user_type()
            elif choice == "12":
                self.user.logout()
                break
            else:
                print("Invalid choice. Please try again.")

    def manager_menu(self):
        while self.user.current_user:
            print(f"\n===== MANAGER MENU ({self.user.current_user['first_name']}) =====")
            print("1. Add Product")
            print("2. View All Products")
            print("3. Update Product Details")
            print("4. View All Orders")
            print("5. View All Customers")
            print("6. Logout")

            choice = input("Enter choice (1-5): ")

            if choice == "1":
                self.product.add_product()
            elif choice == "2":
                self.product.list_products()
            elif choice == "3":
                self.product.update_product()
            elif choice == "4":
                self.order.view_all_orders()
            elif choice == "5":
                self.user.view_all_customers()
            elif choice == "6":
                self.user.logout()
                break
            else:
                print("Invalid choice. Please try again.")

    def run(self):
        print("Welcome to Dollmart E-Market!")

        while True:
            self.display_main_menu()

if __name__ == "__main__":
    app = DollmartApp()
    app.run()