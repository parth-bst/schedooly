from linkedin_scraper import LinkedinJobFinder
from ats_generator import GenerateCoverLetterCV
from google_docs_reader import GoogleDocManager
from config import AppConfig
from custom_webdriver import CustomWebDriver
from application_pipeline import ApplicationProcessor
from datetime import datetime
import json
import openai
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = AppConfig()
artifacts_base_path = Path(config.config['paths']['artifacts_dir'])

# Configure services
openai.api_key = config.config['openai']['api-key']
openai.organization = config.config['openai']['organization']

# Step 1: Fetch job details from LinkedIn
#TODO: Loop over "start" to fetch more jobs
job_details = LinkedinJobFinder().start(config.config['linkedin']['search-url'] + "&start=0", limit=2)
logger.info(f"Fetched {len(job_details)} job details from LinkedIn.")

# Step 2: Read base CV data from Google Docs
google_doc_manager = GoogleDocManager()
base_cv_data = google_doc_manager.get_base_cv_data(config.config['google']['base-cv-doc-id'])
base_cv = {
    "experience": base_cv_data
}

# Step 3: Generate ATS-compliant documents
job_artifacts = {}
for job in job_details:
    logger.info(f"Generating documents for job: {job['title']} at {job['company']}")
    
    # Get user profile from form_parser
    user_profile = {
        "name": "Somya Agarwal",
        "email": "somya.agarwal@example.com",
        "resume_path": "/path/to/tailored_resume.docx",
        "phone": "+1234567890",
        "linkedin": "linkedin.com/in/somya-agarwal",
        "portfolio": "somya-agarwal.com"
    }
    
    # Generate ATS documents
    generated_docs = GenerateCoverLetterCV().generate_documents(job, base_cv)
    
    # Create composite key
    job_key = f"{job['company']}_{job['title']}".replace(' ', '_').lower()
    
    # Create job-specific directory
    job_dir = artifacts_base_path / job_key
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Save paths relative to artifacts_base_path
    cv_path = job_dir / "cv.pdf"
    cover_letter_path = job_dir / "cover_letter.pdf"
    metadata_path = job_dir / "metadata.json"
    
    # Combine all data into job_artifacts
    job_artifacts[job_key] = {
        "job_details": job,
        "base_cv": base_cv,
        "user_profile": user_profile,
        "document_paths": {
            "cv": str(cv_path.relative_to(artifacts_base_path)),
            "cover_letter": str(cover_letter_path.relative_to(artifacts_base_path)),
            "metadata": str(metadata_path.relative_to(artifacts_base_path))
        },
        "application_url": job.get('application_url', ''),
        "company": job.get('company', ''),
        "location": job.get('location', ''),
        "timestamp": datetime.now().isoformat()
    }

# Step 4: Process job applications
logger.info("Starting job application processing...")
application_processor = ApplicationProcessor()
application_processor.process_applications(job_artifacts)
logger.info("Successfully completed processing all job applications")
        
# At the end of processing
def cleanup():
    CustomWebDriver().quit()

if __name__ == "__main__":
    try:
        job_details = LinkedinJobFinder().start(config.config['linkedin']['search-url'] + "&start=0", limit=2)
        # Initialize the ApplicationProcessor
        application_processor = ApplicationProcessor()
        # Process the applications  
        application_processor.process_applications(job_artifacts) 
    finally:
        cleanup()