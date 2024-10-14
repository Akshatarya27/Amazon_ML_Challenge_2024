import streamlit as st
from PIL import Image
import requests
import os
from io import BytesIO
import pytesseract 
import cv2
# from extract_units import process_image, process_image_from_url  # Import functions

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Preprocessing and OCR configurations
custom_config = r'--oem 3 --psm 6'

# Entity unit map (as per your provided dictionary)
entity_unit_map = {
    'width': {'centimetre', 'foot', 'inch', 'metre', 'millimetre', 'yard'},
    'depth': {'centimetre', 'foot', 'inch', 'metre', 'millimetre', 'yard'},
    'height': {'centimetre', 'foot', 'inch', 'metre', 'millimetre', 'yard'},
    'item_weight': {'gram', 'kilogram', 'microgram', 'milligram', 'ounce', 'pound', 'ton'},
    'maximum_weight_recommendation': {'gram', 'kilogram', 'microgram', 'milligram', 'ounce', 'pound', 'ton'},
    'voltage': {'kilovolt', 'millivolt', 'volt'},
    'wattage': {'kilowatt', 'watt'},
    'item_volume': {'centilitre', 'cubic foot', 'cubic inch', 'cup', 'decilitre', 'fluid ounce', 'gallon', 'imperial gallon', 'litre', 'microlitre', 'millilitre', 'pint', 'quart'}
}

def expand_units(units):
    expanded_units = {}
    for unit in units:
        if unit == 'pound':
            expanded_units.update({'lb': 'pound', 'lbs': 'pound', 'pound': 'pound'})
        elif unit == 'ounce':
            expanded_units.update({'oz': 'ounce', 'ounce': 'ounce'})
        elif unit == 'gram':
            expanded_units.update({'g': 'gram', 'gram': 'gram'})
        elif unit == 'kilogram':
            expanded_units.update({'kg': 'kilogram', 'kilogram': 'kilogram'})
        elif unit == 'ton':
            expanded_units.update({'ton': 'ton', 'tons': 'ton'})
        elif unit == 'milligram':
            expanded_units.update({'mg': 'milligram', 'milligram': 'milligram'})
        elif unit == 'microgram':
            expanded_units.update({'mcg': 'microgram', 'microgram': 'microgram'})
        elif unit == 'volt':
            expanded_units.update({'v': 'volt', 'volt': 'volt'})
        elif unit == 'kilovolt':
            expanded_units.update({'kv': 'kilovolt', 'kilovolt': 'kilovolt'})
        elif unit == 'watt':
            expanded_units.update({'w': 'watt', 'watt': 'watt'})
        elif unit == 'kilowatt':
            expanded_units.update({'kw': 'kilowatt', 'kilowatt': 'kilowatt'})
        elif unit == 'litre':
            expanded_units.update({'l': 'litre', 'liter': 'litre', 'litre': 'litre'})
        elif unit == 'millilitre':
            expanded_units.update({'ml': 'millilitre', 'milliliter': 'millilitre', 'millilitre': 'millilitre'})
        elif unit == 'centilitre':
            expanded_units.update({'cl': 'centilitre', 'centiliter': 'centilitre', 'centilitre': 'centilitre'})
        elif unit == 'cubic foot':
            expanded_units.update({'ft³': 'cubic foot', 'cubic foot': 'cubic foot'})
        elif unit == 'cubic inch':
            expanded_units.update({'in³': 'cubic inch', 'cubic inch': 'cubic inch'})
        elif unit == 'cup':
            expanded_units.update({'cup': 'cup'})
        elif unit == 'decilitre':
            expanded_units.update({'dl': 'decilitre', 'deciliter': 'decilitre', 'decilitre': 'decilitre'})
        elif unit == 'fluid ounce':
            expanded_units.update({'fl oz': 'fluid ounce', 'fluid ounce': 'fluid ounce'})
        elif unit == 'gallon':
            expanded_units.update({'gal': 'gallon', 'gallon': 'gallon'})
        elif unit == 'imperial gallon':
            expanded_units.update({'imperial gal': 'imperial gallon', 'imperial gallon': 'imperial gallon'})
        elif unit == 'pint':
            expanded_units.update({'pint': 'pint'})
        elif unit == 'quart':
            expanded_units.update({'qt': 'quart', 'quart': 'quart'})
        elif unit == 'foot':
            expanded_units.update({'ft': 'foot', 'foot': 'foot'})
        elif unit == 'inch':
            expanded_units.update({'in': 'inch', 'inch': 'inch'})
        elif unit == 'metre':
            expanded_units.update({'m': 'metre', 'meter': 'metre', 'metre': 'metre'})
        elif unit == 'millimetre':
            expanded_units.update({'mm': 'millimetre', 'millimeter': 'millimetre', 'millimetre': 'millimetre'})
        elif unit == 'yard':
            expanded_units.update({'yd': 'yard', 'yard': 'yard'})
        else:
            expanded_units[unit] = unit
    return expanded_units

# Helper function to extract relevant units from text
def extract_units(text, key, entity_unit_map):
    if key not in entity_unit_map:
        return f"Key '{key}' not found in entity_unit_map."

    units = entity_unit_map[key]
    expanded_units = expand_units(units)

    # Create regex pattern to match a number followed by a unit
    units_pattern = '|'.join(re.escape(unit) for unit in expanded_units.keys())
    pattern = rf'(\d+(\.\d+)?)\s*({units_pattern})'
    
    # Find all matches
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    extracted_results = []
    for match in matches:
        number = match[0]  # The number part (e.g., 2.31)
        unit = match[2].lower()  # The unit part (e.g., lb)
        base_unit = expanded_units[unit]  # Map to base unit (e.g., pound)
        extracted_results.append(f"{number} {base_unit}")
    
    return extracted_results

def process_image(image_path, entity_name):
    # Open the image using OpenCV
    img = cv2.imread(image_path)

    # Convert to grayscale
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply thresholding for better contrast
    thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Extract text using pytesseract
    text = pytesseract.image_to_string(thresh_img, config='--oem 3 --psm 6')

    # Clean the extracted text
    cleaned_text = text.replace('”', '"').strip().replace('\n\n', '\n')

    # Extract relevant units from the text
    result = extract_units(cleaned_text, entity_name, entity_unit_map)

    return result if result else ""

def process_image_from_url(image_path, entity_name):
    # Open the image using OpenCV
    img = cv2.imread(image_path)

    # Convert to grayscale
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply thresholding for better contrast
    thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Extract text using pytesseract
    text = pytesseract.image_to_string(thresh_img, config='--oem 3 --psm 6')

    # Clean the extracted text
    cleaned_text = text.replace('”', '"').strip().replace('\n\n', '\n')

    # Extract relevant units from the text
    result = extract_units(cleaned_text, entity_name, entity_unit_map)

    return result if result else ""




st.title("Tesseract Image Classification")

# Option to choose input method
input_method = st.radio("Choose input method:", ["Upload an image", "Enter an image URL"])

uploaded_file = None
image_url = None

# Handle image upload or URL input
if input_method == "Upload an image":
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])
elif input_method == "Enter an image URL":
    image_url = st.text_input("Enter an image URL")

# Key selection (single select)
key = st.selectbox("Select a key for classification:", ["width", "depth", "height", "item_weight", "maximum_weight_recommendation", "voltage", "wattage", "item_volume"])

# Process and display results
if input_method == "Upload an image" and uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # Save uploaded file to a temporary location for processing
    temp_image_path = os.path.join("temp_uploaded_image.jpg")
    image.save(temp_image_path)

    if st.button("Classify"):
        result = process_image(temp_image_path, key)
        st.write(f"Classification Result: {result}")

elif input_method == "Enter an image URL" and image_url:
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        # Display the image from the URL on the Streamlit app
        st.image(image, caption="Image from URL", use_column_width=True)
    except Exception as e:
        st.error(f"Error loading image from URL: {e}")
    if st.button("Classify"):
        result = process_image_from_url(image_url, key)
        st.write(f"Classification Result: {result}")
