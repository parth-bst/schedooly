# Google Docs Manager

A Python library for reading and writing data between Google Docs and Google Sheets.


## Setup
1. Create a Google Cloud Project
2. Enable Google Docs and Google Sheets APIs
3. Create service account credentials
4. Download credentials JSON file
5. Set up environment variables

## Testing
The project includes comprehensive unit tests that interact with real Google Docs and Sheets APIs.

### Prerequisites for Testing
1. Create dedicated test documents in Google Docs and Google Sheets
2. Update the test document IDs in `tests/test_google_docs_reader.py`:
   - TEST_DOC_ID
   - TEST_SHEET_ID

### Running Tests
First, CD to the required folder:
```bash
cd scripts/schedooly
```

Execute the test suite using:

```bash
python -m unittest tests/test_google_docs_reader.py
```

To run a specific test:

```bash
python -m unittest tests.test_google_docs_reader.TestGoogleDocManager.test_get_base_cv_data
```

```bash
python -m unittest tests/test_linkedin_scraper.py -v -k test_jobfinder_start_success
```

To test run a function within a test sub class
```bash
python -m unittest tests.test_linkedin_scraper.TestLinkedinJobFinder.TestIntegration.test_real_job_search
```

Run the test file using pytest
```bash
pytest tests/test_linkedin_scraper.py -v
```

Run 1 test from test class using pytest
```bash
pytest tests/test_linkedin_scraper.py::TestJobFinder::test_jobfinder_start_success -v
```

Run only integration test, a subclass within a test class
```bash
pytest tests/test_linkedin_scraper.py -v -m integration
```

Run only unit test, a subclass within a test class
```bash
pytest scripts/schedooly/tests/test_linkedin_scraper.py::TestJobFinder::TestIntegration::test_real_job_search -v
```

## Google Suite Access Requirements

To enable API access to Google Suite files (Docs, Sheets), share your documents with the following service account email:
```
parthlocal@general-448219.iam.gserviceaccount.com
```
This email is associated with our project's Google service account credentials and needs viewer access to any Google Suite files used by the application.
