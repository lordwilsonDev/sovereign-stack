import zipfile
import os

zip_path = "/Users/lordwilson/model training data set 1/google-docs.zip"
extract_path = "/Users/lordwilson/model training data set 1/unzipped"

os.makedirs(extract_path, exist_ok=True)

try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            try:
                # Try to extract each file individually to skip problematic ones
                zip_ref.extract(file_info, extract_path)
                print(f"Extracted: {file_info.filename}")
            except Exception as e:
                print(f"Failed to extract {file_info.filename}: {e}")
except Exception as e:
    print(f"Error opening zip: {e}")
