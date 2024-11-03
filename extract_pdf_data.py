import fitz  # PyMuPDF
from PIL import Image
import io
import json
import re

def extract_text_from_pdf(pdf_path):
    with fitz.open(pdf_path) as pdf:
        text = ""
        for page in pdf:
            text += page.get_text()
        return text

def extract_images_from_pdf(pdf_path):
    images = []
    with fitz.open(pdf_path) as pdf:
        for page_num in range(len(pdf)):
            for img_index, img in enumerate(pdf.get_page_images(page_num), start=1):
                xref = img[0]
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                image = Image.open(io.BytesIO(image_bytes))
                image_path = f"extracted_image_page{page_num + 1}_{img_index}.{image_ext}"
                image.save(image_path)
                
                images.append({
                    "page": page_num + 1,
                    "image_index": img_index,
                    "image_path": image_path
                })
    return images

def extract_key_value_pairs(text):
    patterns = {
        "nid_number": r"National ID\n(.+?)\n",
        "nid_pin": r"Pin\n(.+?)\n",
        "name_bn": r"Name\(Bangla\)\n(.+?)\n",
        "name_en": r"Name\(English\)\n(.+?)\n",
        "date_of_birth": r"Date of Birth\n(.+?)\n",
        "date_of_place": r"Birth Place\n(.+?)\n",
        "father_n": r"Father Name\n(.+?)\n",
        "mother_n": r"Mother Name\n(.+?)\n",
        "Present Address": r"Present Address\n(.+?)\n",
        "Permanent Address": r"Permanent Address\n(.+?)\n",
        "blood_group": r"Blood Group\n(.+?)\n(?:TIN|$)",
        "Phone": r"Phone\n(.+?)\n",
        "Education": r"Education\n(.+?)\n",
        "Division": r"Division\n(.+?)\n",
        "District": r"District\n(.+?)(?=RMO|$)",
        "RMO": r"RMO\n(.+?)(?=City|$)",
        "Municipality": r"Municipality\n(.+?)(?=Upozila|$)",
        "Upozila": r"Upozila\n(.+?)(?=Union|$)",
        "Union/Ward": r"Union/Ward\n(.+?)(?=Mouza/Moholla|$)",
        "Mouza/Moholla": r"Mouza/Moholla\n(.+?)\n(?:Additional|$)",
        "Additional": r"Additional\n(.+?)\n(?:Ward|$)",
        "Ward For": r"Ward For\n(.+?)\n(?:Village/Road|$)",
        "Village/Road": r"Village/Road\n(.+?)\n(?:Additional|$)",
        "homeOrHoldingNo": r"Home/Holding\n(.+?)\n(?:Post Office|$)",
        "Post Office": r"Post Office\n(.+?)\n(?:Postal Code|$)",
        "Postal Code": r"Postal Code\n(.+?)\n(?:Region|$)",
        "Region": r"Region\n(.+?)\n(?:Permanent Address|$)"
    }
    
    extracted_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            extracted_data[key] = match.group(1).strip()
        else:
            extracted_data[key] = None
            
    return extracted_data

def process_pdf(pdf_path):
    # Extract text
    text_data = extract_text_from_pdf(pdf_path)
    
    # Extract key-value pairs
    extracted_info = extract_key_value_pairs(text_data)
    
    # Extract images
    image_data = extract_images_from_pdf(pdf_path)
    
    # Combine all data
    output_data = {
        "extracted_info": extracted_info,
        "images": image_data
    }
    
    return output_data

if __name__ == "__main__":
    # Specify PDF file path
    pdf_path = "file.pdf"
    
    # Process PDF and get structured data
    output_data = process_pdf(pdf_path)
    
    # Save to JSON file
    with open("extracted_pdf_data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    
    print("Data extraction complete. Information saved in 'extracted_pdf_data.json'")