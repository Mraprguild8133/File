import os
import time

async def rename_file(file_path, new_name):
    """
    Renames a given file to a new name.

    Args:
        file_path (str): The original path of the file.
        new_name (str): The new name for the file.

    Returns:
        str: The new path of the renamed file, or None if an error occurs.
    """
    try:
        # Get the directory and the original file extension
        directory = os.path.dirname(file_path)
        _, extension = os.path.splitext(file_path)

        # Create the new file path
        new_file_path = os.path.join(directory, new_name + extension)

        # Perform the rename operation
        os.rename(file_path, new_file_path)

        return new_file_path
    except OSError as e:
        print(f"Error renaming file: {e}")
        return None
