import sys
from pathlib import Path    
import fitz

from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException    


class DocumentComparator:
    def __init__(self, base_dir):
        self.log = CustomLogger().get_logger(__name__)
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True )





    def delete_existing_files(self, path: Path):
        try:
            if path.exists():
                for file in path.iterdir():
                    file.unlink()
        except Exception as e:
            raise DocumentPortalException(e, sys) from e

    def save_uploaded_files(self, reference_file, actual_file ):
        try:
            self.delete_existing_files(self.base_dir)
            self.log.info(f"Existing files deleted successfully: {self.base_dir}")
            ref_path =self.base_dir /reference_file.name
            act_path = self.base_dir /actual_file.name
            
            if not reference_file.name.endswith(".pdf") or not actual_file.name.endswith(".pdf"):
                raise ValueError("Invalid file format")

            with open(ref_path, "wb") as ref_file:
                ref_file.write(reference_file.read_bytes())
            with open(act_path, "wb") as act_file:
                act_file.write(actual_file.read_bytes())
            self.log.info(f"Files saved successfully: {ref_path}, {act_path}")
            return ref_path, act_path
      

        except Exception as e:
            self.log.error(f"Error in save_uploaded_files method of DocumentComparator class: {e}")
            raise DocumentPortalException("An error occurred while saving the uploaded files", sys)

    def read_pdf(self, pdf_path):
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError("Encrypted PDFs are not supported",{"pdf_path": pdf_path})
                all_text = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text.strip():
                        all_text.append(f"\n ---Page {page_num + 1}---\n{text}")
                self.log.info(f"PDF read successfully: {pdf_path}")
                return "".join(all_text)

        except Exception as e:
            self.log.error(f"Error in read_pdf method of DocumentComparator class: {e}")
            raise DocumentPortalException("An error occurred while reading the PDF", sys)