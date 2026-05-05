import sqlite3
from collections import defaultdict

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# --- Load data ---
cursor.execute("SELECT * FROM shop_customer")
customers = cursor.fetchall()
customer_cols = [d[0] for d in cursor.description]

cursor.execute("SELECT * FROM shop_order")
orders = cursor.fetchall()
order_cols = [d[0] for d in cursor.description]

cursor.execute("SELECT * FROM shop_orderitem")
order_items = cursor.fetchall()
item_cols = [d[0] for d in cursor.description]

cursor.execute("SELECT * FROM shop_orderpayment")
payments = cursor.fetchall()
payment_cols = [d[0] for d in cursor.description]

# --- Convert to dicts ---
customers = [dict(zip(customer_cols, c)) for c in customers]
orders = [dict(zip(order_cols, o)) for o in orders]
order_items = [dict(zip(item_cols, i)) for i in order_items]
payments = [dict(zip(payment_cols, p)) for p in payments]

# --- Group data ---
orders_by_customer = defaultdict(list)
items_by_order = defaultdict(list)
payments_by_order = defaultdict(list)

for o in orders:
    orders_by_customer[o['customer_id']].append(o)

for i in order_items:
    items_by_order[i['order_id']].append(i)

for p in payments:
    payments_by_order[p['order_id']].append(p)

# --- Print report ---
for customer in customers:
    print("\n" + "="*50)
    print(f"👤 Customer: {customer['name']}")
    print(f"📞 Mobile: {customer['mobile_number']}")

    cust_orders = orders_by_customer.get(customer['id'], [])

    if not cust_orders:
        print("  No orders")
        continue

    total_due = 0
    total_paid = 0

    for order in cust_orders:
        print("\n  🧾 Order ID:", order['id'])
        print("  Total:", order['total_price'], " | Due:", order['due_amount'])

        total_due += order['due_amount']

        # --- Items ---
        print("   📦 Items:")
        for item in items_by_order.get(order['id'], []):
            print(f"     - {item['product_name']} | Qty: {item['quantity']} | Price: {item['total_price']}")

        # --- Payments ---
        order_payments = payments_by_order.get(order['id'], [])
        paid = sum(p['amount'] for p in order_payments)
        total_paid += paid

        print("   💰 Paid:", paid)

    print("\n  🔹 TOTAL PAID:", total_paid)
    print("  🔹 TOTAL DUE :", total_due)

conn.close()

