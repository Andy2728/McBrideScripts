import fitz
import pytesseract
import os
from PIL import Image
import cv2
import numpy as np
import pandas as pd
import sys
from datetime import datetime

# Set the Tesseract executable path
script_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
tesseract_cmd_path = os.path.join(script_dir, 'tesseract', 'tesseract.exe')
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

# Print the Tesseract path to verify it
print(f"Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")

# List of known customer names
known_customers = [
    "Asahi Lifestyle Beverages",
    "Asahi Beverages NSW",
    "Asahi Beverages QLD - Heathwood",
    "Asahi Beverages QLD - Trailways",
    "Asahi Beverages SA",
    "Asahi Beverages SA - AB Service",
    "Asahi Beverages SA - Bulk",
    "Asahi Beverages TAS - Invermay",
    "Asahi Beverages TAS - New Town",
    "Asahi Beverages VIC",
    "Asahi Beverages VIC - Bulk",
    "Asahi Beverages WA",
    "Asahi Beverages WA - Bulk",
    "ATLANTA REFRIGERATION SA",
    "BENDESIGNS NT",
    "Frozen Sunshine",
    "Hoshizaki Lancer",
    "JJR Engineering Pty Ltd",
    "KINGLOC NSW",
    "Kingloc QLD",
    "Kingloc TAS/RBR Refrigeration",
    "KINGLOC VIC",
    "PFM LOGISTICS VIC",
    "PFM NT",
    "PFM SA",
    "Rud Chains",
    "Wrapt Freight NSW",
    "KINGLOC WA",
    "ZONCA REFRIGERATION",
    "PICCOLO ME HORSLEY PARK",
    "TCN VENDING AUSTRALIA"
]

# Dictionary mapping customer names to CardIDs
customer_card_ids = {
    "Asahi Beverages NSW": "ASAHINSW",
    "Asahi Beverages QLD - Heathwood": "ASAHIQ-HW",
    "Asahi Beverages QLD - Trailways": "ASAHIQLD-TRL",
    "Asahi Beverages SA": "ASAHISA",
    "Asahi Beverages SA - AB Service": "ASAHISA-AB",
    "Asahi Beverages SA - Bulk": "ASAHISA-BLK",
    "Asahi Beverages TAS - Invermay": "ASAHITAS-I",
    "Asahi Beverages TAS - New Town": "ASAHITAS-NT",
    "Asahi Beverages VIC": "ASAHI-VIC",
    "Asahi Beverages VIC - Bulk": "ASAHIVIC-BLK",
    "Asahi Lifestyle Beverages": "ASAHI",
    "Asahi Beverages WA": "ASAHIWA",
    "Asahi Beverages WA - Bulk": "ASAHIWA-BLK",
    "ATLANTA REFRIGERATION SA": "ATLANTAFRDG",
    "BENDESIGNS NT": "BENDESIGNS",
    "Frozen Sunshine": "FROZENSUNSHINE",
    "Hoshizaki Lancer": "HOSHIZAKIL",
    "JJR Engineering Pty Ltd": "JJRENGINEERING",
    "KINGLOC NSW": "KINGLOCNSW",
    "Kingloc QLD": "KINGLOCQLD",
    "Kingloc TAS/RBR Refrigeration": "KINGLOCTAS-R",
    "KINGLOC VIC": "KINGLOC-VIC",
    "PFM LOGISTICS VIC": "PFM-VIC-LGT",
    "PFM NT": "PFM-NT",
    "PFM SA": "PFM-SA",
    "Rud Chains": "RUDCHAINS",
    "Wrapt Freight NSW": "WRPTFREIGHT",
    "KINGLOC WA": "KINGLOCWA",
    "ZONCA REFRIGERATION": "ZONCAFRIDGE",
    "PICCOLO ME HORSLEY PARK": "PICCOLOMHP",
    "TCN VENDING AUSTRALIA": "TCNVENDAUS"
}

# Function to preprocess image for better OCR results using OpenCV
def preprocess_image(image):
    # Convert PIL image to numpy array
    img = np.array(image)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Enhance contrast by applying histogram equalization
    gray = cv2.equalizeHist(gray)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)

    # Convert back to PIL image
    processed_image = Image.fromarray(thresh)
    return processed_image

# Function to extract text from PDF using OCR
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(5, 5))  # Increase resolution
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Preprocess the image for better OCR results
        img = preprocess_image(img)

        # Try different Tesseract configurations
        custom_config = r'--oem 3 --psm 6'
        page_text = pytesseract.image_to_string(img, config=custom_config)
        print(f"Extracted text from page {page_num} of {pdf_path}:\n{page_text}\n")
        text += page_text + "\n\n"  # Add extra line breaks between lines
    return text

# Function to parse the extracted text to find the target values
def parse_text(text):
    data = {
        "Date": "",
        "Invoice #": "",
        "Customer PO": "",
        "Co./Last Name": "",
        "Card ID": "",
        "Addr 1 - Line 1": "",
        "- Line 2": "",
        "- Line 3": "",
        "- Line 4": "",
        "Items": []
    }

    print("Extracted text:")
    print(text)

    lines = text.split('\n')
    capture_items = False
    current_item = {}
    first_customer_matched = False
    address_lines = []

    for i, line in enumerate(lines):
        print(f"Processing line: {line.strip()}")
        if "Date:" in line:
            date_str = line.split(':')[-1].strip()
            data["Date"] = date_str

            # Check if the date is within the current month
            try:
                invoice_date = datetime.strptime(date_str, "%d/%m/%Y")
                current_date = datetime.now()
                if invoice_date.month != current_date.month or invoice_date.year != current_date.year:
                    data["Date"] = current_date.replace(day=1).strftime("%d/%m/%Y")
                    print(f"Updated date to the first day of the current month: {data['Date']}")
            except ValueError:
                print(f"Invalid date format: {date_str}")
        elif "Invoice:" in line:
            data["Invoice #"] = line.split(':')[-1].strip()
        elif "Purchase Order:" in line:
            data["Customer PO"] = line.split(':')[-1].strip()
        elif "Invoice to:" in line:
            # Continue to next line to process customers
            continue
        elif "Ship to:" in line:
            # Process the customers in the next line
            next_line = lines[i + 1].strip()
            words = next_line.split()
            found_customers = []

            # Build potential customer names from words
            current_name = ""
            for word in words:
                if current_name:
                    current_name += " "
                current_name += word
                if current_name in known_customers:
                    found_customers.append(current_name)
                    current_name = ""  # Reset for the next potential customer

            # Ensure we have at least two customers
            if len(found_customers) >= 2:
                data["Co./Last Name"] = found_customers[0]
                data["Card ID"] = customer_card_ids.get(found_customers[0], "")
                first_customer_matched = True
                print(f"Captured first customer name: {data['Co./Last Name']}")

                data["Addr 1 - Line 1"] = found_customers[1]
                # Capture the address lines for the second customer
                address_lines = []
                for j in range(i + 2, len(lines)):
                    if "QTY" in lines[j] and "Material Number" in lines[j]:
                        break
                    if lines[j].strip():  # Exclude empty lines
                        address_lines.append(lines[j].strip())
                if len(address_lines) > 0:
                    data["- Line 2"] = address_lines[0]
                if len(address_lines) > 1:
                    data["- Line 3"] = address_lines[1]
                if len(address_lines) > 2:
                    data["- Line 4"] = address_lines[2]
                print(f"Captured second customer name and address: {data['Addr 1 - Line 1']}, {address_lines}")
            continue
        else:
            for customer in known_customers:
                if customer in line:
                    if not first_customer_matched:
                        data["Co./Last Name"] = customer
                        data["Card ID"] = customer_card_ids.get(customer, "")
                        first_customer_matched = True
                        print(f"Captured first customer name: {data['Co./Last Name']}")
                    else:
                        data["Addr 1 - Line 1"] = customer
                        # Capture the address lines for the second customer
                        address_lines = []
                        for j in range(i + 1, len(lines)):
                            if "QTY" in lines[j] and "Material Number" in lines[j]:
                                break
                            if lines[j].strip():  # Exclude empty lines
                                address_lines.append(lines[j].strip())
                        if len(address_lines) > 0:
                            data["- Line 2"] = address_lines[0]
                        if len(address_lines) > 1:
                            data["- Line 3"] = address_lines[1]
                        if len(address_lines) > 2:
                            data["- Line 4"] = address_lines[2]
                        print(f"Captured second customer name and address: {data['Addr 1 - Line 1']}, {address_lines}")
                        break

        if "Material Number" in line or "Material Nurnber" in line:  # account for OCR misreads
            capture_items = True
            print(f"Starting to capture items...")
        elif capture_items:
            if "Direct deposit details:" in line:
                capture_items = False
                print(f"Stopped capturing items.")
                continue
            if line.strip():
                parts = line.split()
                if len(parts) >= 2 and parts[0].isdigit() and parts[-1].replace(",", "").replace("$", "").replace(".", "").isdigit():
                    qty = parts[0]
                    material_number = parts[1] if len(parts) > 3 else ""
                    unit_cost = parts[-2]
                    amount_str = parts[-1].replace(",", "").replace("$", "")  # Remove comma and dollar sign
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        print(f"Skipping invalid item line: {line.strip()}")
                        continue
                    inc_tax_amount = amount
                    description = " ".join(parts[2:-2]) if len(parts) > 3 else " ".join(parts[1:-1])
                    if "Freight" in description:
                        description = description.strip()
                    else:
                        description = f"{material_number} - {description.strip()} x {qty}"
                    current_item = {
                        "Description": description,
                        "Amount": amount,
                        "Inc-Tax Amount": inc_tax_amount,
                        "Date": data["Date"],
                        "Invoice #": data["Invoice #"],
                        "Customer PO": data["Customer PO"],
                        "Co./Last Name": data["Co./Last Name"],
                        "Card ID": data["Card ID"],
                        "Addr 1 - Line 1": data["Addr 1 - Line 1"],
                        "- Line 2": address_lines[0] if len(address_lines) > 0 else "",
                        "- Line 3": address_lines[1] if len(address_lines) > 1 else "",
                        "- Line 4": address_lines[2] if len(address_lines) > 2 else "",
                        "Account #": 43000,
                        "Category": "Yeronga",
                        "Job": data["Invoice #"],
                        "Tax Code": "GST"
                    }
                    data["Items"].append(current_item)
                    print(f"Captured item: {current_item}")
                elif current_item:
                    current_item["Description"] += " " + line.strip()

    print("Parsed data:")
    print(data)

    return data

# Function to save data to CSV and TXT
def save_to_csv_and_txt(data, output_csv_path, output_txt_path):
    items = data.pop("Items")
    df = pd.DataFrame(items)

    # Save to CSV
    print(f"Data to be saved to CSV:\n{df}")
    df.to_csv(output_csv_path, index=False, columns=[
        "Description", "Amount", "Inc-Tax Amount", "Date", "Invoice #", "Customer PO", "Co./Last Name",
        "Card ID", "Addr 1 - Line 1", "- Line 2", "- Line 3", "- Line 4", "Account #", "Category", "Job", "Tax Code"
    ])

    # Save to TXT in tab-separated format with updated headers
    with open(output_txt_path, "w") as txt_file:
        # Write headers
        txt_file.write(
            "Description\tAmount\tInc-Tax Amount\tDate\tInvoice #\tCustomer PO\tCo./Last Name\tCard ID\tAddr 1 - Line 1\t- Line 2\t- Line 3\t- Line 4\tAccount #\tCategory\tJob\tTax Code\n")
        # Write item data
        for item in items:
            txt_file.write(
                f"{item['Description']}\t{item['Amount']:.2f}\t{item['Inc-Tax Amount']:.2f}\t{item['Date']}\t{item['Invoice #']}\t{item['Customer PO']}\t"
                f"{item['Co./Last Name']}\t{item['Card ID']}\t{item['Addr 1 - Line 1']}\t{item['- Line 2']}\t{item['- Line 3']}\t{item['- Line 4']}\t{item['Account #']}\t{item['Category']}\t{item['Job']}\t{item['Tax Code']}\n"
            )
    print(f"Data saved to TXT in tab-separated format.")

# Function to process all PDFs in the folder
def process_invoices(input_folder, output_folder):
    if not os.path.exists(input_folder):
        print(f"Input folder '{input_folder}' does not exist.")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            text = extract_text_from_pdf(pdf_path)
            data = parse_text(text)
            output_csv = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.csv")
            output_txt = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
            save_to_csv_and_txt(data, output_csv, output_txt)

# Paths to input and output folders
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
input_folder = os.path.join(script_dir, 'Invoices')
output_folder = os.path.join(script_dir, 'OUT')

# Debugging prints
print(f"Input folder: {input_folder}")
print(f"Output folder: {output_folder}")

# Run the script
process_invoices(input_folder, output_folder)
