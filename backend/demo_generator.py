import os
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any

def create_receipt_image(
    filename: str,
    merchant: str,
    category: str,
    amount: float,
    date_str: str = "",
    items: list = None,
    tax_no: str = "GSTIN: 29AABCS1429B1Z8",
    footer_note: str = "Thank you for your business!",
    highlight_missing: str = None
) -> str:
    """
    Renders an authentic, stylish receipt voucher as a PNG image.
    """
    width, height = 480, 680
    bg_color = (250, 250, 249)  # Soft receipt paper off-white
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Use default bitmap font (guaranteed to work across all platforms)
    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_sub = ImageFont.truetype("arial.ttf", 13)
        font_body = ImageFont.truetype("arial.ttf", 15)
        font_bold = ImageFont.truetype("arialbd.ttf", 16)
        font_big = ImageFont.truetype("arialbd.ttf", 28)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_big = ImageFont.load_default()

    # Draw receipt border & top jagged/receipt header styling
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(214, 211, 209), width=2)
    draw.rectangle([(10, 10), (width - 10, 24)], fill=(16, 185, 129) if category != "Hotel" else (59, 130, 246))

    # Header
    y = 35
    draw.text((width // 2, y), merchant.upper(), fill=(15, 23, 42), font=font_title, anchor="mm")
    y += 24
    draw.text((width // 2, y), f"Category: {category}", fill=(100, 116, 139), font=font_sub, anchor="mm")
    y += 18
    draw.text((width // 2, y), tax_no, fill=(120, 113, 108), font=font_sub, anchor="mm")
    
    y += 20
    # Dashed separator line
    for x in range(30, width - 30, 12):
        draw.line([(x, y), (x + 6, y)], fill=(203, 213, 225), width=1)
    
    y += 16
    # Date & Receipt No
    if date_str:
        draw.text((32, y), f"Date: {date_str}", fill=(51, 65, 85), font=font_body)
    else:
        # Intentionally missing date
        draw.text((32, y), "Date: [UNSPECIFIED / BLURRED]", fill=(225, 29, 72), font=font_bold)
    
    draw.text((width - 32, y), f"RCP#{hash(merchant + str(amount)) % 89999 + 10000}", fill=(100, 116, 139), font=font_sub, anchor="ra")
    
    y += 25
    for x in range(30, width - 30, 12):
        draw.line([(x, y), (x + 6, y)], fill=(203, 213, 225), width=1)

    y += 22
    # Items table
    draw.text((32, y), "ITEM DESCRIPTION", fill=(100, 116, 139), font=font_sub)
    draw.text((width - 32, y), "AMOUNT (INR)", fill=(100, 116, 139), font=font_sub, anchor="ra")
    y += 20

    if not items:
        items = [("Service / Goods Provided", amount)]

    for item_name, item_amt in items:
        draw.text((32, y), item_name[:32], fill=(30, 41, 59), font=font_body)
        draw.text((width - 32, y), f"₹{item_amt:,.2f}", fill=(30, 41, 59), font=font_body, anchor="ra")
        y += 22

    # Fill space
    y = max(y, 450)
    for x in range(30, width - 30, 12):
        draw.line([(x, y), (x + 6, y)], fill=(203, 213, 225), width=1)

    y += 25
    # Total Box
    draw.rectangle([(25, y - 5), (width - 25, y + 55)], fill=(241, 245, 249), outline=(226, 232, 240))
    draw.text((40, y + 22), "TOTAL DUE:", fill=(15, 23, 42), font=font_bold, anchor="lm")
    draw.text((width - 40, y + 22), f"₹{amount:,.2f}", fill=(15, 23, 42), font=font_big, anchor="rm")

    y += 75
    # Payment info & Purpose
    draw.text((32, y), "Payment: CORPORATE BILLING / CARD PAID", fill=(71, 85, 105), font=font_sub)
    y += 18
    if highlight_missing == "business_purpose":
        draw.text((32, y), "Business Purpose: [NOT PROVIDED]", fill=(225, 29, 72), font=font_bold)
    else:
        draw.text((32, y), "Status: Verified Valid Voucher", fill=(16, 185, 129), font=font_sub)

    y += 30
    draw.text((width // 2, y), footer_note, fill=(148, 163, 184), font=font_sub, anchor="mm")

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename, "PNG")
    return filename

def create_pdf_receipt(
    filename: str,
    merchant: str,
    category: str,
    amount: float,
    date_str: str,
    items: list
) -> str:
    """
    Creates a clean PDF receipt by rendering the image and saving as PDF.
    """
    temp_img_path = filename.replace(".pdf", "_temp.png")
    create_receipt_image(
        filename=temp_img_path,
        merchant=merchant,
        category=category,
        amount=amount,
        date_str=date_str,
        items=items,
        tax_no="INVOICE / TAX CERTIFIED - PENDING FILING"
    )
    img = Image.open(temp_img_path)
    img_converted = img.convert("RGB")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img_converted.save(filename, "PDF", resolution=100.0)
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)
    return filename

def generate_sample_batch_files(base_dir: str = "backend/sample_receipts") -> List[Dict[str, Any]]:
    """
    Generates the exact 11 receipts matching the user's scenario:
    Total: ₹38,420
    ✅ 8 ready
    ⚠️ 2 need clarification (Hotel ₹4,850 missing purpose, Taxi ₹1,200 missing date)
    🔴 1 duplicate (Cafe Coffee Day ₹1,500)
    """
    os.makedirs(base_dir, exist_ok=True)
    
    receipts_meta = [
        # 1. Hotel Invoice (₹4,850) - Needs Clarification: Missing business purpose
        {
            "id": "exp-1",
            "file_name": "hotel_grand_orchid_invoice.png",
            "is_pdf": False,
            "merchant": "The Grand Orchid Hotel",
            "category": "Hotel",
            "amount": 4850.0,
            "date": "2026-09-23",
            "items": [("Deluxe Room Stay (1 Night)", 4200.0), ("GST & Service Tax", 650.0)],
            "business_purpose": None,
            "highlight_missing": "business_purpose"
        },
        # 2. Taxi Receipt (₹1,200) - Needs Clarification: Missing travel date
        {
            "id": "exp-2",
            "file_name": "taxi_city_cabs_bangalore.png",
            "is_pdf": False,
            "merchant": "City Cabs Bangalore",
            "category": "Taxi",
            "amount": 1200.0,
            "date": None,  # Intentionally missing date
            "items": [("Airport to Tech Park Transit", 1200.0)],
            "business_purpose": "Airport Transfer",
            "highlight_missing": "date"
        },
        # 3. Cafe Coffee Day (₹1,500) - Ready
        {
            "id": "exp-3",
            "file_name": "ccd_team_snacks.png",
            "is_pdf": False,
            "merchant": "Cafe Coffee Day",
            "category": "Meals",
            "amount": 1500.0,
            "date": "2026-09-22",
            "items": [("Cappuccino x 3", 600.0), ("Sandwiches & Muffins", 900.0)],
            "business_purpose": "Team sync meeting"
        },
        # 4. Cafe Coffee Day (₹1,500) - Duplicate of #3
        {
            "id": "exp-4",
            "file_name": "ccd_team_snacks_copy.png",
            "is_pdf": False,
            "merchant": "Cafe Coffee Day",
            "category": "Meals",
            "amount": 1500.0,
            "date": "2026-09-22",
            "items": [("Cappuccino x 3", 600.0), ("Sandwiches & Muffins", 900.0)],
            "business_purpose": "Team sync meeting"
        },
        # 5. Indigo Airlines Flight Ticket (₹12,500) - PDF, Ready
        {
            "id": "exp-5",
            "file_name": "indigo_flight_blr_bom.pdf",
            "is_pdf": True,
            "merchant": "IndiGo Airlines",
            "category": "Transport",
            "amount": 12500.0,
            "date": "2026-09-21",
            "items": [("Flight BLR-BOM Roundtrip", 11200.0), ("Passenger Service Fee & Taxes", 1300.0)],
            "business_purpose": "Client QBR on-site"
        },
        # 6. Toscano Client Dinner (₹6,450) - Ready
        {
            "id": "exp-6",
            "file_name": "toscano_client_dinner.png",
            "is_pdf": False,
            "merchant": "Toscano Ristorante",
            "category": "Meals",
            "amount": 6450.0,
            "date": "2026-09-23",
            "items": [("4-Course Dinner with Client Stakeholders", 5800.0), ("Taxes & Service", 650.0)],
            "business_purpose": "Client dinner with VP Engineering"
        },
        # 7. Uber Airport Ride (₹850) - Ready
        {
            "id": "exp-7",
            "file_name": "uber_ride_airport.png",
            "is_pdf": False,
            "merchant": "Uber India",
            "category": "Taxi",
            "amount": 850.0,
            "date": "2026-09-21",
            "items": [("Uber Premier: Residence to Airport", 850.0)],
            "business_purpose": "Airport commute"
        },
        # 8. WeWork Galaxy Day Pass (₹1,200) - Ready
        {
            "id": "exp-8",
            "file_name": "wework_day_pass.png",
            "is_pdf": False,
            "merchant": "WeWork Galaxy",
            "category": "Office Supplies",
            "amount": 1200.0,
            "date": "2026-09-22",
            "items": [("Day Pass & Conference Room Access", 1200.0)],
            "business_purpose": "Remote workspace during client visit"
        },
        # 9. Smoke House Deli Lunch (₹3,420) - Ready
        {
            "id": "exp-9",
            "file_name": "smoke_house_deli_lunch.png",
            "is_pdf": False,
            "merchant": "Smoke House Deli",
            "category": "Meals",
            "amount": 3420.0,
            "date": "2026-09-24",
            "items": [("Working Lunch with Delivery Leads", 3100.0), ("Taxes", 320.0)],
            "business_purpose": "Technical architecture alignment lunch"
        },
        # 10. Uber Client Office (₹550) - Ready
        {
            "id": "exp-10",
            "file_name": "uber_ride_client_office.png",
            "is_pdf": False,
            "merchant": "Uber India",
            "category": "Taxi",
            "amount": 550.0,
            "date": "2026-09-23",
            "items": [("Uber Go: Hotel to Client HQ", 550.0)],
            "business_purpose": "Travel to client meeting"
        },
        # 11. Airtel Corporate Telecom Bill (₹4,400) - PDF, Ready
        {
            "id": "exp-11",
            "file_name": "airtel_broadband_bill.pdf",
            "is_pdf": True,
            "merchant": "Bharti Airtel Telecom",
            "category": "Telecommunication",
            "amount": 4400.0,
            "date": "2026-09-20",
            "items": [("Corporate Fiber High-speed Plan (2 Months)", 4400.0)],
            "business_purpose": "Home office broadband reimbursement"
        }
    ]

    for item in receipts_meta:
        target_path = os.path.join(base_dir, item["file_name"])
        if item["is_pdf"]:
            create_pdf_receipt(
                filename=target_path,
                merchant=item["merchant"],
                category=item["category"],
                amount=item["amount"],
                date_str=item["date"] or "",
                items=item["items"]
            )
        else:
            create_receipt_image(
                filename=target_path,
                merchant=item["merchant"],
                category=item["category"],
                amount=item["amount"],
                date_str=item["date"] or "",
                items=item["items"],
                highlight_missing=item.get("highlight_missing")
            )

    return receipts_meta

def generate_perks_batch_files(base_dir: str = "backend/sample_receipts") -> List[Dict[str, Any]]:
    """
    Generates test receipts specifically demonstrating:
    1. Mobile Headset (Reliance Digital valid vs Croma violation)
    2. Travel Assistance - Driver Salary (Sept within ₹10k vs Oct exceeding ₹10k)
    3. Fuel Expenses (Indian Oil + HPCL exceeding monthly ₹15k cap)
    """
    os.makedirs(base_dir, exist_ok=True)
    
    perks_meta = [
        # 1. Valid Reliance Digital Headset (₹18,500)
        {
            "id": "perk-1",
            "file_name": "headset_reliance_digital_sony.png",
            "is_pdf": False,
            "merchant": "Reliance Digital Retail Ltd",
            "category": "Mobile Headset",
            "amount": 18500.0,
            "date": "2026-09-18",
            "items": [("Sony WH-1000XM5 ANC Headset", 15678.0), ("GST 18%", 2822.0)],
            "business_purpose": "Client communication headset"
        },
        # 2. Invalid Vendor: Croma Headset (₹22,000)
        {
            "id": "perk-2",
            "file_name": "headset_croma_bose.png",
            "is_pdf": False,
            "merchant": "Croma Electronics",
            "category": "Mobile Headset",
            "amount": 22000.0,
            "date": "2026-09-19",
            "items": [("Bose QuietComfort 45 Headphones", 18645.0), ("GST 18%", 3355.0)],
            "business_purpose": "Headset purchase"
        },
        # 3. Driver Salary - September within cap (₹9,500)
        {
            "id": "perk-3",
            "file_name": "driver_salary_september.png",
            "is_pdf": False,
            "merchant": "Ramesh Kumar (Personal Driver)",
            "category": "Driver Salary",
            "amount": 9500.0,
            "date": "September 2026",
            "items": [("Driver Salary Allowance (Sept 2026)", 9500.0)],
            "business_purpose": "Travel Assistance - Monthly Driver Salary"
        },
        # 4. Driver Salary - October exceeding cap (₹12,000)
        {
            "id": "perk-4",
            "file_name": "driver_salary_october.png",
            "is_pdf": False,
            "merchant": "Ramesh Kumar (Personal Driver)",
            "category": "Driver Salary",
            "amount": 12000.0,
            "date": "October 2026",
            "items": [("Driver Salary + Overtime Allowance (Oct 2026)", 12000.0)],
            "business_purpose": "Travel Assistance - Monthly Driver Salary"
        },
        # 5. Fuel Receipt - September part 1 (₹4,500)
        {
            "id": "perk-5",
            "file_name": "fuel_indian_oil_sept.png",
            "is_pdf": False,
            "merchant": "Indian Oil Petrol Pump",
            "category": "Fuel",
            "amount": 4500.0,
            "date": "2026-09-22",
            "items": [("Speed Petrol (45.2 Litres)", 4500.0)],
            "business_purpose": "Business travel fuel refuel"
        },
        # 6. Fuel Receipt - September part 2 (₹12,000) -> Combined = ₹16,500 (exceeds ₹15,000)
        {
            "id": "perk-6",
            "file_name": "fuel_hpcl_sept.png",
            "is_pdf": False,
            "merchant": "HPCL Auto Care Fuel Station",
            "category": "Fuel",
            "amount": 12000.0,
            "date": "2026-09-28",
            "items": [("Power Petrol Refuel (Fleet Tank)", 12000.0)],
            "business_purpose": "Business travel fuel refuel"
        }
    ]

    for item in perks_meta:
        target_path = os.path.join(base_dir, item["file_name"])
        create_receipt_image(
            filename=target_path,
            merchant=item["merchant"],
            category=item["category"],
            amount=item["amount"],
            date_str=item["date"] or "",
            items=item["items"],
            highlight_missing=item.get("highlight_missing")
        )

    return perks_meta

if __name__ == "__main__":
    generate_sample_batch_files()
    generate_perks_batch_files()
    print("Generated all sample receipts successfully!")
