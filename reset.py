import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "orders.db")
if os.path.exists(db_path):
    os.remove(db_path)
    print("Old database deleted.")
else:
    print("No old database found.")

from database import setup_database, seed_orders, fetch_all_orders
setup_database()
seed_orders()
orders = fetch_all_orders()
print(f"SUCCESS — {len(orders)} orders in database:")
for o in orders:
    print(f"  {o['order_id']} | {o['customer_name']:<16} | {o['product_name']:<30} | PKR {o['total_price']:>10,.0f}")