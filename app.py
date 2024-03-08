import chainlit as cl
from langserve.client import RemoteRunnable
from typing import Dict, Optional, Any
import logging
import aiohttp

# Import the database management functions from db_manager module
from ella_dbo.db_manager import create_connection, create_table, upsert_user, get_memgpt_user_id, get_memgpt_user_id_and_api_key
from ella_memgpt.memgpt_api import MemGPTAPI


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, Any],
    default_user: cl.User,
) -> Optional[cl.User]:
    auth0_user_id = raw_user_data.get("sub", "Unknown ID")
    user_email = raw_user_data.get("email", None)
    user_name = raw_user_data.get("name", None)
    user_roles = raw_user_data.get("https://ella-ai/auth/roles", ["none"])  # Assign 'none' as a default role

    custom_user = cl.User(identifier=user_name, metadata={
        "auth0_user_id": auth0_user_id,
        "email": user_email,
        "name": user_name,
        "roles": user_roles
    })

    conn = create_connection()
    create_table(conn)
    roles_str = ", ".join(user_roles)
    upsert_user(conn, auth0_user_id=auth0_user_id, roles=roles_str, email=user_email, name=user_name)
    conn.close()

    return custom_user

# *** 0Auth version ***
@cl.on_chat_start
async def on_chat_start():
    # Retrieve the cl.User object, assuming it's stored in the session or accessible via a similar mechanism
    app_user = cl.user_session.get("user")
    
    # Access user details from the metadata attribute of the cl.User object
    auth0_user_id = app_user.metadata.get("auth0_user_id", "Unknown ID")
    user_email = app_user.metadata.get("email", "Unknown Email")
    user_name = app_user.metadata.get("name", "Unknown Name")
    user_roles = app_user.metadata.get("roles", ["user"])

    # For simplicity, checking if 'admin' is in user_roles
    if 'admin' in user_roles:
        # Logic to display the dashboard for admins
        # Assuming there's a method or logic to render/display the dashboard
        await cl.display_dashboard()  # Placeholder for actual dashboard display method
        return  # Prevent further execution to avoid going to the chat automatically
        
    #Get MemGPT user_id and api_key
    conn = create_connection()
    #memgpt_user_id = get_memgpt_user_id(conn, auth0_user_id)
    memgpt_user_id, memgpt_user_api_key = get_memgpt_user_id_and_api_key(conn, auth0_user_id)  # Adjust function call accordingly
    
    api = MemGPTAPI()

    if not memgpt_user_id:
        memgpt_user = api.create_user()  # Adjust based on actual API response structure
        memgpt_user_id = memgpt_user.get("user_id")
        memgpt_user_api_key = memgpt_user.get("api_key")
        upsert_user(conn, auth0_user_id, memgpt_user_id=memgpt_user_id, memgpt_user_api_key=memgpt_user_api_key)
    elif not memgpt_user_api_key:
        # If there is no API key, generate a new one
        memgpt_user_api_key = api.create_user_api_key(memgpt_user_id)
        # Update the user record to include the new API key
        upsert_user(conn, auth0_user_id, memgpt_user_api_key=memgpt_user_api_key)
    conn.close()

    # Store MemGPT user ID and API key in the session
    cl.user_session.set("memgpt_user_id", memgpt_user_id)
    cl.user_session.set("memgpt_user_api_key", memgpt_user_api_key)

    # Use the get_agents function to fetch the list of agents
    agents = api.get_agents(memgpt_user_api_key)

    # Assuming this is part of the on_chat_start function
    if not agents or agents.get("num_agents", 0) == 0:
        # No agents found, creating new default agent
        config = {
            "name": "Default Agent",
            "preset": "memgpt_chat",
            "human": "cs_phd",
            "persona": "sam_pov"
        }
        # Call to create a new agent with the specified config
        api.create_agent(user_api_key=memgpt_user_api_key, config=config)
        # Re-fetch the agents after creating a new one to include it in the list
        agents = api.get_agents(memgpt_user_api_key)

    # Now, regardless of whether agents were initially found or a new one was created,
    # you have an up-to-date list of agents for the display logic.
    if agents and agents.get("num_agents") > 0:
        agent_list = agents.get("agents", [])
        display_message = "Your Agents:\n" + "\n".join([f"- {agent['name']}" for agent in agent_list])
        selected_agent_id = agent_list[0].get('id')
        cl.user_session.set("selected_agent_id", selected_agent_id)  # Store the selected agent ID in the session
    else:
        display_message = "No agents available."


    # Construct and send a personalized message using the user's details
    custom_message = f"Hello {user_name} ({auth0_user_id}), your email is {user_email}, and your roles are: {user_roles}. Your MemGPT id is {memgpt_user_id} and your memgpt api key is {memgpt_user_api_key}. {display_message}"
    await cl.Message(custom_message).send()

@cl.on_message
async def on_message(message: cl.Message):
    user_api_key = cl.user_session.get("memgpt_user_api_key")
    agent_id = cl.user_session.get("selected_agent_id")
    memgpt_api = MemGPTAPI()

    msg = cl.Message(content="")
    await msg.send()

    # Now correctly using async for with an asynchronous iterable
    async for part in memgpt_api.send_message_to_agent_streamed(user_api_key, agent_id, message.content):
        if 'assistant_message' in part:
            message = part['assistant_message']
            # Logic to display the message in the chatbot app
            await msg.stream_token(message)  # Example method to stream response to UI

    await msg.update()



# @cl.on_message
# async def on_message(message: cl.Message):
#     user_api_key = cl.user_session.get("memgpt_user_api_key")
#     agent_id = cl.user_session.get("selected_agent_id")  # Assuming this is set elsewhere in your app
#     memgpt_api = MemGPTAPI()

#     # Sending message to the agent
#     print(f"Sending message to agent. User API Key: {user_api_key}, Agent ID: {agent_id}, Message: {message.content}")
#     response = memgpt_api.send_message_to_agent(user_api_key, agent_id, message.content)
#     print(f"Received response: {response}")
#     if response:
#         # Extract and send the agent's response back to the user
#         agent_reply = response.get("message")  # Adjust based on actual response structure
#         print(f"Agent reply: {agent_reply}")
#         await cl.Message(content=agent_reply).send()
#     else:
#         # Handle cases where no response is received
#         print("Failed to communicate with the agent. Response was None.")
#         await cl.Message(content="Failed to communicate with the agent.").send()

# @cl.on_message
# async def on_message(message: cl.Message):
#     # This function is called whenever a new message is received from the user
#     # Calls langchain API using standard Python
#
#     async with httpx.AsyncClient() as client:
#         # Replace "http://localhost:8000/pirate-speak" with the actual URL of your pirate speak endpoint
#         response = await client.post(
#             "https://pirate-2e5e15cdca175f9e91229f8ec398dc0f-ffoprvkqsa-uc.a.run.app/pirate-speak/invoke",
#             json={"input": {"text": message.content},"config": {},"kwargs": {}},
#         )

#         if response.status_code == 200:
#             # Parse the JSON response
#             response_json = response.json()

#             # Extract the translated text from the 'content' field within the 'output' object
#             translated_text = response_json.get("output", {}).get("content", "Arrr! Translation missing.")

#             # Send the extracted translated text as the chat response
#             await cl.Message(content=translated_text).send()
#         else:
#             # Handle errors or unexpected responses
#             await cl.Message(content="Arrr! Something went wrong with the translation.").send()


# @cl.on_chat_start
# async def start_chat():
#     cl.user_session.set(
#         "prompt_history",
#         "",
#     )
#     await cl.Avatar(
#         name="Claude",
#         url="https://www.anthropic.com/images/icons/apple-touch-icon.png",
#     ).send()


# @cl.on_message
# async def on_message(message: cl.Message):
#     # This function is called whenever a new message is received from the user using Langchain client

#     # Initialize the RemoteRunnable with your service URL
#     # "https://pirate2-a09a7c8ac86f5068a2dea2684f41fbe5-ffoprvkqsa-uc.a.run.app/pirate-speak"
#     runnable = RemoteRunnable(
#         "https://pirate2-a09a7c8ac86f5068a2dea2684f41fbe5-ffoprvkqsa-uc.a.run.app/ragtest"
#     )

#     # Prepare the request object
#     # request_object = {"text": message.content}
#     request_object = message.content

#     # Execute the request and capture the response asynchronously
#     response = await runnable.ainvoke(request_object)

#     if response:
#         # Extract the translated text from the response
#         print(response)
#         # translated_text = response.content
#         answer = response

#         # Send the extracted translated text as the chat response
#         # await cl.Message(content=translated_text).send()
#         await cl.Message(content=answer).send()
#     else:
#         # Handle errors or unexpected responses
#         await cl.Message(
#             content="Arrr! Something went wrong with the translation."
#         ).send()
