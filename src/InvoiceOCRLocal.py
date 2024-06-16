import fitz  # PyMuPDF
import pytesseract
import os
from PIL import Image
import cv2
import numpy as np
import pandas as pd
import sys

# Set the Tesseract executable path
script_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
tesseract_cmd_path = os.path.join(script_dir, 'tesseract', 'tesseract.exe')
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

# Print the Tesseract path to verify it
print(f"Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")

# List of known customer names
known_customers = [
    "Kings Stones Music", "Variety Group", "SD DETAILING", "Pirate Life",
    "Mackay North State High School", "MANAWARI PTY LTD", "Frozen Sunshine",
    "Vendors Plus", "KINGLOC COMMERCIAL EQUIPMENT", "Coca-Cola Europacific Partners (EQS)",
    "Asahi Lifestyle Beverages", "Cleanaway Co Pty Ltd", "JJR Engineering Pty Ltd",
    "Sanden International", "Rud Chains", "Oxley Golf Club", "XL Metals",
    "Sunstate Services", "PepsiCo Asia Pacific", "Tusker Roundabout",
    "Big Wave Printing Pty Ltd", "Room 3W-245", "Cool Kundu",
    "Unit 11, 7-15 Gundah Road"
]

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
        "Items": []
    }

    print("Extracted text:")
    print(text)

    lines = text.split('\n')
    capture_items = False
    for i, line in enumerate(lines):
        if "Date:" in line:
            data["Date"] = line.split(':')[-1].strip()
        elif "Invoice:" in line:
            data["Invoice"] = line.split(':')[-1].strip()
        elif "Purchase Order:" in line:
            data["Purchase Order"] = line.split(':')[-1].strip()
        elif "Invoice to:" in line:
            # Check for known customer names in the following lines
            for customer in known_customers:
                if customer in line or (i + 1 < len(lines) and customer in lines[i + 1]):
                    data["Customer Name"] = customer
                    break
            print(f"Captured customer name: {data['Customer Name']}")
        elif "Material Number" in line or "Material Nurnber" in line:  # account for OCR misreads
            capture_items = True
        elif capture_items:
            if "Direct deposit details:" in line:
                capture_items = False
                continue
            if line.strip() and line.split()[0].isdigit():
                parts = line.split()
                # Try to handle spacing issues by ensuring the correct number of parts
                if len(parts) >= 5:
                    qty = parts[0]
                    material_number = parts[1]
                    unit_cost = parts[-2]
                    line_total = parts[-1]
                    description = " ".join(parts[2:-2])
                    item = {
                        "Qty": qty,
                        "Material Number": material_number,
                        "Description": description,
                        "Unit Cost": unit_cost,
                        "Line Total": line_total
                    }
                    item["Date"] = data["Date"]
                    item["Invoice"] = data["Invoice"]
                    item["Purchase Order"] = data["Purchase Order"]
                    item["Customer Name"] = data["Customer Name"]
                    data["Items"].append(item)
                    print(f"Captured item: {item}")

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
