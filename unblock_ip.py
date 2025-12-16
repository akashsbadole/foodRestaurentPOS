import requests

# URL to unblock IP
unblock_url = "http://127.0.0.1:5000/api/security/unblock-ip"

# Get our local IP
import socket
local_ip = socket.gethostbyname(socket.gethostname())

# Prepare data to unblock IP
data = {
    "ip_address": local_ip
}

print(f"Attempting to unblock IP: {local_ip}")

try:
    # Send request to unblock IP
    response = requests.post(unblock_url, json=data)
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text}")
except Exception as e:
    print(f"Error unblocking IP: {e}")