import streamlit as st
import os
import base64
from mistralai import Mistral
from pdf2image import convert_from_bytes
from io import BytesIO

st.set_page_config(layout="wide", page_title="Mistral OCR App", page_icon="🖥️")
st.title("Get accurate and perfect results from your pdf")
#st.markdown("<h3 style color: white;'>Built by <a href='https://github.com/AIAnytime'>AI Anytime with ❤️ </a></h3>", unsafe_allow_html=True)

# 1. API Key Input
api_key ="h98KHKhrGdjHWi2pOwz46F7bWUMwWWk7"
if not api_key:
    st.info("Please enter your API key to continue.")
    st.stop()

# Initialize session state
if "ocr_result" not in st.session_state:
    st.session_state["ocr_result"] = None
if "preview_src" not in st.session_state:
    st.session_state["preview_src"] = None
if "image_bytes" not in st.session_state:
    st.session_state["image_bytes"] = []

# 2. Choose file type
file_type = st.radio("Select file type", ("PDF", "Image"))

# 3. Select source type
source_type = st.radio("Select source type", ("URL", "Local Upload"))

input_url = ""
uploaded_file = None

if source_type == "URL":
    input_url = st.text_input("Enter File URL")
else:
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "jpg", "jpeg", "png"])

# 4. Process Button & OCR Handling
if st.button("Process"):
    if source_type == "URL" and not input_url:
        st.error("Please enter a valid URL.")
    elif source_type == "Local Upload" and not uploaded_file:
        st.error("Please upload a file.")
    else:
        client = Mistral(api_key=api_key)
        
        if file_type == "PDF":
            # Convert PDF to Images
            file_bytes = uploaded_file.read()
            images = convert_from_bytes(file_bytes, fmt="jpeg")
            
            ocr_results = []
            image_previews = []

            for i, image in enumerate(images):
                # Convert image to base64
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

                # Prepare OCR request
                document = {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{img_str}"
                }
                
                # Send to Mistral OCR
                with st.spinner(f"Processing page {i+1}..."):
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document=document,
                        include_image_base64=True
                    )

                    try:
                        if hasattr(ocr_response, "pages"):
                            pages = ocr_response.pages
                        elif isinstance(ocr_response, list):
                            pages = ocr_response
                        else:
                            pages = []
                        result_text = "\n\n".join(page.markdown for page in pages) if pages else "No text found."
                    except Exception as e:
                        result_text = f"Error: {e}"

                    ocr_results.append(f"Page {i+1}:\n{result_text}")
                    image_previews.append(image)

            # Store results
            st.session_state["ocr_result"] = "\n\n".join(ocr_results)
            st.session_state["image_bytes"] = image_previews

# 5. Display Preview and OCR Result if available
if st.session_state["ocr_result"]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Extracted Images")
        for img in st.session_state["image_bytes"]:
            st.image(img)

    with col2:
        st.subheader("OCR Result")
        st.write(st.session_state["ocr_result"])
        
        # Create a download link
        b64 = base64.b64encode(st.session_state["ocr_result"].encode()).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="ocr_result.txt">Download OCR Result</a>'
        st.markdown(href, unsafe_allow_html=True)
