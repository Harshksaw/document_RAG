import sys
import traceback
from logger.custom_logger import CustomLogger



class DocumentPortalException(Exception):
    def __init__(self, error_message ,error_details: sys):
        
        _,_,exe_tb =error_details.exc_info()
        self.file_name = exe_tb.tb_frame.f_code.co_filename
        self.line_number = exe_tb.tb_lineno
        self.error_message = str(error_message)
        self.traceback_str = ''.join(traceback.format_exception(*error_details.exc_info()))
        

    def __str__(self):
        return  f"""
    Error in [{self.file_name}] at line [{self.line_number}],
    Message: {self.error_message}
    Traceback: {self.traceback_str}
    """
    
    
if __name__ == "__main__":
    try:
        a = 1 / 0
    except Exception as e:
        custom_logger = CustomLogger()
        logger = custom_logger.get_logger(__file__)
        doc_exception = DocumentPortalException(e, sys)
        logger.error(doc_exception)
