
import requests
import os
from urllib.parse import urlparse

# Create static/images directory if it doesn't exist
os.makedirs('static/images/holes', exist_ok=True)

# Base URL for hole images
base_url = "https://pinnaclepointestate.co.za/wp-content/uploads/2024/01/"

# Download images for all 18 holes
for hole_num in range(1, 19):
    image_url = f"{base_url}Hole-{hole_num}.jpg"
    local_filename = f"static/images/holes/hole-{hole_num}.jpg"
    
    try:
        print(f"Downloading hole {hole_num} image...")
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        with open(local_filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Successfully downloaded hole {hole_num} image")
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to download hole {hole_num}: {e}")
        
        # Create a placeholder image path for failed downloads
        placeholder_path = f"static/images/holes/placeholder-{hole_num}.jpg"
        print(f"Using placeholder for hole {hole_num}")

print("Image download process completed!")
