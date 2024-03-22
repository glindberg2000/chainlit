from memgpt.client.admin import Admin
from memgpt.client.admin import Admin as AdminRESTClient
from memgpt.client.client import RESTClient

# Load environment variables from .env file
load_dotenv()
base_url = os.getenv("MEMGPT_API_URL", "default_base_url_if_not_set")
master_api_key = os.getenv("MEMGPT_SERVER_PASS", "default_api_key_if_not_set")

restclient = RESTClient()
adminclient = Admin()

print(restclient)
