CREATE DATABASE IF NOT EXISTS restaurant_db;
USE restaurant_db;

DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS bills;
DROP TABLE IF EXISTS discounts;
DROP TABLE IF EXISTS kitchen_tickets;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS food_orders;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS menu_items;
DROP TABLE IF EXISTS waiters;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS restaurant_tables;
DROP TABLE IF EXISTS dining_areas;

CREATE TABLE dining_areas (
    area_id INT AUTO_INCREMENT PRIMARY KEY,
    area_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE restaurant_tables (
    table_id INT AUTO_INCREMENT PRIMARY KEY,
    table_number VARCHAR(20) NOT NULL UNIQUE,
    capacity INT NOT NULL CHECK (capacity > 0),
    status VARCHAR(20) DEFAULT 'available',
    area_id INT NOT NULL,
    CONSTRAINT fk_tables_area FOREIGN KEY (area_id) REFERENCES dining_areas(area_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_table_area (area_id)
);

CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(30),
    email VARCHAR(100)
);

CREATE TABLE waiters (
    waiter_id INT AUTO_INCREMENT PRIMARY KEY,
    waiter_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(30),
    status VARCHAR(30) DEFAULT 'available'
);

CREATE TABLE menu_items (
    menu_item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    availability BOOLEAN DEFAULT TRUE,
    INDEX idx_menu_category (category)
);

CREATE TABLE reservations (
    reservation_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    table_id INT NOT NULL,
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    guest_count INT NOT NULL CHECK (guest_count > 0),
    status VARCHAR(30) NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reservation_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_reservation_table FOREIGN KEY (table_id) REFERENCES restaurant_tables(table_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_reservation_date (reservation_date),
    INDEX idx_reservation_table_time (table_id, reservation_date, reservation_time)
);

CREATE TABLE food_orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    table_id INT,
    waiter_id INT,
    order_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_order_table FOREIGN KEY (table_id) REFERENCES restaurant_tables(table_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_order_waiter FOREIGN KEY (waiter_id) REFERENCES waiters(waiter_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_order_customer (customer_id),
    INDEX idx_order_datetime (order_datetime)
);

CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    menu_item_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES food_orders(order_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_order_item_menu FOREIGN KEY (menu_item_id) REFERENCES menu_items(menu_item_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_order_items_order (order_id),
    INDEX idx_order_items_menu (menu_item_id)
);

CREATE TABLE kitchen_tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    ticket_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_ticket_order FOREIGN KEY (order_id) REFERENCES food_orders(order_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_ticket_status (ticket_status)
);

CREATE TABLE discounts (
    discount_id INT AUTO_INCREMENT PRIMARY KEY,
    discount_name VARCHAR(100) NOT NULL,
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
    discount_value DECIMAL(10,2) NOT NULL CHECK (discount_value >= 0),
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    discount_id INT,
    subtotal DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bill_order FOREIGN KEY (order_id) REFERENCES food_orders(order_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_bill_discount FOREIGN KEY (discount_id) REFERENCES discounts(discount_id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_amount DECIMAL(10,2) NOT NULL CHECK (payment_amount >= 0),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_payment_bill FOREIGN KEY (bill_id) REFERENCES bills(bill_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_payments_bill (bill_id),
    INDEX idx_payments_date (payment_date)
);

CREATE INDEX idx_customer_name ON customers(customer_name);
