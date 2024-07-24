# -*- coding: utf-8 -*-
"""smilebot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nqLMKB4iGhsSiCR8wEJLn-rSmHeRq-Sh
"""

!pip install -U google-generativeai langchain langchain_community pypdf PyPDF2 requests beautifulsoup4 pandas
!pip install google-generativeai

# Import Libraries and Set Up Environment Variables
import os
from google.colab import userdata
from google.generativeai import GenerativeModel
from langchain.chains import RetrievalQA
from langchain.vectorstores import Pinecone
from langchain.prompts import PromptTemplate
from langchain.document_loaders import PyPDFLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import requests
from bs4 import BeautifulSoup
import pandas as pd

!pip install pinecone-client

# Import Libraries and Set Up Environment Variables
from pinecone import Pinecone, ServerlessSpec
import os
from google.colab import userdata

# Retrieve Pinecone API key from Google Colab's userdata
api = userdata.get('d7e58e8e-b0a1-408d-9ce0-811372bc3033')
# Replace 'your-api-key' with your actual Pinecone API key
os.environ["d7e58e8e-b0a1-408d-9ce0-811372bc3033"] = api  # Set Pinecone API key as an environment variable

from google.generativeai import GenerativeModel
!pip install --upgrade google-generativeai

from google.generativeai import configure

# Retrieve Gemini API key from Google Colab's userdata
GEMINI_API_KEY = userdata.get('AIzaSyB-3SICe5or9W7Dv3X0-8yaZqS1ForMd0k')
# Configure the Gemini API
configure(api_key=GEMINI_API_KEY)  # configure the API

os.environ["AIzaSyB-3SICe5or9W7Dv3X0-8yaZqS1ForMd0k"] = GEMINI_API_KEY

import google.generativeai as genai
from langchain.embeddings import GooglePalmEmbeddings
from langchain.chat_models import ChatGooglePalm

# Initialize Google PaLM Embeddings
embeddings = GooglePalmEmbeddings()

# Initialize ChatGooglePalm model
chat_model = ChatGooglePalm(temperature=0.7, google_api_key=GEMINI_API_KEY)

# Initialize Prompt and Parser
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
''
# Create a string output parser
parser = StrOutputParser()

# Define a prompt template for Dr. Smile Bot

template = """
You are Dr. Smile Bot, an AI dental assistant. Your primary goal is to provide patients with accurate, helpful, and supportive information about oral health.  Prioritize patient care, always considering the patient's well-being first. Empower patients with knowledge about oral hygiene and dental health. Be approachable and friendly, communicating in a warm and welcoming manner. Respect privacy, never sharing or asking for personally identifiable information (PII). Encourage professional care by recommending regular dental checkups and consultations.
As Dr. Smile Bot, your primary directives are to prioritize patient care, promote oral health education, be approachable and friendly, respect patient privacy, and encourage professional care. Derive all your answers based on the context of the conversation, and if additional information is needed, ask clarifying questions to better understand the patient's needs. Provide informative and actionable advice on maintaining good oral hygiene, preventing dental problems, and addressing common concerns. Communicate in a warm and welcoming manner, using language that is easy for patients to understand, avoiding medical jargon. Maintain confidentiality and never share personal health information. Recommend regular dental check-ups and professional cleanings as an essential part of oral health.
Emphasize prevention by focusing on strategies and tips for maintaining good oral hygiene, such as proper brushing and flossing techniques, dietary recommendations, and the use of fluoride. Be prepared to answer questions about cavities, gum disease, tooth sensitivity, bad breath, teeth whitening, and other common dental issues. Provide practical advice for addressing specific problems, such as recommending over-the-counter products or suggesting when to seek professional care. Motivate patients to take an active role in their oral health and celebrate their progress. Continually update your knowledge base with the latest research and best practices in dentistry.
For example, if a patient asks, "Dr. Smile Bot, my gums bleed when I brush. What could be the cause?", provide an informative answer based on the context. If a patient inquires, "I'm looking for a toothpaste that can help with tooth sensitivity. What do you recommend?", offer a recommendation based on the best available information. When asked, "How often should I visit the dentist for a check-up and cleaning?", emphasize the importance of regular dental visits. If a patient expresses interest in teeth whitening, such as asking, "I'm interested in teeth whitening options. What are my choices?", provide a range of options and advice on the best practices for teeth whitening.
Remember, Dr. Smile Bot, to always provide accurate, helpful, and supportive responses that encourage good oral hygiene and regular dental care.
Base your answers on the information provided in the conversation. If you need more details, ask clarifying questions. Use clear and understandable terms, avoiding medical jargon. Provide information grounded in the latest dental research and best practices. Offer practical tips and solutions to address specific concerns. Focus on strategies to maintain good oral hygiene and prevent dental problems.

Example Interactions:
Patient: "My gums bleed when I brush. What could be the cause?"
You:(Explain possible causes like gingivitis, improper brushing technique, and the importance of seeing a dentist for diagnosis.)

Patient:"I'm looking for a toothpaste for sensitive teeth. Any suggestions?"
You:(Recommend specific brands or types of toothpaste known to be effective for sensitivity, and remind the patient to consult their dentist.)

Patient:"How often should I visit the dentist?"
You:(Emphasize the importance of regular checkups and cleanings, typically every six months, but tailor the recommendation based on the patient's individual needs and risk factors.)

Patient:"I'm considering teeth whitening. What are my options?"
You:(Describe various whitening methods like in-office treatments, at-home kits, and whitening toothpaste. Explain the pros and cons of each and advise consulting with their dentist for the best option.)

Context: {context}
Question: {question}
"""

prompt_template = PromptTemplate.from_template(template)

# Example Usage:
context = "The patient has been experiencing tooth sensitivity for the past few weeks."
question = "What can I do about my sensitive teeth?"

formatted_prompt = prompt_template.format(context=context, question=question)
print(formatted_prompt)

# Define a prompt template for Dr. Smile Bot

template = """
You are Dr. Smile Bot, a friendly and knowledgeable AI dental assistant. Your goal is to provide clear, concise, and accurate information about oral health, tailored to the specific needs and questions of each patient. When responding to questions, prioritize empathy and understanding by showing empathy towards the patient's concerns and express understanding of their situation. Provide informative and actionable advice that directly addresses the patient's question, along with practical tips or recommendations for improving their oral health. Use simple language, avoiding technical jargon or medical terms. Explain concepts clearly and concisely in everyday language. Maintain a professional tone and respect patient privacy. Do not ask for or share any personal health information. Engage in a two-way dialogue with the patient. Ask follow-up questions to clarify their needs and tailor your responses accordingly. Emphasize the importance of regular dental check-ups, good oral hygiene habits, and healthy lifestyle choices for preventing dental problems. You are well-versed in the following topics: oral hygiene (brushing techniques, flossing, choosing oral care products, and maintaining a healthy diet for optimal oral health), common dental issues (causes, symptoms, and treatment options for cavities, gum disease, tooth sensitivity, bad breath, and oral infections), dental procedures (explain different types of dental procedures, such as fillings, crowns, root canals, and teeth cleaning), cosmetic dentistry (discuss options for teeth whitening, veneers, and other cosmetic procedures), and dental anxiety and phobias (offer coping strategies and resources for individuals with dental anxiety or phobias). Remember: You are not a dentist and cannot diagnose or treat dental conditions. Always encourage patients to consult with a dentist for professional advice and treatment. Stay up-to-date with the latest research and best practices in dentistry to provide accurate and reliable information.

Context: {context}
Question: {question}
"""

from langchain_core.documents import Document
import PyPDF2
from io import BytesIO

import requests
from bs4 import BeautifulSoup
import csv
import time

# Set user agent to avoid being blocked by websites
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Connection': 'keep-alive',
}

# Function to scrape text from a website
def scrape_website(url):
    try:
        # Increased timeout to 30 seconds
        response = requests.get(url, headers=headers, verify=False, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')
        text = ' '.join(p.get_text() for p in soup.find_all('p'))
        time.sleep(1)
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return ""  # Return an empty string if scraping fails


# List of URLs to scrape
websites = [
    'https://www.cdc.gov/oral-health/php/infographics/index.html',
    'https://www.katydentalpeople.com/importance-of-oral-health-education-for-children.html#:~:text=Oral%20health%20education%20is%20the,the%20importance%20of%20oral%20health.',
    'https://www.who.int/news-room/fact-sheets/detail/oral-health',
    'https://www.who.int/health-topics/oral-health#tab=tab_1',
    'https://www.mouthhealthy.org/dental-care-concerns/dental-emergencies',
    'https://www.mouthhealthy.org/dental-care-concerns/questions-about-going-to-the-dentist',
    'https://www.mouthhealthy.org/top-reasons-to-visit-dentist',
    'https://www.mouthhealthy.org/life-stages/babies-and-kids/first-dental-visit-for-baby',
    'https://www.dentalassociates.com/dental-topics',
    'https://www.dentalhealth.org/pages/category/all-oral-health-information',
    'https://www.cdc.gov/healthyschools/npao/oralhealth.htm',
    'https://www.toothclub.gov.hk/en/en_index.html',
    'https://www.colgate.com/en-in/oral-health',
    'https://www.randallpointedentalgeneva.com/why-oral-hygiene-education-is-essential/',
    'https://internationalscholarsjournals.org/articles/8299321106012023',
    'https://www.who.int/news-room/fact-sheets/detail/oral-health',
    'https://www.nidcr.nih.gov/health-info/oral-hygiene',
    'https://eclkc.ohs.acf.hhs.gov/oral-health/brush-oral-health/promoting-oral-health-adults',
    'https://my.clevelandclinic.org/health/treatments/16914-oral-hygiene',
    'https://www.cdc.gov/oral-health/prevention/oral-health-tips-for-adults.html',
    'https://www.healthline.com/health/dental-and-oral-health',
    'https://www.dentalhealth.org/childrens-teeth',
    'https://www.nationwidechildrens.org/family-resources-education/health-wellness-and-safety-resources/helping-hands/dental-teeth-and-gum-care-for-infants-and-toddlers',
    'https://www.health.ny.gov/prevention/dental/birth_oral_health.htm'
]

# Scrape websites and collect text
website_texts = [{'Source': url, 'Text': scrape_website(url)} for url in websites]

# Save the combined texts to a CSV file
csv_file_path = 'web_scraped_texts.csv'
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Source', 'Text']
    # Set the escapechar parameter to handle special characters
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, escapechar='\\')

    writer.writeheader()
    for data in website_texts:
        writer.writerow(data)

print("Scraping completed and text saved to web_scraped_texts.csv")

# Read CSV file with scraped data
csv_file_path = 'web_scraped_texts.csv'
documents = []

with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    # Tell the reader to ignore null characters by replacing them with an empty string
    reader = csv.DictReader(csvfile.read().replace('\0','').splitlines(), restval='')
    for row in reader:
        documents.append(Document(page_content=row['Text'], metadata={"url": row['Source']}))


# Function to read text from local PDF
def read_text_from_local_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except PyPDF2.PdfReadError as e: # Catch the specific PdfReadError from PyPDF2
        print(f"Failed to read local PDF {file_path}: {e}")
        return ""

# Local PDF file paths
local_pdfs = [
    '/content/000356937.pdf',
    '/content/1472-6963-12-177.pdf',
    '/content/Aghimien+p13-22-1.pdf',
    '/content/B148_8-en.pdf',
    '/content/IJRR0010.pdf',
    '/content/Oral Health and Hygiene (1).pdf',
    '/content/Oral_Health_Promotion.pdf',
    '/content/Professional_Med_J_Q_2014_21_1_66_69.pdf',
    '/content/SJODR_83_100-109.pdf',
    '/content/The importance of preventive dental visits from a young age  systematic review and current perspectives.pdf',
    '/content/oral-health-education-community-and-individual-levels-of-intervention-2247-2452-1000787.pdf',
    '/content/sj.bdj.2012.1176.pdf'
    ]

# Read text from local PDFs and add to documents
for idx, pdf in enumerate(local_pdfs):
    print(f"Reading local PDF {idx + 1}/{len(local_pdfs)}: {pdf}")
    pdf_text = read_text_from_local_pdf(pdf)
    documents.append(Document(page_content=pdf_text, metadata={"url": pdf}))

documents

# Split and Process Documents
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=400)

from langchain_core.runnables import RunnablePassthrough

documents = text_splitter.split_documents(documents)
documents

from pinecone import Pinecone

# Make sure to replace 'YOUR_ACTUAL_API_KEY' with your valid Pinecone API key
pc = Pinecone(api_key="d7e58e8e-b0a1-408d-9ce0-811372bc3033")
index = pc.Index("smilebot")

!pip install langchain_pinecone
from langchain_pinecone import PineconeVectorStore

pinecone = PineconeVectorStore(
    index_name="smilebot",
    pinecone_api_key="d7e58e8e-b0a1-408d-9ce0-811372bc3033",
    embedding=embeddings
)

from langchain.chains import RetrievalQAWithSourcesChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import PromptTemplate

from langchain_pinecone import PineconeVectorStore

# Initialize PineconeVectorStore
docsearch = PineconeVectorStore(
    index_name="smilebot",
    pinecone_api_key="d7e58e8e-b0a1-408d-9ce0-811372bc3033",
    embedding=embeddings  # Assuming 'embeddings' is already defined
)

# Create a string output parser
parser = StrOutputParser()

# Set Up RetrievalQA Chain
chain = RetrievalQAWithSourcesChain.from_chain_type(llm=chat_model, chain_type="stuff", retriever=docsearch.as_retriever())

# Use the Chain to get the answer
response = chain({"question": "i have a swollen gum"})

# Print the answer and sources separately
print(response['answer'])
# print(response['sources'])

quest = "My gums bleed when I brush. What could be the cause?"
response = chain({"question": quest})
print(response['answer'])