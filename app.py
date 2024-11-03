from flask import Flask, request, jsonify, render_template_string, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
from extract_pdf_data import process_pdf

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf'}

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF Data Extractor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            text-align: center;
        }
        #result {
            margin-top: 20px;
            white-space: pre-wrap;
            text-align: left;
        }
        .loading {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>PDF Data Extractor</h1>
        <div class="upload-section">
            <form id="uploadForm">
                <input type="file" id="pdfFile" accept=".pdf" required>
                <button type="submit">Extract Data</button>
            </form>
            <div class="loading">Processing...</div>
        </div>
        <div id="result"></div>
    </div>

    <script>
        const form = document.getElementById('uploadForm');
        const loading = document.querySelector('.loading');
        const result = document.getElementById('result');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('pdfFile');
            const file = fileInput.files[0];

            if (!file) {
                alert('Please select a PDF file');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            loading.style.display = 'block';
            result.textContent = '';

            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                result.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                result.textContent = 'Error processing PDF: ' + error.message;
            } finally {
                loading.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract', methods=['POST'])
def extract_pdf_data():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({
            "Status": False,
            "data": {},
            "Message": "No file uploaded"
        }), 400
    
    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({
            "Status": False,
            "data": {},
            "Message": "No file selected"
        }), 400
    
    if file and allowed_file(file.filename):
        try:
            # Generate a unique filename
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the uploaded file
            file.save(filepath)
            
            # Process the PDF
            result = process_pdf(filepath)
            
            # Clean up - delete the uploaded file
            os.remove(filepath)
            
            # Handle any extracted images in the uploads folder
            for file in os.listdir(app.config['UPLOAD_FOLDER']):
                if file.startswith('extracted_image'):
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
                    except:
                        pass
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                "Status": False,
                "data": {},
                "Message": f"Error processing PDF: {str(e)}"
            }), 500
    
    return jsonify({
        "Status": False,
        "data": {},
        "Message": "Invalid file type. Only PDF files are allowed."
    }), 400

@app.route('/extract', methods=['OPTIONS'])
def handle_options():
    response = app.make_default_options_response()
    add_cors_headers(response)
    return response

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
