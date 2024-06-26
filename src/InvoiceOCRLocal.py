import fitz  # PyMuPDF
import pytesseract
import os
from PIL import Image
import cv2
import numpy as np
import pandas as pd
import sys

# Set the Tesseract executable path
script_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(
    os.path.abspath(__file__))
tesseract_cmd_path = os.path.join(script_dir, 'tesseract', 'tesseract.exe')
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

# Print the Tesseract path to verify it
print(f"Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")

# List of known customer names
known_customers = [
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
    "Asahi Lifestyle Beverages",
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
    "KINGLOC WA"
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
    "KINGLOC WA": "KINGLOCWA"
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
        "Invoice": "",
        "Purchase Order": "",
        "Customer Name": "",
        "CardID": "",
        "Addr 1 - Line 1": "",
        "Items": []
    }

    print("Extracted text:")
    print(text)

    lines = text.split('\n')
    capture_items = False
    current_item = {}
    first_customer_matched = False

    for i, line in enumerate(lines):
        if "Date:" in line:
            data["Date"] = line.split(':')[-1].strip()
        elif "Invoice:" in line:
            data["Invoice"] = line.split(':')[-1].strip()
        elif "Purchase Order:" in line:
            data["Purchase Order"] = line.split(':')[-1].strip()
        elif "Invoice to:" in line:
            for customer in known_customers:
                if customer in line or (i + 1 < len(lines) and customer in lines[i + 1]):
                    if not first_customer_matched:
                        data["Customer Name"] = customer
                        data["CardID"] = customer_card_ids.get(customer, "")
                        first_customer_matched = True
                        print(f"Captured first customer name: {data['Customer Name']}")
                    else:
                        data["Addr 1 - Line 1"] = customer
                        print(f"Captured second customer name: {data['Addr 1 - Line 1']}")
                    break
        elif "Material Number" in line or "Material Nurnber" in line:  # account for OCR misreads
            capture_items = True
        elif capture_items:
            if "Direct deposit details:" in line:
                capture_items = False
                continue
            if line.strip():
                parts = line.split()
                # Try to handle spacing issues by ensuring the correct number of parts
                if len(parts) >= 2 and parts[0].isdigit():
                    qty = parts[0]
                    material_number = parts[1] if len(parts) > 3 else ""
                    unit_cost = parts[-2]
                    line_total = parts[-1]
                    description = " ".join(parts[2:-2]) if len(parts) > 3 else " ".join(parts[1:-1])
                    current_item = {
                        "Qty": qty,
                        "Material Number": material_number,
                        "Description": description,
                        "Unit Cost": unit_cost,
                        "Line Total": line_total,
                        "Date": data["Date"],
                        "Invoice": data["Invoice"],
                        "Purchase Order": data["Purchase Order"],
                        "Customer Name": data["Customer Name"],
                        "CardID": data["CardID"],
                        "Addr 1 - Line 1": data["Addr 1 - Line 1"],
                        "Account No.": 43000,
                        "Category": "McBride"
                    }
                    data["Items"].append(current_item)
                    print(f"Captured item: {current_item}")
                elif current_item:
                    # If current_item exists but the line doesn't have a new item, it's part of the description
                    current_item["Description"] += " " + line.strip()

    print("Parsed data:")
    print(data)

    return data

# Function to save data to CSV
def save_to_csv(data, output_path):
    items = data.pop("Items")
    df = pd.DataFrame(items)
    print(f"Data to be saved to CSV:\n{df}")
    df.to_csv(output_path, index=False)

# Main function to process all PDFs in the folder
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
            save_to_csv(data, output_csv)

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
