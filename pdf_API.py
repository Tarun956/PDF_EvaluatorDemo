from fastapi import FastAPI, UploadFile, File
from PyPDF2 import PdfFileReader
from PyPDF2 import PdfReader
import re
from langdetect import detect
from pdf2image import convert_from_path
from io import BytesIO
import fitz
import os
import uvicorn
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # You can specify specific HTTP methods
    allow_headers=["*"],  # You can specify specific headers
)


@app.get("/get_stat/")
def get_stats_of_files(name: str):
    current_directory = os.getcwd()
    result =  get_stats_of_file(curr_file_path= f"{current_directory}/{name}")
    print(result)
    return json.dumps(result)


@app.post("/get_stats")
def get_stats_of_file(name: str):

    # Get the name of the uploaded PDF file
    pdf_file_name = pdf_stats.filename
    
    # You can now use pdf_file_name as needed
    

    current_directory = os.getcwd()
    print("Current Folder Path:", current_directory)
    result = {"file_name": f"{current_directory}\\{name}"}

    print(result)


    result =  get_stats_of_file(curr_file_path= f"{current_directory}\\{name}")
    
    # return json.loads(f"{result}")

    # result = await get_stats_of_file(curr_file_path= f"{current_directory}\\{pdf_file_name}")
    
    return json.dumps(result)


def get_stats_of_file(curr_file_path="C:\\Users\\adity\\Desktop\\Doc1.pdf"):
    curr_file_path = curr_file_path
    # curr_file_path = '/Users/kodali.praveen/Desktop/Doc1.pdf'
    pdf_file = open(curr_file_path, 'rb')

    # Create a PDF reader object
    pdf_reader = PdfReader(pdf_file)

    # Initialize variables to store data
    total_words = 0
    headings = 0
    sub_headings = 0
    text_sizes = []
    langs = []
    image_count = 0

    # Open the PDF file with PyMuPDF (Fitz)
    # pdf_document = fitz.open('/Users/kodali.praveen/Desktop/slashnext_doc.pdf')
    pdf_document = fitz.open(curr_file_path)

    heading_pattern = re.compile(r' [\dA-Z]+:')

    # heading_pattern = re.compile(r'\b\w+:\w+\b')

    pattern = r'[a-z]:'

    hdgs_result = []
    # Iterate through pages and extract text
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        page_text = page.extract_text()

        # print(page_text)
        try:
            langs.append(detect(page_text.strip()[:100]))
        except:
            pass

        hdgs = re.findall(" (.+)\:\b", page_text, re.I)
        final_hdgs = [h.strip() for h in hdgs]
        hdgs_result.extend(final_hdgs)
        total_words += len(page_text.split())

        for line in page_text.split('\n'):
            matches = re.findall(pattern, line)

            sub_headings += len(matches)

        # Increment the heading count
        # headings += len(matches)

        # Count images using PyMuPDF
        page_fitz = pdf_document[page_num]
        image_list = page_fitz.get_images(full=True)
        image_count += len(image_list)

    # Close the PDF file
    pdf_file.close()

    # Close the PDF document opened with PyMuPDF
    pdf_document.close()

    # Print the results
    print("Total Words:", total_words)
    print("Total Headings:", headings)
    print("Total Sub Headings:", sub_headings)
    print("Text Sizes:", text_sizes) # Implement text size analysis logic
    print("Total Images:", image_count)
    print(hdgs_result)
    print("Language : ", set(langs))

    result = {}
    result["total_words"] = str(total_words)
    result["languages"] = str(set(langs)),
    result["Is_english_present"] = True if "en" in langs else False
    result["total_headings"] = str(headings)
    result["total_images_count"] = str(image_count)
    result["Summary"] = "#TODO - Can handle for Articles"
    result["Font_color_majority"] = "Black"

    return result



if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=5000)
