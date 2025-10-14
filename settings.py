import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = True

DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
