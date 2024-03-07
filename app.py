import chainlit as cl
from langserve.client import RemoteRunnable
from typing import Dict, Optional, Any
import chainlit as cl
import logging

# Import the database management functions from db_manager module
from ella_dbo.db_manager import create_connection, create_table, upsert_user, get_memgpt_user_id
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

def handle_memgpt_login(auth0_user_id):
    conn = create_connection()
    memgpt_user_id = get_memgpt_user_id(conn, auth0_user_id)
    api = MemGPTAPI()

    if not memgpt_user_id:
        memgpt_user = api.create_user()  # Adjust based on actual API response structure
        memgpt_user_id = memgpt_user.get("user_id")
        memgpt_user_api_key = memgpt_user.get("api_key")
        upsert_user(conn, auth0_user_id, memgpt_user_id=memgpt_user_id)  # Assuming upsert_user is adjusted to handle memgpt_user_id
    else:
        memgpt_user_api_key=api.create_user_api_key(memgpt_user_id)
    conn.close()

    # Now, memgpt_user_id is either fetched or newly created, and you can proceed with your app's logic

# # ***Base Working Example *** #
# @cl.on_chat_start
# async def on_chat_start():
#     # This function is called at the beginning of the chat session
#     # You can perform any initialization here if necessary
#     print("Chat session started!")

# *** 0Auth version ***
@cl.on_chat_start
async def on_chat_start():
    # Retrieve the cl.User object, assuming it's stored in the session or accessible via a similar mechanism
    app_user = cl.user_session.get("user")
    
    # Access user details from the metadata attribute of the cl.User object
    # This step assumes that 'metadata' or a similar mechanism is actually supported and correctly populated
    auth0_user_id = app_user.metadata.get("auth0_user_id", "Unknown ID")
    user_email = app_user.metadata.get("email", "Unknown Email")
    user_name = app_user.metadata.get("name", "Unknown Name")
    #user_roles_str = ", ".join(app_user.metadata.get("roles", ["user"]))
    user_roles = app_user.metadata.get("roles", ["user"])
    #auth0_user_id = app_user.identifier  # This was set as 'name' in the callback

    # For simplicity, checking if 'admin' is in user_roles
    if 'admin' in user_roles:
        # Logic to display the dashboard for admins
        # Assuming there's a method or logic to render/display the dashboard
        await cl.display_dashboard()  # Placeholder for actual dashboard display method
        return  # Prevent further execution to avoid going to the chat automatically
        
    #Get MemGPT user_id and api_key
    conn = create_connection()
    memgpt_user_id = get_memgpt_user_id(conn, auth0_user_id)
    api = MemGPTAPI()

    if not memgpt_user_id:
        memgpt_user = api.create_user()  # Adjust based on actual API response structure
        memgpt_user_id = memgpt_user.get("user_id")
        memgpt_user_api_key = memgpt_user.get("api_key")
        upsert_user(conn, auth0_user_id, memgpt_user_id=memgpt_user_id)  # Assuming upsert_user is adjusted to handle memgpt_user_id
    else:
        memgpt_user_api_key=api.create_user_api_key(memgpt_user_id)
    conn.close()


    # Construct and send a personalized message using the user's details
    custom_message = f"Hello {user_name} ({auth0_user_id}), your email is {user_email}, and your roles are: {user_roles}. Your MemGPT id is {memgpt_user_id} and your memgpt api key is {memgpt_user_api_key}"
    await cl.Message(custom_message).send()


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


@cl.on_message
async def on_message(message: cl.Message):
    # This function is called whenever a new message is received from the user using Langchain client

    # Initialize the RemoteRunnable with your service URL
    # "https://pirate2-a09a7c8ac86f5068a2dea2684f41fbe5-ffoprvkqsa-uc.a.run.app/pirate-speak"
    runnable = RemoteRunnable(
        "https://pirate2-a09a7c8ac86f5068a2dea2684f41fbe5-ffoprvkqsa-uc.a.run.app/ragtest"
    )

    # Prepare the request object
    # request_object = {"text": message.content}
    request_object = message.content

    # Execute the request and capture the response asynchronously
    response = await runnable.ainvoke(request_object)

    if response:
        # Extract the translated text from the response
        print(response)
        # translated_text = response.content
        answer = response

        # Send the extracted translated text as the chat response
        # await cl.Message(content=translated_text).send()
        await cl.Message(content=answer).send()
    else:
        # Handle errors or unexpected responses
        await cl.Message(
            content="Arrr! Something went wrong with the translation."
        ).send()
