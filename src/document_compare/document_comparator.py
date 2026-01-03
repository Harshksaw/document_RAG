import sys
from pathlib import Path    
import fitz

from logger.custom_logger import CustomLogger
from exceptions.custom_exception import CustomException 

class DocumentComparator:
    def __init__(self):
        pass
    def delete_exisiting_files(self, path: Path):
        try:
            if path.exists():
                for file in path.iterdir():
                    file.unlink()
        except Exception as e:
            raise CustomException(e, sys) from e
    
    def save_uploaded_files(self):
        pass
    
    def read_pdf(self):
        pass