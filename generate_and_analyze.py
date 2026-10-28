"""Generate a reproducible synthetic retail dataset and portfolio charts.

All records are fictional and must be described as synthetic in any portfolio.
Run: python generate_and_analyze.py
"""
from pathlib import Path
import csv
import random
from collections import defaultdict
from datetime import date, timedelta

from PIL import Image, ImageDraw, ImageFont

SEED = 17
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
IMAGE_DIR = ROOT / "images"
DATA_DIR.mkdir(exist_ok=True)
IMAGE_DIR.mkdir(exist_ok=True)

random.seed(SEED)
products = [
    ("P001", "Ceramic Mug", 8.50),
    ("P002", "Canvas Tote", 12.00),
    ("P003", "Desk Plant", 15.00),
    ("P004", "Notebook Set", 9.00),
    ("P005", "Water Bottle", 18.00),
    ("P006", "Desk Lamp", 32.00),
    ("P007", "Pen Pack", 5.00),
    ("P008", "Travel Cup", 14.00),
]
customers = [f"C{i:04d}" for i in range(1, 181)]
countries = ["United Kingdom", "Germany", "France", "Netherlands", "Spain"]
rows = []
invoice_number = 10000

# Create 1,440 orders across 2024. December has a designed seasonal uplift.
for month in range(1, 13):
    order_count = 100 + (35 if month in (11, 12) else 0)
    for _ in range(order_count):
        invoice_number += 1
        day = random.randint(1, 27)
        order_date = date(2024, month, day)
        customer = random.choice(customers)
        country = random.choices(countries, weights=[65, 12, 10, 7, 6])[0]
        # A small subset of products is intentionally more popular.
        basket_lines = random.choices(products, weights=[18, 15, 12, 16, 11, 6, 14, 8], k=random.choices([1, 2, 3], [72, 23, 5])[0])
        for sku, name, price in basket_lines:
            quantity = random.choices([1, 2, 3, 4], [65, 23, 9, 3])[0]
            rows.append({
                "invoice_no": f"{invoice_number}",
                "stock_code": sku,
                "description": name,
                "quantity": quantity,
                "unit_price": f"{price:.2f}",
                "invoice_date": order_date.isoformat(),
                "customer_id": customer,
                "country": country,
            })

csv_path = DATA_DIR / "synthetic_retail_transactions.csv"
with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

# Aggregate order-level and product-level results.
month_sales = defaultdict(float)
month_orders = defaultdict(set)
product_sales = defaultdict(float)
customer_orders = defaultdict(set)
cohort_activity = defaultdict(set)
for r in rows:
    month = r["invoice_date"][:7]
    revenue = int(r["quantity"]) * float(r["unit_price"])
    month_sales[month] += revenue
    month_orders[month].add(r["invoice_no"])
    product_sales[r["description"]] += revenue
    customer_orders[r["customer_id"]].add(r["invoice_no"])
    cohort_activity[r["customer_id"]].add(month)

months = sorted(month_sales)
sales_values = [month_sales[m] for m in months]
orders_values = [len(month_orders[m]) for m in months]
top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
repeat_customers = sum(len(order_set) >= 2 for order_set in customer_orders.values())
repeat_rate = repeat_customers / len(customer_orders) * 100
nov_dec = month_sales["2024-11"] + month_sales["2024-12"]
jan_oct_avg = sum(month_sales[f"2024-{m:02d}"] for m in range(1, 11)) / 10
nov_dec_avg = nov_dec / 2
peak_lift = (nov_dec_avg / jan_oct_avg - 1) * 100

font = ImageFont.load_default()

def draw_line_chart(path: Path) -> None:
    width, height = 1200, 650
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 90, 90, 1140, 530
    draw.text((left, 28), "Synthetic Retail Revenue by Month (2024)", fill="#172554", font=font)
    draw.text((left, 55), "Revenue (fictional currency units)", fill="#334155", font=font)
    low, high = 0, max(sales_values) * 1.15
    for tick in range(5):
        y = bottom - (bottom - top) * tick / 4
        value = low + (high - low) * tick / 4
        draw.line((left, y, right, y), fill="#e2e8f0", width=1)
        draw.text((8, y - 7), f"{value:,.0f}", fill="#475569", font=font)
    points = []
    for i, value in enumerate(sales_values):
        x = left + (right - left) * i / (len(sales_values) - 1)
        y = bottom - (bottom - top) * value / high
        points.append((x, y))
        draw.text((x - 17, bottom + 15), months[i][5:], fill="#475569", font=font)
    draw.line(points, fill="#2563eb", width=4)
    for x, y in points:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="#2563eb")
    draw.line((left, top, left, bottom), fill="#64748b", width=2)
    draw.line((left, bottom, right, bottom), fill="#64748b", width=2)
    image.save(path)

def draw_bar_chart(path: Path) -> None:
    width, height = 1200, 650
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 190, 90, 1120, 570
    draw.text((left, 28), "Synthetic Revenue by Product", fill="#172554", font=font)
    draw.text((left, 55), "Revenue (fictional currency units)", fill="#334155", font=font)
    max_value = max(v for _, v in top_products) * 1.1
    for idx, (name, value) in enumerate(top_products):
        y = top + idx * 58
        bar_end = left + (right - left) * value / max_value
        draw.text((12, y + 8), name, fill="#334155", font=font)
        draw.rounded_rectangle((left, y, bar_end, y + 32), radius=5, fill="#0f766e")
        draw.text((bar_end + 8, y + 8), f"{value:,.0f}", fill="#334155", font=font)
    draw.line((left, top - 8, left, bottom), fill="#64748b", width=2)
    image.save(path)

draw_line_chart(IMAGE_DIR / "monthly_revenue.png")
draw_bar_chart(IMAGE_DIR / "product_revenue.png")

with (ROOT / "FINDINGS.md").open("w", encoding="utf-8") as f:
    f.write("# Findings — Synthetic Retail Demonstration\n\n")
    f.write("> **Important:** This is fictional, programmatically generated data. These findings do not describe a real retailer and must not be presented as real business evidence.\n\n")
    f.write(f"- The dataset contains **{len(rows):,} transaction lines**, **{len(set(r['invoice_no'] for r in rows)):,} orders**, and **{len(customer_orders):,} fictional customers**.\n")
    f.write(f"- **{repeat_customers:,} customers ({repeat_rate:.1f}%)** placed at least two orders in the generated year.\n")
    f.write(f"- Average monthly revenue in November–December was **{peak_lift:.1f}%** higher than the January–October monthly average by design.\n")
    f.write(f"- Highest-revenue generated product: **{top_products[0][0]}** ({top_products[0][1]:,.2f} fictional currency units).\n\n")
    f.write("## Charts\n\n![Synthetic monthly revenue](images/monthly_revenue.png)\n\n![Synthetic product revenue](images/product_revenue.png)\n\n")
    f.write("## Interpretation and limitations\n\n")
    f.write("The seasonal uplift and product/customer patterns are artifacts of the generation rules, not discoveries from observed customer behavior. Use this dataset to demonstrate code and chart formatting only. For a job portfolio, replace it with a public real-world dataset and rerun the analysis before making business recommendations.\n")

print(f"Created {csv_path} ({len(rows)} rows)")
print(f"Repeat customers: {repeat_customers}/{len(customer_orders)} ({repeat_rate:.1f}%)")
print(f"Nov-Dec monthly revenue vs Jan-Oct average: {peak_lift:+.1f}%")
print(f"Top product: {top_products[0][0]} ({top_products[0][1]:.2f})")
