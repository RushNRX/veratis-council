import os
import time
import requests
import fitz  # PyMuPDF
import json
import base64
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file in parent directory
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path)

# Now you can access the GOOGLE_API_KEY
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

def download_pdf(url):
    # Create 'downloaded_files' directory if it doesn't exist
    if not os.path.exists('downloaded_files'):
        os.makedirs('downloaded_files')

    # Generate timestamp
    timestamp = int(time.time())

    # Construct filename
    filename = f"latest_guidance{timestamp}.pdf"
    filepath = os.path.join('downloaded_files', filename)

    # Download the PDF
    response = requests.get(url)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"PDF downloaded and saved as {filepath}")
        return filepath
    else:
        print("Failed to download PDF")
        return None

def extract_pdf_to_images(pdf_path):
    # Open the PDF
    doc = fitz.open(pdf_path)

    # Get the timestamp from the PDF filename
    timestamp = os.path.basename(pdf_path).split('.')[0].split('latest_guidance')[1]

    # Create directory for images if it doesn't exist
    image_dir = 'downloaded_files'
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # List to store image paths
    image_paths = []

    # Iterate through each page
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Set the zoom factor for higher quality
        zoom = 2  # Increase this for even higher quality, but larger file size
        mat = fitz.Matrix(zoom, zoom)
        
        # Render page to an image with higher resolution
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Construct image filename
        image_filename = f"{page_num+1}_latest_guidance_{timestamp}.png"
        image_path = os.path.join(image_dir, image_filename)
        
        # Save the image
        pix.save(image_path)
        print(f"Saved image: {image_path}")
        
        # Add image path to the list
        image_paths.append(image_path)

    # Close the document
    doc.close()

    return image_paths

def extractTextFromImage(image_paths):
    # Initialize the Gemini model with the API key
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=GOOGLE_API_KEY)

    # List to store extracted text for each page
    extracted_text = []

    for i, image_path in enumerate(image_paths):
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        # Create a message with the image
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Read out what's in this page accurately - YOU MUST ONLY READ THE TEXT, DO NOT TALK ABOUT ANYTHING ELSE SUCH AS THE PAGE COLOUR IF YOU CAN'T FIND ANY TEXT JUST SAY 'NULL', do not include additional commentary"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_data}"},
                },
            ],
        )

        # Invoke the model with the message
        response = model.invoke([message])

        # Add the extracted text to the list
        extracted_text.append({
            "page": i + 1,
            "content": response.content
        })

    # Create a single JSON with all extracted text
    json_output = json.dumps(extracted_text, indent=2)

    # Create 'extracted_data' directory if it doesn't exist
    if not os.path.exists('extracted_data'):
        os.makedirs('extracted_data')

    # Save the JSON to a file in the 'extracted_data' directory
    json_path = os.path.join('extracted_data', 'extracted_text.json')
    with open(json_path, 'w') as json_file:
        json_file.write(json_output)

    print(f"Extracted text saved to {json_path}")

if __name__ == "__main__":
    pdf_url = "https://drive.usercontent.google.com/download?id=1SvRIU3ON4FFUu-Dp0AOmerFs_xcQg7t-&export=download&authuser=0"  
    pdf_path = download_pdf(pdf_url)
    if pdf_path:
        image_paths = extract_pdf_to_images(pdf_path)
        extractTextFromImage(image_paths)