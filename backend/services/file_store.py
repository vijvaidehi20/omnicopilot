"""
In-memory temporary file store.
Maps user_id -> { 'filename': str, 'content': str }
"""
TEMP_FILE_STORE = {}

def store_file_text(user_id: int, filename: str, content: str):
    TEMP_FILE_STORE[user_id] = {
        'filename': filename,
        'content': content
    }

def get_file_text(user_id: int) -> dict | None:
    return TEMP_FILE_STORE.get(user_id)
