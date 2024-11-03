from flask import Flask, request, render_template, jsonify
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
from flask_cors import CORS  # Add this import

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle PDF upload and extraction
@app.route('/extract', methods=['POST'])
def extract_data():
    if 'pdf_file' not in request.files:
        return jsonify({"Status": False, "Message": "No file part in the request"}), 400
    
    file = request.files['pdf_file']

    if file.filename == '':
        return jsonify({"Status": False, "Message": "No file selected"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            pdf_document = file.read()
            pdf_data = extract_from_pdf(pdf_document)
            return jsonify(pdf_data)
        except Exception as e:
            return jsonify({"Status": False, "Message": f"Error processing PDF: {str(e)}"}), 500
    else:
        return jsonify({"Status": False, "Message": "Invalid file format"}), 400

def extract_from_pdf(pdf_data):
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    
    extracted_data = {
        "Status": True,
        "data": {
            "text": "",
            "images": [],
            "extracted_info": {}  # Add this to store structured info
        },
        "Message": "PDF extracted successfully."
    }

    # Extract text and images from each page
    for page_num in range(doc.page_count):
        page = doc[page_num]
        extracted_data["data"]["text"] += page.get_text("text")

        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Convert image to base64 string for JSON response
            image = Image.open(io.BytesIO(image_bytes))
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            extracted_data["data"]["images"].append(f"data:image/png;base64,{img_str}")

    # Add structured info extraction
    text = extracted_data["data"]["text"]
    extracted_data["data"]["extracted_info"] = extract_key_value_pairs(text)

    doc.close()
    return extracted_data

def extract_key_value_pairs(text):
    # Import the patterns from your extract_pdf_data.py
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
        "Education": r"Education\n(.+?)\n"
    }
    
    extracted_data = {}
    import re
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            extracted_data[key] = match.group(1).strip()
        else:
            extracted_data[key] = None
            
    return extracted_data

if __name__ == '__main__':
    app.run(debug=True, port=5000)