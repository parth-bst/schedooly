from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from langchain_openai import ChatOpenAI
from src.linkedin_helpers import check_linkedin_login, linkedin_login
import time
import logging
from config import get_config
from job_tracker import log_JD

config = get_config()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from custom_webdriver import CustomWebDriver

class LinkedinJobFinder:
    def __init__(self):
        self.driver = CustomWebDriver().get_driver()
    
    def login(self):
        # Replace existing login code with helper function
        if not check_linkedin_login(self.driver):
            linkedin_login(self.driver)
        
    def analyze_job_cards(self, page_html = " "):
        # Use LLM to identify the correct selectors
        prompt = f"""Analyze this LinkedIn jobs page HTML and identify the CSS selectors for:
        <dict>
            "jobCardContainer": ".job-card-container",
            "jobTitle": ".job-title",
            "companyName": ".company-name",
            "location": ".location",
            "jobDescription": ".job-description",
            "aboutTheCompany": ".about-the-company"
        </dict>
        
        These selectors will be used to extract job details from the job listings.
        
        Return only the CSS selectors in structured JSON format.
        
        HTML: {page_html}"""
        
        chat = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.3, 
            api_key=config.config['openai']['api-key']
        )
        response = chat.invoke(
            input=prompt,
            # messages=[
            #     # {"role": "system", "content": "You are a personal job search helper that generates ATS-friendly CVs and cover letters."},
            # ],
            max_tokens=500
        )
        
        logger.info(f"Received selectors from LLM: \n\n {response.content}")
        print(f"Received selectors from LLM: \n\n {response.content}")
        
        selectors = response.content if isinstance(response.content, str) else response.content[0]
        return selectors

    def get_elements_by_selectors(self, wait, selector_list) -> list[WebElement]:
        element = []
        for selector in selector_list:
            try:
                elems = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                logger.info(f"found {len(elems)} elements")
                # logger.info(f"elements found are \n {elems}")
                return elems
                #element.append(elems)
            except:
                continue
        return element
    
    def get_text_from_selectors(self, wait, selector_list, text_if_not_available="not found"):
        element = None
        for selector in selector_list:
            try:
                element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
            except:
                continue
            if element:
                innerText = element.get_attribute("textContent").strip() if element else text_if_not_available
                logger.info(f"{selector}: {innerText}")
                return innerText
        return text_if_not_available

    def get_all_job_details(self, wait, selectors):
        # Get all elements in a single DOM query using a compound selector
        compound_selector = ", ".join([
            selector for selector_list in selectors.values() 
            for selector in selector_list
        ])
        logger.info(f"Using compound selector: {compound_selector}")
        
        all_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, compound_selector)))
        logger.info(f"Found {len(all_elements)} total elements")
        
        job_detail = {
            'company': '',
            'location': '',
            'title': '',
            'description': '',
            'about_company': ''
        }
    
        # Match elements to fields based on their selectors
        for element in all_elements:
            element_html = element.get_attribute('outerHTML')
            logger.info(f"Processing element: {element_html[:100]}...")  # Log first 100 chars
            
            for field, selector_list in selectors.items():
                for selector in selector_list:
                    if selector in element_html:
                        value = element.get_attribute("textContent").strip()
                        job_detail[field.replace('Name', '').lower()] = value
                        logger.info(f"Matched {field} with selector {selector}: {value[:100]}...")  # Log first 100 chars
                        break
        
        logger.info(f"Final job details: {job_detail}")
        return job_detail
    
    def start(self, search_url, limit=10):
        logger.info(f"Starting LinkedIn job search with URL: {search_url}")
        try:
            self.login()
            self.driver.get(search_url)
            time.sleep(20)
            
            # Get dynamic selectors from LLM
            # Get the page HTML for analysis
            # selectors = self.analyze_job_cards(self.driver.page_source)
            
            selectors = {
                "jobCardContainer": [".base-search-card--link", ".job-card-container--clickable"],
                "jobTitle": [".top-card-layout__title", ".job-details-jobs-unified-top-card__job-title"],
                "companyName": [".topcard__org-name-link", ".job-details-jobs-unified-top-card__company-name"],
                "location": ["span.topcard__flavor.topcard__flavor--bullet"],
                "jobDescription": [".description__text", ".jobs-description__container", ".jobs-description-content__text--stretch"],
                "aboutTheCompany": [".jobs-company__company-description"]
                }
            wait = WebDriverWait(self.driver, 20)
            
            # Use the dynamically identified selector for job cards
            job_cards = self.get_elements_by_selectors(wait, selectors['jobCardContainer'])
            logger.info(f"Found {len(job_cards)} job cards")
            
            job_details = []
            processed_cards = 0
            
            while processed_cards < limit and processed_cards < len(job_cards):
                current_card = job_cards[processed_cards]
                logger.info(f"Processing job {processed_cards + 1}")
                
                try:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(current_card).perform()
                    # time.sleep(1)
                    # self.driver.execute_script("window.scrollTo(0, arguments[0].getBoundingClientRect().top - 100);", current_card)
                    time.sleep(4)
                    
                    current_card.click()
                    time.sleep(4)
                    
                    # Use dynamic selectors for each field
                    # element = current_card.find_element(By.CSS_SELECTOR, selectors['companyName'])
                    
                    # TODO: OPTIMIZATION to get data from DOM in single pass.
                    # job_detail = self.get_all_job_details(wait, selectors)

                    company = self.get_text_from_selectors(wait, selectors['companyName']) 
                    logger.info(f"Company: {company}")
                    
                    location = self.get_text_from_selectors(wait, selectors['location']) 
                    logger.info(f"Location: {location}")
                    
                    title = self.get_text_from_selectors(wait, selectors['jobTitle']) 
                    logger.info(f"Title: {title}")
                    
                    description = self.get_text_from_selectors(wait, selectors['jobDescription']) 
                    logger.info(f"Description: {description}")
                    
                    about_company = self.get_text_from_selectors(wait, selectors['aboutTheCompany']) 
                    logger.info(f"About Company: {about_company}")
                    
                    
                    job_detail = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'about_company': about_company
                    }
                    job_details.append(job_detail)
                    logger.info(f"Processed job with detials {job_detail}")
                    print(f"Processed job with detials {job_detail}")
                    log_JD(job_detail)
                    
                except Exception as e:
                    logger.error(f"Error processing job card: {str(e)}")
                
                processed_cards += 1
                
            return job_details

        finally:
            pass
            # if self.driver:
            #     self.driver.quit()


def test_analyze_job_cards_real(job_finder):
        """Integration test for form analysis"""
        logger.info("Running DYnamic analyze_job_cards test")
        
        # Get the HTML content
        html_content = ""
        selectors = job_finder.analyze_job_cards(html_content[:350000])
        
        logger.info(f"Selectors from LLM are:\n\n {selectors}")
        
        # Validate the response structure
        assert isinstance(selectors, dict), "Form data should be a dictionary"
        
        # Check for essential fields
        expected_fields = ['job_card_container', 'job_title', 'company_name', 'location', 'job_description']
        for field in expected_fields:
            assert field in selectors, f"Missing field: {field}"
            assert isinstance(selectors[field], str), f"Field {field} should be a string selector"
        
        logger.info("Form analysis test completed successfully")                


if __name__ == "__main__":
    job_finder = LinkedinJobFinder()
    # test_analyze_job_cards_real(job_finder)
    results = job_finder.start(config.config['linkedin']['search-url'], limit=1)
    logger.info(f"Results from Linkedin: {results}")
    
    