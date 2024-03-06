import chainlit as cl
from langserve.client import RemoteRunnable
from typing import Dict, Optional, Any
import chainlit as cl
import logging

# Import the database management functions from db_manager module
from ella_dbo.db_manager import create_connection, create_table, upsert_user


# Example usage
# db_file = './database.db'
# conn = create_connection(db_file)

# # Create table if not exists
# create_table(conn)
# Insert a new user
# user_info = ('auth0|1234567', 'user2@example.com', 'John Doe', 'user')
# upsert_user(conn, *user_info)

#conn.close()


# Example oAuth Callback
# @cl.oauth_callback
# def oauth_callback(
#     provider_id: str,
#     token: str,
#     raw_user_data: Dict[str, str],
#     default_user: cl.User,
# ) -> Optional[cl.User]:
#     return default_user

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# *** oAuth working ***
@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, Any],
    default_user: cl.User,
) -> Optional[cl.User]:
    # Extract necessary information from raw_user_data
    unique_id = raw_user_data.get("sub", "Unknown ID")
    user_email = raw_user_data.get("email", "Unknown Email")
    user_name = raw_user_data.get("name", "Unknown Name")
    user_roles = raw_user_data.get("https://ella-ai/auth/roles", ["user"])  # Default role

    # Construct the cl.User object with identifier and metadata
    # This example assumes that the cl.User class can accept and store additional metadata
    # If cl.User does not support this directly, you may need to explore alternative approaches
    custom_user = cl.User(identifier=user_name, metadata={
        "user_id": unique_id,
        "email": user_email,
        "name": user_name,
        "roles": user_roles
    })

    conn = create_connection()
    create_table(conn)
    # Upsert user
    #dummy_info = ('auth0|1234567', 'user3@example.com', 'Pepe the Frog', 'superuser')
    roles_str = ", ".join(user_roles)  # Convert list of roles to a string
    custom_info = (unique_id,user_email,user_name,roles_str)
    #print(dummy_info)
    print(custom_info)
    upsert_user(conn, *custom_info)
    conn.close()

    return custom_user

# # ***Base Working *** #
# @cl.on_chat_start
# async def on_chat_start():
#     # This function is called at the beginning of the chat session
#     # You can perform any initialization here if necessary
#     print("Chat session started!")

# *** 0Auth working version ***
@cl.on_chat_start
async def on_chat_start():
    # Retrieve the cl.User object, assuming it's stored in the session or accessible via a similar mechanism
    app_user = cl.user_session.get("user")
    
    # Access user details from the metadata attribute of the cl.User object
    # This step assumes that 'metadata' or a similar mechanism is actually supported and correctly populated
    user_email = app_user.metadata.get("email", "Unknown Email")
    user_id = app_user.metadata.get("user_id", "Unknown ID")
    user_name = app_user.metadata.get("name", "Unknown Name")
    #user_roles_str = ", ".join(app_user.metadata.get("roles", ["user"]))
    user_roles = app_user.metadata.get("roles", ["user"])
    #unique_id = app_user.identifier  # This was set as 'name' in the callback

    # For simplicity, checking if 'admin' is in user_roles
    if 'admin' in user_roles:
        # Logic to display the dashboard for admins
        # Assuming there's a method or logic to render/display the dashboard
        await cl.display_dashboard()  # Placeholder for actual dashboard display method
        return  # Prevent further execution to avoid going to the chat automatically
        


    # Construct and send a personalized message using the user's details
    custom_message = f"Hello {user_name} ({user_id}), your email is {user_email}, and your roles are: {user_roles}."
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
