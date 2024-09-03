import os
import requests
from bs4 import BeautifulSoup
from groq import Groq
import json
import logging
from retrying import retry
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up Groq API key and client
os.environ["GROQ_API_KEY"] = "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"
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def clean_text(text):
    return ' '.join(text.split())

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def extract_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return clean_text(text)
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return ""
    except Exception as e:
        logging.error(f"Error extracting text: {e}")
        return ""

def extract_event_details(text):
    prompt = f"""
    Extract the following details from the text below and format them in Schema.org 'Event' format. If some details are missing or not explicitly mentioned, leave them blank:

    - Name of event
    - Start date
    - End date
    - Time (in 12-hour format with AM/PM)
    - Event attendance mode
    - Event status
    - Location details (type, name, address, geo coordinates)
    - Address region
    - Address country
    - Description
    - Offer details (type, url, price, price currency, availability, valid from)
    - Performer details (type, name)
    - Organizer details (name, type, url)

    Text:
    {text}

    Provide the extracted details in the following JSON format (Schema.org 'Event'):

    {{
        "name": "",
        "startDate": "",
        "endDate": "",
        "time": "",
        "eventAttendanceMode": "",
        "eventStatus": "",
        "location": {{
            "@type": "Place",
            "name": "",
            "address": {{
                "@type": "PostalAddress",
                "addressLocality": "",
                "addressRegion": "",
                "addressCountry": ""
            }},
            "geo": {{
                "@type": "GeoCoordinates",
                "latitude": "",
                "longitude": ""
            }}
        }},
        "description": "",
        "offers": {{
            "@type": "Offer",
            "url": "",
            "price": "",
            "priceCurrency": "",
            "availability": "",
            "validFrom": ""
        }},
        "performer": {{
            "@type": "Person",
            "name": ""
        }},
        "organizer": {{
            "@type": "Organization",
            "name": "",
            "url": ""
        }}
    }}
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-70b-versatile"
        )
        response_content = chat_completion.choices[0].message.content.strip()

        if not response_content:
            logging.error("Received empty response from the Groq API")
            return ""

        # Log the raw API response for debugging
        logging.info(f"Raw API response: {response_content}")

        return response_content
    except Exception as e:
        logging.error(f"Error with Groq API: {e}")
        return ""

def main():
    st.markdown("<h1 style='color: #21c0e8;'>Event Scraper</h1>", unsafe_allow_html=True)

    url = st.text_input("Enter the URL to scrape:")

    if url:
        # Automatically trigger extraction when the user presses Enter
        with st.spinner('Extracting text from URL...'):
            cleaned_text = extract_text_from_url(url)
        
        if cleaned_text:
            st.subheader("Preview of Cleaned Text")
            st.text(cleaned_text[:500])
            
            with st.spinner('Extracting event details...'):
                event_details = extract_event_details(cleaned_text)
            
            if event_details:
                st.subheader("Extracted Event Details")
                try:
                    event_info = json.loads(event_details)
                    st.json(event_info)
                except json.JSONDecodeError:
                    st.text(event_details)
            else:
                st.error("Failed to extract event details.")
        else:
            st.warning("Please enter a valid URL.")

if __name__ == "__main__":
    main()
