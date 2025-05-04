import os
import json
def check_directory_permissions(path: str) -> bool:
    # Get the parent directory of the path
    parent_dir = os.path.dirname(path)
    
    # Check if we have write and execute permissions on the parent directory
    if not os.path.exists(parent_dir):
        # If parent directory doesn't exist, check permissions on the first existing parent
        while parent_dir and not os.path.exists(parent_dir):
            parent_dir = os.path.dirname(parent_dir)
    
    if parent_dir:
        return os.access(parent_dir, os.W_OK | os.X_OK)
    return False

def write_json_to_file(file_path: str, data: dict) -> None:
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def read_json_from_file(file_path: str) -> dict:
    with open(file_path, "r") as file:
        return json.load(file)