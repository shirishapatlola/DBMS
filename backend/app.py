import os
from decimal import Decimal, InvalidOperation

from flask import Flask, flash, redirect, render_template, request, url_for

from db import fetch_all, fetch_one, get_connection

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

ALLOWED_TABLES = [
    "dining_areas",
    "restaurant_tables",
    "customers",
    "waiters",
    "menu_items",
    "reservations",
    "food_orders",
    "order_items",
    "kitchen_tickets",
    "bills",
    "discounts",
    "payments",
]


def money(value):
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, TypeError, ValueError):
        return 0.0


def get_dashboard_data():
    metrics = {
        "customers": fetch_one("SELECT COUNT(*) AS total FROM customers")["total"],
        "tables": fetch_one("SELECT COUNT(*) AS total FROM restaurant_tables")["total"],
        "reservations": fetch_one("SELECT COUNT(*) AS total FROM reservations")["total"],
        "orders": fetch_one("SELECT COUNT(*) AS total FROM food_orders")["total"],
        "menu_items": fetch_one("SELECT COUNT(*) AS total FROM menu_items")["total"],
        "sales": fetch_one("SELECT COALESCE(SUM(total_amount), 0) AS total FROM bills")["total"],
        "pending_kitchen": fetch_one(
            "SELECT COUNT(*) AS total FROM kitchen_tickets WHERE ticket_status IN ('pending', 'preparing')"
        )["total"],
    }
    return metrics


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/")
def index():
    try:
        metrics = get_dashboard_data()
    except Exception:
        metrics = {
            "customers": 0,
            "tables": 0,
            "reservations": 0,
            "orders": 0,
            "menu_items": 0,
            "sales": 0,
            "pending_kitchen": 0,
        }
    return render_template("index.html", metrics=metrics)


@app.route("/dining-areas", methods=["GET", "POST"])
def dining_areas():
    if request.method == "POST":
        area_name = (request.form.get("area_name") or "").strip()
        if not area_name:
            flash("Area name is required.", "danger")
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO dining_areas (area_name) VALUES (%s)",
                    (area_name,),
                )
                conn.commit()
                flash("Dining area added successfully.", "success")
            except Exception as exc:
                flash(f"Could not add dining area: {exc}", "danger")
            finally:
                conn.close()
        return redirect(url_for("dining_areas"))

    rows = fetch_all(
        "SELECT area_id, area_name FROM dining_areas ORDER BY area_name"
    )
    return render_template("dining_areas.html", rows=rows)


@app.route("/tables", methods=["GET", "POST"])
def tables():
    if request.method == "POST":
        table_number = (request.form.get("table_number") or "").strip()
        capacity = request.form.get("capacity")
        status = request.form.get("status") or "available"
        area_id = request.form.get("area_id")
        if not table_number or not capacity or not area_id:
            flash("Table number, capacity and area are required.", "danger")
            return redirect(url_for("tables"))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO restaurant_tables (table_number, capacity, status, area_id) VALUES (%s, %s, %s, %s)",
                (table_number, int(capacity), status, int(area_id)),
            )
            conn.commit()
            flash("Table added successfully.", "success")
        except Exception as exc:
            flash(f"Could not add table: {exc}", "danger")
        finally:
            conn.close()
        return redirect(url_for("tables"))

    rows = fetch_all(
        "SELECT t.table_id, t.table_number, t.capacity, t.status, a.area_name FROM restaurant_tables t LEFT JOIN dining_areas a ON a.area_id = t.area_id ORDER BY t.table_number"
    )
    areas = fetch_all("SELECT area_id, area_name FROM dining_areas ORDER BY area_name")
    return render_template("tables.html", rows=rows, areas=areas)


@app.route("/customers", methods=["GET", "POST"])
def customers():
    if request.method == "POST":
        customer_name = (request.form.get("customer_name") or "").strip()
        phone_number = (request.form.get("phone_number") or "").strip()
        email = (request.form.get("email") or "").strip()
        if not customer_name:
            flash("Customer name is required.", "danger")
            return redirect(url_for("customers"))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers (customer_name, phone_number, email) VALUES (%s, %s, %s)",
                (customer_name, phone_number, email),
            )
            conn.commit()
            flash("Customer added successfully.", "success")
        except Exception as exc:
            flash(f"Could not add customer: {exc}", "danger")
        finally:
            conn.close()
        return redirect(url_for("customers"))

    rows = fetch_all(
        "SELECT customer_id, customer_name, phone_number, email FROM customers ORDER BY customer_name"
    )
    return render_template("customers.html", rows=rows)


@app.route("/customers/search")
def customer_search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return redirect(url_for("customers"))

    rows = fetch_all(
        "SELECT customer_id, customer_name, phone_number, email FROM customers WHERE customer_name LIKE %s OR phone_number LIKE %s ORDER BY customer_name",
        (f"%{query}%", f"%{query}%"),
    )
    return render_template("customers.html", rows=rows, search_query=query)


@app.route("/reservations", methods=["GET", "POST"])
def reservations():
    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        table_id = request.form.get("table_id")
        reservation_date = request.form.get("reservation_date")
        reservation_time = request.form.get("reservation_time")
        guest_count = request.form.get("guest_count")
        status = request.form.get("status") or "confirmed"

        if not all([customer_id, table_id, reservation_date, reservation_time, guest_count]):
            flash("All reservation fields are required.", "danger")
            return redirect(url_for("reservations"))

        table = fetch_one(
            "SELECT table_id, table_number, capacity FROM restaurant_tables WHERE table_id = %s",
            (int(table_id),),
        )
        if not table:
            flash("Selected table does not exist.", "danger")
            return redirect(url_for("reservations"))

        if int(guest_count) > table["capacity"]:
            flash("Guest count exceeds table capacity.", "danger")
            return redirect(url_for("reservations"))

        conflict = fetch_one(
            "SELECT reservation_id FROM reservations WHERE table_id = %s AND reservation_date = %s AND reservation_time = %s AND status != 'cancelled'",
            (int(table_id), reservation_date, reservation_time),
        )
        if conflict:
            flash("This table is already reserved at the same date and time.", "danger")
            return redirect(url_for("reservations"))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reservations (customer_id, table_id, reservation_date, reservation_time, guest_count, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (int(customer_id), int(table_id), reservation_date, reservation_time, int(guest_count), status),
            )
            conn.commit()
            flash("Reservation created successfully.", "success")
        except Exception as exc:
            flash(f"Could not create reservation: {exc}", "danger")
        finally:
            conn.close()
        return redirect(url_for("reservations"))

    rows = fetch_all(
        "SELECT r.reservation_id, c.customer_name, t.table_number, r.reservation_date, r.reservation_time, r.guest_count, r.status FROM reservations r INNER JOIN customers c ON c.customer_id = r.customer_id INNER JOIN restaurant_tables t ON t.table_id = r.table_id ORDER BY r.reservation_date DESC, r.reservation_time DESC"
    )
    customers_list = fetch_all("SELECT customer_id, customer_name FROM customers ORDER BY customer_name")
    tables_list = fetch_all("SELECT table_id, table_number, capacity FROM restaurant_tables ORDER BY table_number")
    return render_template("reservations.html", rows=rows, customers_list=customers_list, tables_list=tables_list)


@app.route("/menu", methods=["GET", "POST"])
def menu():
    if request.method == "POST":
        item_name = (request.form.get("item_name") or "").strip()
        category = (request.form.get("category") or "").strip()
        price = request.form.get("price")
        availability = request.form.get("availability") == "1"
        if not item_name or not price:
            flash("Item name and price are required.", "danger")
            return redirect(url_for("menu"))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO menu_items (item_name, category, price, availability) VALUES (%s, %s, %s, %s)",
                (item_name, category, Decimal(str(price)), availability),
            )
            conn.commit()
            flash("Menu item added successfully.", "success")
        except Exception as exc:
            flash(f"Could not add menu item: {exc}", "danger")
        finally:
            conn.close()
        return redirect(url_for("menu"))

    rows = fetch_all(
        "SELECT menu_item_id, item_name, category, price, availability FROM menu_items ORDER BY category, item_name"
    )
    return render_template("menu.html", rows=rows)


@app.route("/orders", methods=["GET", "POST"])
def orders():
    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        table_id = request.form.get("table_id") or None
        waiter_id = request.form.get("waiter_id") or None
        item_ids = request.form.getlist("item_id")
        quantities = request.form.getlist("quantity")

        if not customer_id or not item_ids:
            flash("Customer and at least one menu item are required.", "danger")
            return redirect(url_for("orders"))

        valid_items = []
        for idx, item_id in enumerate(item_ids):
            if not item_id:
                continue
            quantity = int(quantities[idx]) if idx < len(quantities) and quantities[idx] else 0
            if quantity <= 0:
                continue
            item = fetch_one(
                "SELECT menu_item_id, item_name, price FROM menu_items WHERE menu_item_id = %s AND availability = TRUE",
                (int(item_id),),
            )
            if item:
                valid_items.append({"item": item, "quantity": quantity})

        if not valid_items:
            flash("No valid order items were selected.", "danger")
            return redirect(url_for("orders"))

        total_amount = sum(Decimal(str(item["item"]["price"])) * item["quantity"] for item in valid_items)

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO food_orders (customer_id, table_id, waiter_id, status, total_amount) VALUES (%s, %s, %s, 'pending', %s)",
                (int(customer_id), int(table_id) if table_id else None, int(waiter_id) if waiter_id else None, Decimal(str(total_amount))),
            )
            order_id = cursor.lastrowid
            for entry in valid_items:
                item = entry["item"]
                subtotal = Decimal(str(item["price"])) * entry["quantity"]
                cursor.execute(
                    "INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (order_id, item["menu_item_id"], entry["quantity"], Decimal(str(item["price"])), subtotal),
                )
            cursor.execute(
                "INSERT INTO kitchen_tickets (order_id, ticket_status) VALUES (%s, 'pending')",
                (order_id,),
            )
            conn.commit()
            flash("Order created successfully.", "success")
            return redirect(url_for("order_detail", order_id=order_id))
        except Exception as exc:
            conn.rollback()
            flash(f"Could not create order: {exc}", "danger")
            return redirect(url_for("orders"))
        finally:
            conn.close()

    rows = fetch_all(
        "SELECT o.order_id, c.customer_name, t.table_number, w.waiter_name, o.order_datetime, o.status, o.total_amount FROM food_orders o LEFT JOIN customers c ON c.customer_id = o.customer_id LEFT JOIN restaurant_tables t ON t.table_id = o.table_id LEFT JOIN waiters w ON w.waiter_id = o.waiter_id ORDER BY o.order_datetime DESC"
    )
    customers_list = fetch_all("SELECT customer_id, customer_name FROM customers ORDER BY customer_name")
    tables_list = fetch_all("SELECT table_id, table_number FROM restaurant_tables ORDER BY table_number")
    waiters_list = fetch_all("SELECT waiter_id, waiter_name FROM waiters ORDER BY waiter_name")
    menu_items = fetch_all("SELECT menu_item_id, item_name, category, price FROM menu_items WHERE availability = TRUE ORDER BY category, item_name")
    return render_template("orders.html", rows=rows, customers_list=customers_list, tables_list=tables_list, waiters_list=waiters_list, menu_items=menu_items)


@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    order = fetch_one(
        "SELECT o.order_id, c.customer_name, t.table_number, w.waiter_name, o.order_datetime, o.status, o.total_amount FROM food_orders o LEFT JOIN customers c ON c.customer_id = o.customer_id LEFT JOIN restaurant_tables t ON t.table_id = o.table_id LEFT JOIN waiters w ON w.waiter_id = o.waiter_id WHERE o.order_id = %s",
        (order_id,),
    )
    items = fetch_all(
        "SELECT oi.order_item_id, mi.item_name, oi.quantity, oi.unit_price, oi.subtotal FROM order_items oi INNER JOIN menu_items mi ON mi.menu_item_id = oi.menu_item_id WHERE oi.order_id = %s ORDER BY oi.order_item_id",
        (order_id,),
    )
    return render_template("order_detail.html", order=order, items=items)


@app.route("/kitchen", methods=["GET", "POST"])
def kitchen():
    if request.method == "POST":
        ticket_id = request.form.get("ticket_id")
        ticket_status = request.form.get("ticket_status")
        if ticket_id and ticket_status:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE kitchen_tickets SET ticket_status = %s, updated_at = CURRENT_TIMESTAMP WHERE ticket_id = %s",
                    (ticket_status, int(ticket_id)),
                )
                conn.commit()
                flash("Kitchen ticket updated.", "success")
            except Exception as exc:
                flash(f"Could not update kitchen ticket: {exc}", "danger")
            finally:
                conn.close()
        return redirect(url_for("kitchen"))

    rows = fetch_all(
        "SELECT k.ticket_id, o.order_id, c.customer_name, k.ticket_status, k.created_at, k.updated_at FROM kitchen_tickets k INNER JOIN food_orders o ON o.order_id = k.order_id INNER JOIN customers c ON c.customer_id = o.customer_id ORDER BY k.updated_at DESC"
    )
    return render_template("kitchen.html", rows=rows)


@app.route("/bills", methods=["GET", "POST"])
def bills():
    if request.method == "POST":
        order_id = request.form.get("order_id")
        discount_id = request.form.get("discount_id") or None
        if not order_id:
            flash("Order reference is required.", "danger")
            return redirect(url_for("bills"))

        order = fetch_one("SELECT order_id, total_amount FROM food_orders WHERE order_id = %s", (int(order_id),))
        if not order:
            flash("Order not found.", "danger")
            return redirect(url_for("bills"))

        subtotal = Decimal(str(order["total_amount"]))
        discount_amount = Decimal("0")
        if discount_id:
            discount = fetch_one("SELECT discount_id, discount_type, discount_value FROM discounts WHERE discount_id = %s AND active = TRUE", (int(discount_id),))
            if discount:
                if discount["discount_type"] == "percentage":
                    discount_amount = (subtotal * Decimal(str(discount["discount_value"])) / Decimal("100"))
                else:
                    discount_amount = Decimal(str(discount["discount_value"]))
        tax_amount = subtotal * Decimal("0.10")
        total_amount = subtotal - discount_amount + tax_amount
        if total_amount < 0:
            flash("Final total cannot be negative.", "danger")
            return redirect(url_for("bills"))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO bills (order_id, discount_id, subtotal, discount_amount, tax_amount, total_amount, payment_status) VALUES (%s, %s, %s, %s, %s, %s, 'pending')",
                (int(order_id), int(discount_id) if discount_id else None, subtotal, discount_amount, tax_amount, total_amount),
            )
            conn.commit()
            flash("Bill generated successfully.", "success")
        except Exception as exc:
            flash(f"Could not generate bill: {exc}", "danger")
        finally:
            conn.close()
        return redirect(url_for("bills"))

    rows = fetch_all(
        "SELECT b.bill_id, o.order_id, c.customer_name, b.subtotal, b.discount_amount, b.tax_amount, b.total_amount, b.payment_status FROM bills b INNER JOIN food_orders o ON o.order_id = b.order_id INNER JOIN customers c ON c.customer_id = o.customer_id ORDER BY b.generated_at DESC"
    )
    orders_list = fetch_all("SELECT order_id, customer_id, total_amount FROM food_orders ORDER BY order_datetime DESC")
    discounts_list = fetch_all("SELECT discount_id, discount_name, discount_type, discount_value FROM discounts WHERE active = TRUE ORDER BY discount_name")
    return render_template("bills.html", rows=rows, orders_list=orders_list, discounts_list=discounts_list)


@app.route("/payments", methods=["GET", "POST"])
def payments():
    if request.method == "POST":
        bill_id = request.form.get("bill_id")
        payment_method = (request.form.get("payment_method") or "").strip()
        payment_amount = request.form.get("payment_amount")
        if not all([bill_id, payment_method, payment_amount]):
            flash("Bill, payment method and amount are required.", "danger")
            return redirect(url_for("payments"))

        bill = fetch_one("SELECT bill_id, total_amount FROM bills WHERE bill_id = %s", (int(bill_id),))
        total_paid = fetch_one("SELECT COALESCE(SUM(payment_amount), 0) AS total_paid FROM payments WHERE bill_id = %s", (int(bill_id),))
        outstanding = Decimal(str(bill["total_amount"])) - Decimal(str(total_paid["total_paid"]))
        incoming = Decimal(str(payment_amount))
        if incoming > outstanding:
            flash("Payment exceeds outstanding balance.", "danger")
            return redirect(url_for("payments"))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO payments (bill_id, payment_method, payment_amount, payment_status) VALUES (%s, %s, %s, 'paid')",
                (int(bill_id), payment_method, incoming),
            )
            new_total_paid = Decimal(str(total_paid["total_paid"])) + incoming
            if new_total_paid >= Decimal(str(bill["total_amount"])):
                cursor.execute("UPDATE bills SET payment_status = 'paid' WHERE bill_id = %s", (int(bill_id),))
            else:
                cursor.execute("UPDATE bills SET payment_status = 'partially_paid' WHERE bill_id = %s", (int(bill_id),))
            conn.commit()
            flash("Payment recorded successfully.", "success")
        except Exception as exc:
            flash(f"Could not save payment: {exc}", "danger")
        finally:
            conn.close()
        return redirect(url_for("payments"))

    rows = fetch_all(
        "SELECT p.payment_id, b.bill_id, c.customer_name, p.payment_method, p.payment_amount, p.payment_date, p.payment_status FROM payments p INNER JOIN bills b ON b.bill_id = p.bill_id INNER JOIN food_orders o ON o.order_id = b.order_id INNER JOIN customers c ON c.customer_id = o.customer_id ORDER BY p.payment_date DESC"
    )
    bills_list = fetch_all("SELECT b.bill_id, c.customer_name, b.total_amount, b.payment_status FROM bills b INNER JOIN food_orders o ON o.order_id = b.order_id INNER JOIN customers c ON c.customer_id = o.customer_id ORDER BY b.generated_at DESC")
    return render_template("payments.html", rows=rows, bills_list=bills_list)


@app.route("/reports")
def reports():
    queries = {
        "daily_sales": fetch_all("SELECT DATE(o.order_datetime) AS sale_date, SUM(o.total_amount) AS total_sales FROM food_orders o GROUP BY DATE(o.order_datetime) ORDER BY sale_date DESC"),
        "monthly_sales": fetch_all("SELECT DATE_FORMAT(o.order_datetime, '%Y-%m') AS month, SUM(o.total_amount) AS total_sales FROM food_orders o GROUP BY DATE_FORMAT(o.order_datetime, '%Y-%m') ORDER BY month DESC"),
        "popular_items": fetch_all("SELECT m.item_name, SUM(oi.quantity) AS total_quantity FROM order_items oi INNER JOIN menu_items m ON m.menu_item_id = oi.menu_item_id GROUP BY m.menu_item_id, m.item_name ORDER BY total_quantity DESC LIMIT 5"),
        "customer_history": fetch_all("SELECT c.customer_name, COUNT(o.order_id) AS order_count, COALESCE(SUM(o.total_amount), 0) AS total_spent FROM customers c LEFT JOIN food_orders o ON o.customer_id = c.customer_id GROUP BY c.customer_id, c.customer_name ORDER BY total_spent DESC"),
        "pending_kitchen": fetch_all("SELECT k.ticket_id, o.order_id, c.customer_name, k.ticket_status FROM kitchen_tickets k INNER JOIN food_orders o ON o.order_id = k.order_id INNER JOIN customers c ON c.customer_id = o.customer_id WHERE k.ticket_status IN ('pending', 'preparing') ORDER BY k.created_at DESC"),
        "payment_method_revenue": fetch_all("SELECT payment_method, SUM(payment_amount) AS revenue FROM payments GROUP BY payment_method ORDER BY revenue DESC"),
    }
    return render_template("reports.html", queries=queries)


@app.route("/db-explorer")
def db_explorer():
    selected_table = request.args.get("table", "customers")
    if selected_table not in ALLOWED_TABLES:
        selected_table = "customers"

    tables = fetch_all(
        "SELECT TABLE_NAME AS table_name FROM information_schema.tables WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME"
    )
    selected_structure = fetch_all(f"SHOW COLUMNS FROM `{selected_table}`")
    try:
        total_records = fetch_one(f"SELECT COUNT(*) AS total FROM `{selected_table}`")["total"]
        records = fetch_all(f"SELECT * FROM `{selected_table}` ORDER BY 1 LIMIT 25")
    except Exception:
        total_records = 0
        records = []

    relationship_rows = fetch_all(
        "SELECT TABLE_NAME AS table_name, COLUMN_NAME AS column_name, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME FROM information_schema.key_column_usage WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY TABLE_NAME"
    )
    return render_template(
        "db_explorer.html",
        tables=tables,
        selected_table=selected_table,
        selected_structure=selected_structure,
        total_records=total_records,
        records=records,
        relationship_rows=relationship_rows,
    )


@app.route("/sql-demo")
def sql_demo():
    queries = [
        {
            "title": "Show all customers",
            "description": "List all customer records.",
            "sql": "SELECT * FROM customers ORDER BY customer_name;",
            "rows": fetch_all("SELECT * FROM customers ORDER BY customer_name"),
        },
        {
            "title": "Show reservations with customer and table details",
            "description": "Display reservation details with joins to the customers and table tables.",
            "sql": "SELECT r.reservation_id, c.customer_name, t.table_number, r.reservation_date, r.reservation_time, r.guest_count FROM reservations r INNER JOIN customers c ON c.customer_id = r.customer_id INNER JOIN restaurant_tables t ON t.table_id = r.table_id;",
            "rows": fetch_all("SELECT r.reservation_id, c.customer_name, t.table_number, r.reservation_date, r.reservation_time, r.guest_count FROM reservations r INNER JOIN customers c ON c.customer_id = r.customer_id INNER JOIN restaurant_tables t ON t.table_id = r.table_id ORDER BY r.reservation_date DESC"),
        },
        {
            "title": "Show orders with customer names and totals",
            "description": "View all food orders with customer data and total amounts.",
            "sql": "SELECT o.order_id, c.customer_name, o.total_amount, o.status FROM food_orders o INNER JOIN customers c ON c.customer_id = o.customer_id;",
            "rows": fetch_all("SELECT o.order_id, c.customer_name, o.total_amount, o.status FROM food_orders o INNER JOIN customers c ON c.customer_id = o.customer_id ORDER BY o.order_datetime DESC"),
        },
        {
            "title": "Show menu items and categories",
            "description": "List item names, categories, and price values.",
            "sql": "SELECT item_name, category, price FROM menu_items ORDER BY category, item_name;",
            "rows": fetch_all("SELECT item_name, category, price FROM menu_items ORDER BY category, item_name"),
        },
        {
            "title": "Calculate total sales",
            "description": "Summarize the total bill value received by the restaurant.",
            "sql": "SELECT COALESCE(SUM(total_amount), 0) AS total_sales FROM bills;",
            "rows": fetch_all("SELECT COALESCE(SUM(total_amount), 0) AS total_sales FROM bills"),
        },
        {
            "title": "Find the most popular menu item",
            "description": "Use GROUP BY and SUM to see which item appears most often in orders.",
            "sql": "SELECT m.item_name, SUM(oi.quantity) AS total_quantity FROM order_items oi INNER JOIN menu_items m ON m.menu_item_id = oi.menu_item_id GROUP BY m.menu_item_id, m.item_name ORDER BY total_quantity DESC LIMIT 5;",
            "rows": fetch_all("SELECT m.item_name, SUM(oi.quantity) AS total_quantity FROM order_items oi INNER JOIN menu_items m ON m.menu_item_id = oi.menu_item_id GROUP BY m.menu_item_id, m.item_name ORDER BY total_quantity DESC LIMIT 5"),
        },
        {
            "title": "Show pending kitchen tickets",
            "description": "Display current kitchen activity and preparation status.",
            "sql": "SELECT * FROM kitchen_tickets WHERE ticket_status IN ('pending', 'preparing');",
            "rows": fetch_all("SELECT * FROM kitchen_tickets WHERE ticket_status IN ('pending', 'preparing') ORDER BY updated_at DESC"),
        },
        {
            "title": "Monthly revenue",
            "description": "Group incoming sales by month with SQL aggregation.",
            "sql": "SELECT DATE_FORMAT(order_datetime, '%Y-%m') AS month, SUM(total_amount) AS revenue FROM food_orders GROUP BY DATE_FORMAT(order_datetime, '%Y-%m') ORDER BY month;",
            "rows": fetch_all("SELECT DATE_FORMAT(order_datetime, '%Y-%m') AS month, SUM(total_amount) AS revenue FROM food_orders GROUP BY DATE_FORMAT(order_datetime, '%Y-%m') ORDER BY month"),
        },
    ]
    return render_template("sql_demo.html", queries=queries)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
