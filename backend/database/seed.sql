USE restaurant_db;

INSERT INTO dining_areas (area_name) VALUES
('Main Hall'),
('Garden Terrace'),
('Private Dining');

INSERT INTO restaurant_tables (table_number, capacity, status, area_id) VALUES
('A-01', 2, 'available', 1),
('A-02', 4, 'available', 1),
('A-03', 6, 'occupied', 1),
('A-04', 2, 'available', 1),
('B-01', 4, 'available', 2),
('B-02', 4, 'reserved', 2),
('B-03', 8, 'available', 2),
('C-01', 6, 'available', 3),
('C-02', 4, 'occupied', 3);

INSERT INTO customers (customer_name, phone_number, email) VALUES
('Aisha Khan', '555-1001', 'aisha@example.com'),
('Rahul Sharma', '555-1002', 'rahul@example.com'),
('Maria Lopez', '555-1003', 'maria@example.com'),
('Daniel Brown', '555-1004', 'daniel@example.com'),
('Priya Nair', '555-1005', 'priya@example.com'),
('Samuel Lee', '555-1006', 'samuel@example.com'),
('Nina Patel', '555-1007', 'nina@example.com'),
('Omar Hassan', '555-1008', 'omar@example.com'),
('Sofia Meyer', '555-1009', 'sofia@example.com'),
('Arjun Singh', '555-1010', 'arjun@example.com');

INSERT INTO waiters (waiter_name, phone_number, status) VALUES
('Alice Gomez', '555-2001', 'available'),
('Dev Patel', '555-2002', 'busy'),
('Liam Chen', '555-2003', 'available');

INSERT INTO menu_items (item_name, category, price, availability) VALUES
('Classic Burger', 'Main Course', 180.00, TRUE),
('Grilled Chicken Pasta', 'Main Course', 220.00, TRUE),
('Margherita Pizza', 'Pizza', 250.00, TRUE),
('Veggie Supreme Pizza', 'Pizza', 280.00, TRUE),
('Chicken Caesar Salad', 'Starter', 160.00, TRUE),
('Tomato Basil Soup', 'Starter', 120.00, TRUE),
('French Fries', 'Side', 90.00, TRUE),
('Mint Lemonade', 'Beverage', 70.00, TRUE),
('Cappuccino', 'Beverage', 110.00, TRUE),
('Chocolate Brownie', 'Dessert', 130.00, TRUE),
('Cheese Sandwich', 'Main Course', 150.00, TRUE),
('Cold Coffee', 'Beverage', 100.00, TRUE);

INSERT INTO reservations (customer_id, table_id, reservation_date, reservation_time, guest_count, status) VALUES
(1, 1, '2026-10-14', '19:00:00', 2, 'confirmed'),
(2, 2, '2026-10-14', '19:30:00', 4, 'confirmed'),
(3, 5, '2026-10-15', '20:00:00', 4, 'pending'),
(4, 6, '2026-10-15', '18:30:00', 4, 'confirmed'),
(5, 8, '2026-10-16', '21:00:00', 6, 'confirmed'),
(6, 3, '2026-10-17', '19:15:00', 6, 'confirmed'),
(7, 9, '2026-10-17', '20:30:00', 4, 'cancelled'),
(8, 4, '2026-10-18', '18:00:00', 2, 'confirmed');

INSERT INTO food_orders (customer_id, table_id, waiter_id, order_datetime, status, total_amount) VALUES
(1, 1, 1, '2026-10-12 19:05:00', 'served', 370.00),
(2, 2, 2, '2026-10-12 19:45:00', 'preparing', 520.00),
(3, 5, 1, '2026-10-13 20:15:00', 'pending', 460.00),
(4, 6, 3, '2026-10-13 18:45:00', 'served', 310.00),
(5, 8, 2, '2026-10-14 21:10:00', 'ready', 615.00),
(6, 3, 1, '2026-10-14 19:20:00', 'preparing', 430.00),
(7, 9, 3, '2026-10-15 20:40:00', 'cancelled', 0.00),
(8, 4, 2, '2026-10-15 18:10:00', 'served', 290.00),
(9, NULL, 1, '2026-10-16 12:30:00', 'paid', 220.00),
(10, NULL, 3, '2026-10-16 13:00:00', 'pending', 245.00);

INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, subtotal) VALUES
(1, 1, 1, 180.00, 180.00),
(1, 8, 2, 70.00, 140.00),
(1, 10, 1, 130.00, 130.00),
(2, 3, 1, 250.00, 250.00),
(2, 5, 1, 160.00, 160.00),
(2, 9, 2, 110.00, 220.00),
(3, 2, 1, 220.00, 220.00),
(3, 6, 1, 120.00, 120.00),
(3, 7, 2, 90.00, 180.00),
(4, 11, 2, 150.00, 300.00),
(4, 8, 1, 70.00, 70.00),
(5, 3, 2, 250.00, 500.00),
(5, 12, 1, 100.00, 100.00),
(5, 10, 1, 130.00, 130.00),
(6, 1, 1, 180.00, 180.00),
(6, 7, 2, 90.00, 180.00),
(6, 9, 1, 110.00, 110.00),
(8, 4, 1, 280.00, 280.00),
(8, 12, 1, 100.00, 100.00),
(9, 6, 1, 120.00, 120.00),
(9, 8, 1, 70.00, 70.00),
(10, 3, 1, 250.00, 250.00),
(10, 10, 1, 130.00, 130.00);

INSERT INTO kitchen_tickets (order_id, ticket_status) VALUES
(1, 'served'),
(2, 'preparing'),
(3, 'pending'),
(4, 'served'),
(5, 'ready'),
(6, 'preparing');

INSERT INTO discounts (discount_name, discount_type, discount_value, active) VALUES
('Lunch Offer', 'percentage', 10.00, TRUE),
('Birthday Special', 'fixed', 50.00, TRUE),
('Early Dinner', 'percentage', 5.00, TRUE),
('VIP Guest', 'fixed', 25.00, FALSE);

INSERT INTO bills (order_id, discount_id, subtotal, discount_amount, tax_amount, total_amount, payment_status) VALUES
(1, 1, 370.00, 37.00, 29.60, 362.60, 'paid'),
(2, 2, 520.00, 50.00, 41.60, 511.60, 'partially_paid'),
(3, NULL, 460.00, 0.00, 36.80, 496.80, 'pending'),
(4, 3, 310.00, 15.50, 24.80, 319.30, 'paid'),
(5, 1, 615.00, 61.50, 49.20, 602.70, 'pending'),
(6, NULL, 430.00, 0.00, 34.40, 464.40, 'pending'),
(8, NULL, 290.00, 0.00, 23.20, 313.20, 'paid'),
(9, 2, 220.00, 50.00, 17.60, 187.60, 'paid');

INSERT INTO payments (bill_id, payment_method, payment_amount, payment_status) VALUES
(1, 'card', 362.60, 'paid'),
(2, 'cash', 200.00, 'partially_paid'),
(2, 'upi', 250.00, 'paid'),
(4, 'card', 319.30, 'paid'),
(8, 'cash', 313.20, 'paid'),
(9, 'upi', 187.60, 'paid');
