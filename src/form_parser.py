from httpx import get
from langchain_openai import ChatOpenAI
import json
from selenium.webdriver.common.by import By
from pathlib import Path
from src.config import get_config
from src.llm_utils import parse_llm_xml_response
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = get_config()

def save_form_data(url, form_data, filename="application_history.json"):
    history_file = Path("artifacts/logs/data") / filename
    history_file.parent.mkdir(exist_ok=True)
    
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
    else:
        history = {}
    
    history[url] = form_data
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=4)

def get_saved_form_data(url, filename="application_history.json"):
    history_file = Path("artifacts/logs/data") / filename
    if history_file.exists():
        with open(history_file, 'r') as f:
            history = json.load(f)
            return history.get(url)
    return None

def analyze_form(html_content, url, output_format_dict):
    """
    Analyzes form HTML and returns structured data matching the provided format
    
    Args:
        html_content: HTML of the form to analyze
        url: URL of the form for caching
        output_format_dict: Dictionary showing the expected output format
    """
    saved_data = get_saved_form_data(url)
    if saved_data:
        return saved_data
    
    # Limit HTML content to reduce token usage
    truncated_html = html_content[:350000]
    
    prompt = f"""Analyze this job application form HTML and identify the form fields and their types.
    Return the form data with keys matching the below provided sample format:
    ___________________
    {output_format_dict}
    ___________________
    Look for elements that are interactable so that we can dynamically set values for these form fields in next step.
    the "required" field is to be populated with all the attributes that are marked as required in the form data.
    Add attributes to dictionary that are required but are missing in the sample.
    for attributes not matching any form field, return empty strings for them.
    
    HTML: {truncated_html}
    _______________
    
    Output the python dictionary wrapped around <python_dict></python_dict> tag, and explanation wrapped around <explanation> tag.
    """
    
    logger.info(f"Analyzing form with prompt: LLM") # \n\n {prompt} \n\n")

    chat = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=config.config.get('openai.api-key')
    )
    
    response = chat.invoke(
        input=prompt,
        max_tokens=500
    )
    
    parsed_response = parse_llm_xml_response(response.content if isinstance(response.content, str) else response.content[0], dict_tags=["python_dict"])
    logger.info(f"Received form data from LLM: \n\n {parsed_response['python_dict']} \n\n")
    
    # Save the analyzed form data for future use
    save_form_data(url, parsed_response['python_dict'])
    return parsed_response['python_dict']


def fill_dynamic_form(driver, form_data, job_data = {}):
    logger.info(f"Filling form with data:\n\n {form_data}\n\n")
    logger.info(f"Job data:\n\n {job_data}\n\n")
    
    field_mapping = {
        "name": job_data['user_profile']['name'],
        "email": job_data['user_profile']['email'],
        "resume": job_data['document_paths']['cv'],
        "phone": job_data['user_profile']['phone'],
        "linkedin": job_data['user_profile'].get('linkedin', ''),
        "portfolio": job_data['user_profile'].get('portfolio', ''),
        "cover_letter": job_data['document_paths']['cover_letter']
    }
    
    for field_name, selector in form_data.items():
        if field_name == 'required':
            continue
        try:
            for key, value in field_mapping.items():
                if key in field_name:
                    driver.find_element(By.CSS_SELECTOR, selector).send_keys(value)
                    logger.info(f"Filled field: {field_name} with value: {value}")
                    break
        except Exception as e:
            logger.error(f"Error filling field {field_name}: {e}")
            print(f"Could not fill field {field_name}: {e}")