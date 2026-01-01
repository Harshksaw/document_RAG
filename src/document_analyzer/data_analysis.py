import os
from utils.model_loader import ModelLoader
from models.models import *
from exception.custom_exception import DocumentPortalException
from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import JsonOutputParser


class DocumentAnalyzer:
    
    def __init__(self):
        pass
    
    def analyze_metadata(self):
        pass