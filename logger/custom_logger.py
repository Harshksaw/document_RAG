from datetime import datetime
import logging
import os

class CustomLogger:
    def __init__(self):
        self.logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        
        log_file = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file_path =  os.path.join(self.logs_dir, log_file)
        
        logging.basicConfig(
            filename=log_file_path,
            level=logging.INFO,
            format="[%(asctime)s ]  %(levelname)s %(name)s (line:%(lineno)d) - %(message)s",
        )
        
        
        
    def get_logger(self, name=__file__):
        """
        Retrieve a logger instance with the basename of the provided name.
        
        This method creates or returns an existing logger configured with the 
        module's basename. The basename is extracted from the full path provided, 
        which helps in creating clean, readable logger names without full file paths.
        
        Args:
            name (str): The full path or name of the module/file for which to 
                        create or retrieve a logger. Typically, __name__ or a file path.
        
        Returns:
            logging.Logger: A logger instance named after the basename of the input name.
        
        Example:
            >>> logger = get_logger('/path/to/mymodule.py')
            >>> logger.info('This is a log message')
            # Logger name will be 'mymodule.py'
        """
        return logging.getLogger(os.path.basename(name))
    
    
if __name__ == "__main__":
    custom_logger = CustomLogger()
    logger = custom_logger.get_logger(__file__)
    logger.info("This is a test log message.")