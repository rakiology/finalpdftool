import fitz  # PyMuPDF
from PIL import Image
import io
import json
import re
from datetime import datetime
import os

# Base URL for accessing images (modify this to your server's base path)
BASE_URL = "http://localhost/output_images"  # Change this to your actual server URL

def extract_text_from_pdf(pdf_path):
    """Extract text content from PDF file."""
    with fitz.open(pdf_path) as pdf:
        text = ""
        for page in pdf:
            text += page.get_text()
        return text

def extract_images_from_pdf(pdf_path):
    """Extract images from PDF and save them to 'output_images' directory."""
    images = []
    output_dir = "output_images"
    os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist

    with fitz.open(pdf_path) as pdf:
        for page_num in range(len(pdf)):
            for img_index, img in enumerate(pdf.get_page_images(page_num)):
                xref = img[0]
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Save images in the output directory with specific filenames
                image_name = f"image{img_index + 1}.{image_ext}"
                image_path = os.path.join(output_dir, image_name)
                image = Image.open(io.BytesIO(image_bytes))
                image.save(image_path)
                
                # Add the full URL for the image
                image_url = f"{BASE_URL}/{image_name}"
                images.append(image_url)

    return images[:2]  # Return only the first two image URLs (photo and signature)

def format_address():
    """Format address in two different styles using default values."""
    # Default address values
    components = {
        'home': 'মিয়াজী বাড়ী',
        'village': 'মুরগাও',
        'post_office': 'জোড়ডা বাজার',
        'postal_code': '3582',
        'upazila': 'নাঙ্গলকোট',
        'district': 'কুমিল্লা'
    }

    # Format first address style
    address = (
        f"বাসা/হোল্ডিং:{components['home']}, "
        f"গ্রাম/রাস্তা: {components['village']}, "
        f"ডাকঘর: {components['post_office']} , "
        f"পোষ্ট কোড: {components['postal_code']}, "
        f"উপজেলা: {components['upazila']} , "
        f"জেলা: {components['district']}"
    )

    # Format second address style
    address_new = (
        f"বাসা/হোল্ডিং :{components['home']}, "
        f"গ্রাম/রাস্তা : {components['village']}, "
        f"ডাকঘর : {components['post_office']} - {components['postal_code']}, "
        f"{components['upazila']} , {components['district']}"
    )

    return address, address_new

def extract_key_value_pairs(text):
    """Extract specific information using improved regular expressions."""
    patterns = {
        "nid_number": r"National ID\n(.+?)\n",
        "pin": r"Pin\n(.+?)\n",
        "name_bn": r"Name\(Bangla\)\n(.+?)\n",
        "name_en": r"Name\(English\)\n(.+?)\n",
        "date_of_birth": r"Date of Birth\n(.+?)\n",
        "date_of_place": r"Birth Place\n(.+?)\n",
        "father_n": r"Father Name\n(.+?)\n",
        "mother_n": r"Mother Name\n(.+?)\n",
        "address_present": r"Present Address\n(.+?)\n",
        "address_permanent": r"Permanent Address\n(.+?)\n",
        "blood_group": r"Blood Group\n(.+?)\n(?:TIN|$)",
    }

    extracted_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        extracted_data[key] = match.group(1).strip() if match else ""
    return extracted_data

def process_pdf(pdf_path):
    """Process PDF and return data in specified format."""
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        
        # Extract specific information using refined patterns
        info = extract_key_value_pairs(text)
        
        # Extract and save images with URLs
        images = extract_images_from_pdf(pdf_path)
        photo_url = images[0] if len(images) > 0 else f"{BASE_URL}/image1.png"
        sign_url = images[1] if len(images) > 1 else f"{BASE_URL}/image2.png"

        # Format addresses
        address, address_new = format_address()  # Defaults for Bengali formatting

        # Prepare response
        response = {
            "Status": True,
            "data": {
                "nid_number": info.get('nid_number', "1924704057"),
                "pin": info.get('pin', "19681918751038887"),
                "name_bn": info.get('name_bn', "জয়নাল আবদীন"),
                "name_en": info.get('name_en', "Joynal Abden"),
                "date_of_birth": info.get('date_of_birth', "1968-05-06"),
                "date_of_place": info.get('date_of_place', "কুমিল্লা"),
                "father_n": info.get('father_n', "আমান উল্যা"),
                "mother_n": info.get('mother_n', "আতরের নেছা"),
                "blood_group": info.get('blood_group', ""),
                "address": address,
                "address_new": address_new,
                "photo": photo_url,
                "sign": sign_url
            },
            "Message": "PDF extracted successfully."
        }

        return response

    except Exception as e:
        return {
            "Status": False,
            "data": {},
            "Message": f"Error processing PDF: {str(e)}"
        }

if __name__ == "__main__":
    # Example usage
    pdf_path = "input.pdf"
    result = process_pdf(pdf_path)

    # Save output to JSON file
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print("PDF processing complete. Results saved to output.json")
