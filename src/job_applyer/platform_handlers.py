from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.form_parser import analyze_form, fill_dynamic_form
from src.config import AppConfig
from src.job_tracker import log_application
from src.linkedin_helpers import check_linkedin_login, linkedin_login
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = AppConfig()

def handle_popups(driver):
    """Handle common LinkedIn popups and cookie consent windows"""
    try:
        # Handle cookie consent popup
        cookie_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[action-type="ACCEPT_COOKIES"], .cookie-consent-accept'))
        )
        logger.info("Handling cookie consent popup")
        cookie_button.click()
        
        # Handle other common LinkedIn popups
        close_buttons = driver.find_elements(By.CSS_SELECTOR, '[aria-label="Dismiss"], .artdeco-modal__dismiss')
        for button in close_buttons:
            if button.is_displayed():
                button.click()
                time.sleep(1)
    except:
        # Continue if no popups found
        pass

def try_linkedin_easy_apply(driver, job_data):
    """Handle LinkedIn Easy Apply flow if available"""
    easy_apply_selectors = [
        '.jobs-apply-button--top-card',
        '[data-control-name="easy_apply_button"]',
        'button[aria-label*="Easy Apply"]'
    ]
    
    for selector in easy_apply_selectors:
        try:
            easy_apply_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            logger.info("Easy Apply button found - using simplified application flow")
            easy_apply_button.click()
            time.sleep(3)
            
            # Handle Easy Apply form
            form_html = driver.find_element(By.TAG_NAME, 'form').get_attribute('outerHTML')
            output_format = {
                "email": ".email_input",
                "phone": ".phone-input",
                "resume": "#resume-upload-input",
            }
            
            form_data = analyze_form(
                html_content=form_html,
                url=driver.current_url, 
                output_format_dict=output_format
            )
            
            fill_dynamic_form(driver, form_data, job_data)
            
            # Submit Easy Apply
            submit_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label*="Submit"]')
            submit_button.click()
            return True
            
        except:
            continue
    
    return False

def handle_linkedin_platform(driver, url, job_data):
    """Handle LinkedIn job applications with job artifacts data"""
    logger.info(f"Processing LinkedIn application: {url}")
    
    check_linkedin_login(driver)
    driver.get(url)
    time.sleep(5)
    handle_popups(driver)
    
    try:
        # Try Easy Apply first
        if try_linkedin_easy_apply(driver, job_data):
            logger.info("Successfully completed Easy Apply application")
            return
            
        # If Easy Apply not available, proceed with regular flow
        logger.info("Easy Apply not available - proceeding with standard application")
        
        apply_button = driver.find_element(By.CSS_SELECTOR, '[data-control-name="job_apply_button"]')
        apply_button.click()
        time.sleep(3)
        
        # Keep track of redirections and look for forms
        max_redirects = 3
        redirect_count = 0
        
        while redirect_count < max_redirects:
            current_url = driver.current_url
            
            # Handle any popups that might appear after redirect
            handle_popups(driver)
            
            # Try to find a form first
            try:
                form = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'form'))
                )
                # Found the form - break the loop
                break
                # No form found, look for apply buttons
            except:
                pass
            try:
                apply_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR, 
                        '[type="submit"], [aria-label*="apply"], [class*="apply"], [data-automation-id="applyNow"]'
                    ))
                )
                apply_button.click()
                time.sleep(3)
                redirect_count += 1
            except:
                # No apply button found either - might be loading or wrong page
                time.sleep(2)
                redirect_count += 1
        
        # Get form HTML after reaching final application page
        form_html = driver.find_element(By.TAG_NAME, 'form').get_attribute('outerHTML')        
        output_format = {
            "email": ".email_input",
            "cv": ".resume-upload",
            "cover_letter": ".file-upload",
            "first_name": ".candidate-first__name",
            "last_name": ".candidate-last__name",
            "required": ["email", "cv", "first_name", "last_name"]   
        }
        
        # Analyze form with proper parameters
        # LLM CALL HERE 
        form_data = analyze_form(
            html_content=form_html, 
            url=url,
            output_format_dict=output_format
        )
        
        job_data.update({
            'resume': job_data['document_paths']['cv'],
            'cover_letter': job_data['document_paths']['cover_letter'],
            'user_info': job_data['user_profile']
        })
        
        fill_dynamic_form(driver, form_data, job_data)
        
        # Submit final application
        submit_button = driver.find_element(By.CSS_SELECTOR, '[type="submit"], [aria-label*="submit"]')
        submit_button.click()
        
    except Exception as e:
        logger.error(f"Error in LinkedIn application: {str(e)}")
        raise

def handle_workday_platform(driver, url, job_data):
    """Handle Workday job applications with job artifacts data"""
    logger.info(f"Processing Workday application: {url}")
    
    driver.get(url)
    time.sleep(5)
    
    try:
        # Optional Workday login if needed
        if config.config.get('workday', {}).get('credentials'):
            workday_login(driver)
            
        apply_button = driver.find_element_by_css_selector('[data-automation-id="applyNow"]')
        apply_button.click()
        time.sleep(3)
        
        form_html = driver.find_element_by_tag_name('form').get_attribute('outerHTML')
        form_data = analyze_form(form_html, url)
        
        # Update form data with job artifacts
        form_data.update({
            'resume': job_data['document_paths']['cv'],
            'cover_letter': job_data['document_paths']['cover_letter'],
            'name': job_data['user_profile']['name'],
            'email': job_data['user_profile']['email'],
            'phone': job_data['user_profile']['phone']
        })
        fill_dynamic_form(driver, form_data)
        
        submit_button = driver.find_element(By.CSS_SELECTOR, '[data-automation-id="bottom-navigation-next-button"]')
        submit_button.click()
        
    except Exception as e:
        logger.error(f"Error in Workday application: {str(e)}")
        raise

def handle_taleo_platform(driver, url, job_data):
    """Handle Taleo job applications with job artifacts data"""
    logger.info(f"Processing Taleo application: {url}")
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # Optional Taleo login if needed
        if config.config.get('taleo', {}).get('credentials'):
            taleo_login(driver)
            
        form_html = driver.find_element_by_tag_name('form').get_attribute('outerHTML')
        form_data = analyze_form(form_html, url)
        
        form_data.update({
            'resume': job_data['document_paths']['cv'],
            'cover_letter': job_data['document_paths']['cover_letter'],
            'user_info': job_data['user_profile']
        })
        
        fill_dynamic_form(driver, form_data)
        
    except Exception as e:
        logger.error(f"Error in Taleo application: {str(e)}")
        raise

def handle_generic_platform(driver, url, job_data):
    """Handle unknown platform job applications with job artifacts data"""
    logger.info(f"Processing generic platform application: {url}")
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # Find and analyze any forms on the page using current Selenium syntax
        forms = driver.find_elements(By.TAG_NAME, 'form')
        logger.info(f"Found {len(forms)} forms on the page.")
        for form in forms:
            form_html = form.get_attribute('outerHTML')
            
            output_format = {
                "field_name": "type",
                "email": ".email_input",
                "cv": ".resume-upload",
                "cover_letter": ".file-upload",
                "first_name": ".candidate-first__name",
                "last_name": ".candidate-last__name",
                "required": ["email", "cv", "first_name", "last_name"]   
            }

            form_data = {
                'email': '.Emailaddress',
                'cv': '.CurriculumVitae',
                'cover_letter': '.MotivationFile',
                'first_name': '.Firstname',
                'last_name': '.Lastname',
                'required': ['email', 'cv', 'first_name', 'last_name']
            }
            # Commented temporarily for testing
            # form_data = analyze_form(html_content=form_html, url=url, output_format_dict=output_format)

            
            job_data.update({
                'resume': job_data['document_paths']['cv'],
                'cover_letter': job_data['document_paths']['cover_letter'],
                'user_info': job_data['user_profile']
            })
            logger.info(f"Filling form with Form data: {form_data}")
            
            fill_dynamic_form(driver, form_data, job_data)
            
    except Exception as e:
        logger.error(f"Error in generic platform application: {str(e)}")
        raise  