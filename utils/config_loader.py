import yaml

def load_config(file_path):
    """Load a YAML configuration file and return its contents as a dictionary.

    Args:
        file_path (str): The path to the YAML configuration file.
    Returns:
        dict: The contents of the YAML file as a dictionary.
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

