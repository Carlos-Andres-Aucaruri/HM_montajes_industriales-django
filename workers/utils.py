import os
import uuid

from django.conf import settings


def save_excel_file(excel_file):
    folder_path = f"excel_files"
    file_name = f"{uuid.uuid4()}_{excel_file.name}"
    file_path = os.path.join(settings.BASE_DIR, folder_path, file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)
    except Exception as e:
        raise Exception(f"Error saving file: {e}")
    
    return file_path
