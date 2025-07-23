import base64
import os

try:
    with open('logo.png', 'rb') as f:
        encoded_string = base64.b64encode(f.read()).decode('utf-8')
        print(encoded_string)
except FileNotFoundError:
    print("Error: logo.png not found in the current directory.")
except Exception as e:
    print(f"An error occurred: {e}")
