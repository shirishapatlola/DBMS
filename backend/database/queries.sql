-- Summary metrics
SELECT COUNT(*) AS total_customers FROM customers;
SELECT COUNT(*) AS total_tables FROM restaurant_tables;
SELECT COUNT(*) AS total_reservations FROM reservations;
SELECT COUNT(*) AS total_orders FROM food_orders;
SELECT COUNT(*) AS total_menu_items FROM menu_items;
SELECT COALESCE(SUM(total_amount), 0) AS total_sales FROM bills;
SELECT COUNT(*) AS pending_kitchen_orders FROM kitchen_tickets WHERE ticket_status IN ('pending', 'preparing');

-- Restaurant table join example
SELECT t.table_id, t.table_number, t.capacity, a.area_name
FROM restaurant_tables t
INNER JOIN dining_areas a ON a.area_id = t.area_id;

-- Reservation joins
SELECT r.reservation_id, c.customer_name, t.table_number, r.reservation_date, r.reservation_time, r.guest_count
FROM reservations r
INNER JOIN customers c ON c.customer_id = r.customer_id
INNER JOIN restaurant_tables t ON t.table_id = r.table_id;

-- Order total by customer
SELECT o.order_id, c.customer_name, o.total_amount, o.status
FROM food_orders o
INNER JOIN customers c ON c.customer_id = o.customer_id;

-- Popular menu item
SELECT m.item_name, SUM(oi.quantity) AS total_quantity
FROM order_items oi
INNER JOIN menu_items m ON m.menu_item_id = oi.menu_item_id
GROUP BY m.item_name
ORDER BY total_quantity DESC
LIMIT 5;

-- Monthly revenue
SELECT DATE_FORMAT(order_datetime, '%Y-%m') AS month, SUM(total_amount) AS revenue
FROM food_orders
GROUP BY DATE_FORMAT(order_datetime, '%Y-%m')
ORDER BY month;

-- Outstanding bill amounts
SELECT b.bill_id, ROUND(b.total_amount - COALESCE(SUM(p.payment_amount),0), 2) AS outstanding
FROM bills b
LEFT JOIN payments p ON p.bill_id = b.bill_id
GROUP BY b.bill_id, b.total_amount;

-- Customer history
SELECT c.customer_name, COUNT(o.order_id) AS order_count, SUM(o.total_amount) AS total_spent
FROM customers c
LEFT JOIN food_orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_name
ORDER BY total_spent DESC;
