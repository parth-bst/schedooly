# Filename: job_tracker.py
import csv
import time
from src.config import AppConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = AppConfig()

def log_JD(job_detail):
    with open('jd_log.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([job_detail, time.strftime("%Y-%m-%d")])

def log_application(job_title, company, url, status=""):
    with open('applications_log.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([job_title, company, url, status, time.strftime("%Y-%m-%d")])
