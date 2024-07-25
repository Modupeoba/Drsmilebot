# -*- coding: utf-8 -*-
"""smilebot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nqLMKB4iGhsSiCR8wEJLn-rSmHeRq-Sh
"""

# Import Libraries and Set Up Environment Variables
import os
# from google.colab import userdata
from google.generativeai import GenerativeModel
from langchain.chains import RetrievalQA
from langchain.vectorstores import Pinecone
from langchain.prompts import PromptTemplate
from langchain.document_loaders import PyPDFLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from google.generativeai import configure
import google.generativeai as genai
from langchain.embeddings import GooglePalmEmbeddings
from langchain.chat_models import ChatGooglePalm
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
import pandas as pd
import streamlit as st

# Replace 'your-api-key' with your actual Pinecone API key
os.environ["PINECONE_API_KEY"] = st.secrets["PINECONE_API_KEY"] # Set Pinecone API key as an environment variable


# Retrieve Gemini API key from Google Colab's userdata
GEMINI_API_KEY = "AIzaSyB-3SICe5or9W7Dv3X0-8yaZqS1ForMd0k"

os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
# Configure the Gemini API
configure(api_key=GEMINI_API_KEY)  # configure the API

# Initialize Google PaLM Embeddings
embeddings = GooglePalmEmbeddings(google_api_key=GEMINI_API_KEY)

# Initialize ChatGooglePalm model
chat_model = ChatGooglePalm(temperature=0.7, google_api_key=GEMINI_API_KEY)

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

pinecone = PineconeVectorStore(
    index_name="smilebot",
    embedding=embeddings
)

from langchain.chains import RetrievalQAWithSourcesChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import PromptTemplate

from langchain_pinecone import PineconeVectorStore
docsearch = PineconeVectorStore(
    index_name="smilebot",
    pinecone_api_key="d7e58e8e-b0a1-408d-9ce0-811372bc3033",
    embedding=embeddings  # Assuming 'embeddings' is already defined
)

# Create a string output parser
parser = StrOutputParser()

# Set Up RetrievalQA Chain
chain = RetrievalQAWithSourcesChain.from_chain_type(llm=chat_model, chain_type="stuff", retriever=pinecone.as_retriever())

 # -------------------- sTREAMLIT iMPLEMENTATION ---------------------------
import streamlit as st

# Set page configuration at the start
st.set_page_config(page_title="Dr. Smile Bot", page_icon=":smiley:", layout="wide")

# Define the main function
def main():
        
     # Centered title and image
    st.markdown("<h1 style='text-align: center; font-weight: bold;'>🦷 Dr. Smile Bot 🦷</h1>", unsafe_allow_html=True)
    
    # Adding space before the image
    st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
    st.image("realistic-vector-icon-illustration-teeth-whitening-concept-dental-clinic-white-dirty-tooth.png", width=400)  # Replace with your main image path
    st.markdown("</div>", unsafe_allow_html=True, )
    
    # Sidebar options
    st.sidebar.title("Smile hub")
    st.sidebar.image("5495572-removebg-preview.png",use_column_width=True,caption = 'Welcome User')  # Replace with your sidebar image path
    sidebar_option = st.sidebar.selectbox("Choose an option", ["Chat with Dr. Smile Bot", "Dental Tips", "FAQ"])

    # # Display main image
    # st.image("teeth-dental-care-medical-background.png", width = 800)  # Replace with your main image path

    if sidebar_option == "Chat with Dr. Smile Bot":
        st.header("Chat with Dr. Smile Bot")

        # Chat history
        if 'responses' not in st.session_state:
            st.session_state['responses'] = []
        if 'user_inputs' not in st.session_state:
            st.session_state['user_inputs'] = []

        user_input = st.chat_input("Ask your dental-related question")

        if user_input:
            response = chain({"question": user_input})
            st.session_state['user_inputs'].append(user_input)
            st.session_state['responses'].append(response['answer'])

        if st.session_state['responses']:
            for i in range(len(st.session_state['responses'])):
                st.write(f"**You:** {st.session_state['user_inputs'][i]}")
                st.write(f"**Dr. Smile Bot:** {st.session_state['responses'][i]}")

    elif sidebar_option == "Dental Tips":
        st.header("Dental Tips")
        st.write("""
            - Brush your teeth twice a day with fluoride toothpaste.
            - Floss daily to remove plaque from between your teeth.
            - Eat a healthy diet and limit sugary snacks.
            - Visit your dentist regularly for check-ups and cleanings.
        """)

    elif sidebar_option == "FAQ":
        st.header("Frequently Asked Questions")
        st.write("""
            **Q: How often should I visit the dentist?**
            A: It is recommended to visit the dentist every six months for a check-up and cleaning.

            **Q: What should I do if I have a toothache?**
            A: If you have a toothache, rinse your mouth with warm water, floss to remove any food particles, and see your dentist as soon as possible.

            **Q: How can I prevent gum disease?**
            A: Brush your teeth twice a day, floss daily, eat a balanced diet, and visit your dentist regularly.
        """)

if __name__ == '__main__':
    main()
