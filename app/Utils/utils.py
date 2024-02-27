import os
import uuid
import re


def generate_filename(filename):
    # Get the file extension
    ext = os.path.splitext(filename)[1]

    # Generate a unique filename
    unique_filename = str(uuid.uuid4())

    # Concatenate the filename and extension with the unique filename
    return f"{unique_filename}{ext}"


def generate_slug(title):
    # Remove leading and trailing whitespace
    title = title.strip()

    # Convert to lowercase
    title = title.lower()

    # Replace spaces with dashes
    title = title.replace(" ", "-")

    # Remove special characters
    title = re.sub(r"[^a-z0-9\-]", "", title)

    return title