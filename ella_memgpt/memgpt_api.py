import os
import requests
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

class MemGPTAPI:
    def __init__(self):
        # Load environment variables
        self.base_url = os.getenv('MEMGPT_API_URL', 'default_base_url_if_not_set')
        self.master_api_key = os.getenv('MEMGPT_SERVER_PASS', 'default_api_key_if_not_set')

    def get_users(self):
        """Retrieve a list of users from the memGPT API."""
        url = f"{self.base_url}/admin/users"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.master_api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    # The get api key does not work. 
    #
    # def get_user_api_key(self, user_id):
    #     """Retrieve the API key for a specific user."""
    #     url = f"{self.base_url}/admin/users/keys?user_id={user_id}"
    #     headers = {
    #         "accept": "application/json",
    #         "authorization": f"Bearer {self.master_api_key}"
    #     }
    #     response = requests.get(url, headers=headers)
    #     if response.status_code == 200:
    #         # Assuming the API returns the key directly or adjust based on actual response structure
    #         return response.json()
    #     else:
    #         return None
        
    # Create a new Api key works:
    def create_user_api_key(self, user_id):
        """Retrieve the API key for a specific user."""
        url = f"{self.base_url}/admin/users/keys"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.master_api_key}"
        }
        # Now using POST and including user_id in the JSON body
        payload = {"user_id": user_id}
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            # Parse the response based on the actual structure
            # Adjust the parsing as necessary based on the API's response structure
            api_key = response.json().get('api_key', [])
            return api_key
        else:
            return None
            # Handle non-200 responses or add more specific error handling as needed


    def create_user(self):
        """Create a new user in the memGPT API."""
        url = f"{self.base_url}/admin/users"
        #payload = {"user_id": user_id}
        payload = {}
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.master_api_key}"
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:  # Success or Created
            return response.json()
        else:
            return None

# Example usage
if __name__ == "__main__":
    api = MemGPTAPI()
    user_id = 'mycustomuser'
    
    users = api.get_users()
    if users and any(user['user_id'] == user_id for user in users.get('user_list', [])):
        print("User exists, fetching API key...")
        user_key = api.get_user_api_key(user_id)
        print(f"User API Key: {user_key}")
    else:
        print("User does not exist, creating user...")
        new_user = api.create_user(user_id)
        print(f"New User Created: {new_user}")
