# 🛒 Dollmart E-Market CLI

A command-line e-commerce platform built with **Python** and **SQLite**, supporting user registration, authentication, product management, cart and order processing, coupon generation, and role-based access for **customers, bulk buyers, and managers**.

---

## 🚀 Features

- **User Registration & Login**  
  Secure registration and authentication with SHA-256 password hashing.  

- **Role-Based Access**  
  Supports individual customers, bulk buyers, and a manager role with different privileges.  

- **Product & Category Management**  
  Add, update, and view products and categories.  

- **Cart System**  
  Add, update, and clear items in a shopping cart.  

- **Order Processing**  
  Place orders, view order history, and order details.  

- **Coupon System**  
  Automatic coupon generation for regular customers and coupon application at checkout.  

- **Admin Tools**  
  Manager can view all customers, products, and orders.  

- **Tabular Data Display**  
  Uses `tabulate` for clear, formatted output.  

---

## 🛠️ Technologies Used

- Python 3  
- SQLite (`sqlite3`)  
- OOP (Object-Oriented Programming)  
- [tabulate](https://pypi.org/project/tabulate/) for table formatting  

---

## 📦 Getting Started

### ✅ Prerequisites
- Python 3.x installed  
- Install dependencies:
```bash
pip install tabulate
```

### ▶️ Running the Application

Clone the repository and run:

python Q3_cli_final.py

📌 Usage
   On startup, register as a new user or login.

  Customers can:

        Browse/search products

        Manage their cart

        Place orders

        Use/view coupons

  Managers can:

        Add/update products

        View all orders

        See all customers

