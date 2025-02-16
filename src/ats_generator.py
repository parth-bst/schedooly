import openai
import json
from typing import Dict, Any
from pathlib import Path
from langchain_openai import ChatOpenAI
from config import AppConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenerateCoverLetterCV:
    def __init__(self):
        self.config = AppConfig()
        self.openai_api_key = self.config.config['openai']['api_key']
        openai.api_key = self.openai_api_key
        self.chat = ChatOpenAI(
            model="gpt-3.5-turbo", 
            temperature=0, 
            api_key=self.config.config['openai']['api-key']
        )

    def _create_prompt(self, job: Dict[str, Any], base_cv_data: Dict[str, Any]) -> str:
        return f"""
        Based on the following job description and base CV data, generate a tailored ATS-friendly CV and cover letter:
        
        Job Description: {job['description']}
        Base CV Data: {base_cv_data}
        
        Output the CV and cover letter in a structured JSON format.
        """

    def generate_documents(self, job: Dict[str, Any], base_cv_data: Dict[str, Any]) -> str:
        prompt = self._create_prompt(job, base_cv_data)
        
        response = self.chat.invoke(
            input=prompt,
            messages=[
                {"role": "system", "content": "You are a personal job search helper that generates ATS-friendly CVs and cover letters."},
            ],
            max_tokens=8000
        )

        generated_docs = json.dumps(response.content if isinstance(response.content, str) else response.content[0])
        logger.info(f"\n\n Generated documents from LLM: \n{generated_docs}")
        
        self._save_documents(job['title'], generated_docs)
        return generated_docs

    def _save_documents(self, job_title: str, generated_docs: str) -> None:
        output_path = Path("output")
        output_path.mkdir(exist_ok=True)
        
        cover_letter_path = output_path / f"{job_title}_Cover_Letter.docx"
        with open(cover_letter_path, "w") as cl_file:
            cl_file.write(generated_docs)
