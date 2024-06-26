import json

import aiohttp
from memgpt.client.client import RESTClient

# from client import RESTClient


class ExtendedRESTClient(RESTClient):

    def __init__(self, base_url: str, token: str, debug: bool = False):
        super().__init__(base_url=base_url, token=token, debug=debug)
        self.token = token
        print(f"Token set in ExtendedRESTClient: {self.token}")  # Debugging line

    async def send_message_to_agent_streamed(self, agent_id, message):
        url = f"{self.base_url}/api/agents/{agent_id}/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        payload = {
            "agent_id": agent_id,
            "message": message,
            "stream": "True",
            "role": "user",
        }
        print(f"PAYLOAD: {payload}")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                async for line in response.content:
                    decoded_line = line.decode("utf-8").strip()
                    if not decoded_line:  # Skip empty lines
                        continue
                    print(f"Raw streamed data: {decoded_line}")
                    try:
                        # Remove the "data: " prefix before parsing JSON
                        if decoded_line.startswith("data: "):
                            json_str = decoded_line[6:]  # Skip the "data: " part
                            data = json.loads(json_str)
                            yield data
                        else:
                            print("Streamed line doesn't start with 'data: '")
                    except json.JSONDecodeError:
                        print("Error parsing JSON from streamed data")
                        continue
