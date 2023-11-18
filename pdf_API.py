
import tabula#!pip install tabula-py

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

# new imports
import language_tool_python
from spellchecker import SpellChecker
import markdown


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
    result =  get_stats_of_file(curr_file_path= f"{current_directory}\\{name}")
    print(result)
    return json.dumps(result)



def get_stats_of_file(curr_file_path = '/Users/kodali.praveen/Desktop/slashnext_doc.pdf'):
    pdf_file_path = curr_file_path
    pdf_document = fitz.open(curr_file_path)

    total_words = 0
    headings = 0
    sub_headings = 0
    text_sizes = []
    langs = []
    image_count = 0
    pdf_metadata = {}
    grammar_flag = False
    spelling_mistakes_flag = False
    reference_flag = False
    can_be_converted_to_html_flag = False

    pdf_len = len(pdf_document)
    references_list = [pdf_len-1, pdf_len-2, pdf_len-3]

    image_first_last_flag = False
    image_first_last_list = [0, pdf_len-1]

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        page_text = page.get_text()

        try:
            grammar_errors = grammar_check(page_text)
            if grammar_errors:
                grammar_flag = True
        except:
            pass
    
        try:
            spelling_corrections = spell_check(page_text)
            if spelling_corrections:
                spelling_mistakes_flag = True
        except:
            pass
    
        try:
            if page_num in references_list:
                if "reference" in page_text.lower():
                    reference_flag = True
        except:
            pass
    
        try:
            if validate_markdown(input_markdown):
                can_be_converted_to_html_flag = True
        except:
            pass
    
    
        try:
            langs.append(detect(page_text.strip()[:100]))
        except:
            pass

        hdgs = re.findall(r'\b([A-Z\d]+:)', page_text, re.I)
        hdgs_result = [h.strip() for h in hdgs]
        headings += len(hdgs_result)

        sub_hdgs = re.findall(r'([a-z]+:)', page_text, re.I)
        sub_headings += len(sub_hdgs)

        # Extract font sizes from the page
        for block in page_text.split('\n'):
            for span in block.split(' '):
                if span.strip().isdigit():
                    text_sizes.append(int(span.strip()))

        # Count images in the page
        image_list = page.get_images(full=True)
        image_count += len(image_list)

        # Count total words
        total_words += len(page_text.split())

        # checking for the image in the first and last pages
        try:
            if page_num in image_first_last_list:
                image_list = page.get_images(full=True)
                if image_list:
                    image_first_last_flag = True
        except:
            pass

    # change - 1
    # pdf_document.close()

    # pdf metadata also need to update or TODO
    pdf_metadata['Title'] = "Pdf Document"
    pdf_metadata['page_num'] = len(pdf_document)
    pdf_metadata['created_time'] = "2023"

    ### picking text size dominating one
    final_text_sizes = []
    for sz in text_sizes:
        if sz in [10,11,12,13,14,15,16,17,18,19,20]:
            final_text_sizes.append(sz)

    text_sizes_count = {}
    for elem in final_text_sizes:
        if elem not in text_sizes_count:
            text_sizes_count[elem] = 1
        else:
            already_count = text_sizes_count[elem]
            text_sizes_count[elem] = already_count+1

    Keymax = None
    if text_sizes_count:
        Keymax = max(zip(text_sizes_count.values(), text_sizes_count.keys()))[1]

    result = {}
    result["total_words"] = str(total_words) if total_words != 0 else 'NA'
    result["languages"] = str(set(langs))
    result["Is_english_present"] = "en" in langs
    result["total_headings"] = str(headings) if total_words != 0 else 'NA'
    result["total_subheadings"] = str(sub_headings) if total_words != 0 else 'NA'
    result["text_sizes"] = Keymax if Keymax else 'NA'
    result["total_images_count"] = str(image_count)
    result["Font_color_majority"] = "Black" if total_words != 0 else 'NA'

    # Count the number of tables in the PDF
    table_count = get_table_count(curr_file_path)
    result["total_tables"] = str(table_count)


    #changes 2
    suggestions = []

    if grammar_flag:
        suggestions.append('There are grammatical mistake(s) in this PDF Document')
    else:
        suggestions.append('There are no grammatical mistake(s) in this PDF Document')

    if spelling_mistakes_flag:
        suggestions.append('There are spelling mistake(s) in this PDF')
    else:
        suggestions.append('There are no spelling mistake(s) in this PDF')

    if reference_flag:
        suggestions.append("Reference(s) are mentioned.")
    else:
        suggestions.append("Reference(s) are not mentioned and is good to provide some references.")

    if Keymax:
        if Keymax in [12,13,14,15]:
            suggestions.append('Font size used in the Document is good and recommmended.')
        else:
            suggestions.append('Font size used is not recommmended.')

    if image_first_last_flag:
        suggestions.append("Images format in this Document are not recommmended.")
    elif image_count:
        suggestions.append("Images attached in this Document are recommmended.")
    else:
        suggestions.append("It is better to add some images wherever applicable.")


    if can_be_converted_to_html_flag:
        suggestions.append("Some page(s) text in this pdf can be converted to HTML.")
    else:
        suggestions.append("No page(s) text in this PDF can be converted to HTML and properly formatted for pdf.")


    if pdf_len == image_count:
        suggestions.append("All the pages are having images mostly and is not recommmended.")
    else:
        suggestions.append("Decent number of images are used in this Document and the usage is recommmended")


    pdf_metadata = get_pdf_metadata(pdf_file_path)
    suggestions.append(pdf_metadata)

    # print(suggestions)
    result["text_sizes"] = str(suggestions)
    return result



def get_table_count(pdf_path):
    """Counts the number of tables in a PDF file.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        The number of tables in the PDF file.
    """
    try:
        # Read the PDF file and extract all of the tables using tabula
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        return len(tables)
    except Exception as e:
        return 0


def grammar_check(text):
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    return matches


def spell_check(text):
    spell = SpellChecker()
    # Split the text into words
    words = text.split()

    # Find misspelled words
    misspelled = spell.unknown(words)

    # Get suggestions for misspelled words
    corrections = {word: spell.correction(word) for word in misspelled}

    return corrections


# Checking whether a page text of document can be converted to HTML or not
def validate_markdown(text):
    try:
        # Try to convert the text to HTML using the markdown library
        markdown.markdown(text)
        return True
    except:
        return False

# Fetches the pdf metadata
def get_pdf_metadata(pdf_path):
    metadata = {}
    try:
        with fitz.open(pdf_path) as pdf_document:
            metadata['Title'] = pdf_document.metadata.get('title', 'N/A')
            metadata['Author'] = pdf_document.metadata.get('author', 'N/A')
            metadata['Subject'] = pdf_document.metadata.get('subject', 'N/A')
            metadata['Creator'] = pdf_document.metadata.get('creator', 'N/A')
            metadata['Producer'] = pdf_document.metadata.get('producer', 'N/A')
            metadata['Creation Date'] = pdf_document.metadata.get('creationDate', 'N/A')
            metadata['Modification Date'] = pdf_document.metadata.get('modDate', 'N/A')
            metadata['Number of Pages'] = pdf_document.page_count
    except Exception as e:
        print(f"Error: {e}")

    return metadata



# Get the path to the PDF file
# pdf_path = "/content/ACFrOgCnVFkjnidLiOabke2j-sdMa5NsWPD_kUASChfblcqOzP94T-04ABxGAxHi7WFqeAnCEj3IYwh3ffEnUPxa_bKhwCgrvp5ANj1sp_O8dEruLh7cbRFgx7IFEa12nKcgDGEWHkLkCYGq7ZbSsMNCgkdYreYNzRe-kS2A2g==.pdf"

# Call the modified function to get the stats
# result = get_stats_of_file(pdf_path)

# Print the results
# print(result)

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=5000)
