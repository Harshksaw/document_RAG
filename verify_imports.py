import sys
import os

# Add src to path and current directory
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

print("Verifying imports...")

try:
    from src.document_compare.data_ingestion import DocumentComparator as DCIngestion
    print("SUCCESS: Imported DocumentComparator from data_ingestion")
except Exception as e:
    print(f"FAILURE: Could not import from data_ingestion: {e}")

try:
    from src.document_compare.document_comparator import DocumentComparator as DCComparator
    print("SUCCESS: Imported DocumentComparator from document_comparator")
except Exception as e:
    print(f"FAILURE: Could not import from document_comparator: {e}")
