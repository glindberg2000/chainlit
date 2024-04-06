import logging

# Configure the root logger to log debug information
logging.basicConfig(level=logging.INFO)
import os
import time
from typing import Any, Dict, Optional

from chainlit.server import app
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from memgpt.client.admin import Admin as AdminRESTClient

import chainlit as cl
from ella_memgpt.extendedRESTclient import ExtendedRESTClient
from ella_memgpt.memgpt_api import MemGPTAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Load environment variables from .env file
load_dotenv()
base_url = os.getenv("MEMGPT_API_URL", "http://localhost:8283")
master_api_key = os.getenv("MEMGPT_SERVER_PASS", "ilovellms")
api_key = os.getenv("OPENAI_API_KEY", "defaultopenaikey")

# Define default values
DEFAULT_USER_ID = "d48465a1-8153-448d-9115-93fdaae4b290"
DEFAULT_API_KEY = "sk-614ca012fa835acffa3879729c364124eba195fca46b190b"
DEFAULT_AGENT_ID = "31b3722a-ebc1-418a-9056-4ef780d2f494"
DEFAULT_AGENT_CONFIG = {
    "name": "DefaultAgent5",
    "preset": "memgpt_chat",
    "human": "cs_phd",
    "persona": "anna_pa",
}
CHATBOT_NAME = "Ella"


@app.get("/hello")
def hello(request: Request):
    print(request.headers)
    return HTMLResponse("Hello World")


@app.get("/test-page", response_class=HTMLResponse)
async def test_page(request: Request):
    headers = request.headers
    cookies = request.cookies

    headers_list = "<br>".join([f"{key}: {value}" for key, value in headers.items()])
    cookies_list = "<br>".join([f"{key}: {value}" for key, value in cookies.items()])

    html_content = f"""
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h2>Headers</h2>
            <p>{headers_list}</p>
            <h2>Cookies</h2>
            <p>{cookies_list}</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/new-test-page")
async def new_test_page():
    return FileResponse("public/test_page.html")


@app.get("/voice-chat")
async def new_test_page():
    return RedirectResponse(
        url="https://vapi.ai/?demo=true&shareKey=c87ea74e-bebf-4196-aebb-fbd77d5f28c0&assistantId=7d444afe-1c8b-4708-8f45-5b6592e60b47"
    )


@app.post("/api/dummy-model/chat/completions")
async def custom_model(request: Request):
    data = await request.json()
    user_message = data.get("messages", [{}])[-1].get("content", "")

    # Dummy response mimicking the structured response from your custom AI model
    response = {
        "id": "customcmpl-0000XxXxx0XXxXx0x0X0XxX0x0X0000",
        "object": "chat.completion",
        "created": 1712373788,
        "model": "my-custom-model-0001",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Received your message: {user_message}. This is a dummy response.",
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": 36,
            "total_tokens": 60,
        },
    }

    return JSONResponse(content=response)


# Assuming handle_message_from_vapi is properly imported and available
# from your_message_handling_module import handle_message_from_vapi


@app.post("/api/custom-model")
async def custom_model(request: Request):
    data = await request.json()
    user_message = data.get("messages", [{}])[-1].get("content", "")

    # Call the function to handle the message and get memGPT's response
    assistant_message = await handle_message_from_vapi(user_message)

    # Construct a response in the expected format
    response = {
        "id": "customcmpl-0000XxXxx0XXxXx0x0X0XxX0x0X0000",
        "object": "chat.completion",
        "created": int(time.time()),  # Use current time for the 'created' field
        "model": "my-custom-model-0001",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": assistant_message,  # Use the actual response from memGPT
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": len(
                assistant_message.split()
            ),  # Adjust based on actual response length
            "total_tokens": len(user_message.split()) + len(assistant_message.split()),
        },
    }

    return JSONResponse(content=response)


@app.get("/protected-page", response_class=HTMLResponse)
def protected_page():
    print("trying protected page....")
    try:
        # Attempt to retrieve the Chainlit user session
        app_user = user_session.get("user")
        # app_user = None

        # Print the user session data to the console for debugging
        logger.error(f"User session data: {app_user}")
        print(f"User session data: {app_user}")

        if app_user and "user" in app_user.metadata.get("roles", []):
            # If the user is authenticated and authorized, return a simple HTML page
            return HTMLResponse(
                content=f"""
            <html>
                <head>
                    <title>Protected Page</title>
                </head>
                <body>
                    <h1>Welcome, {app_user.metadata['name']}</h1>
                    <p>This is a protected page.</p>
                </body>
            </html>
            """
            )
        else:
            # User not authorized to access this page
            logger.info("Access denied: User not authorized or session missing.")
            return HTMLResponse(
                content="""
            <html>
                <head>
                    <title>Access Denied</title>
                </head>
                <body>
                    <h1>Access Denied</h1>
                    <p>You must be a valid user to view this page.</p>
                </body>
            </html>
            """,
                status_code=403,
            )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401, detail="Authentication error. Please try again."
        )


from datetime import datetime, timedelta
from typing import Dict

import jwt

# Your secret key for signing the JWT - keep it secure and do not expose it
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def generate_jwt_for_user(user_details: Dict[str, any]) -> str:
    """
    Generates a JWT for an authenticated user with the provided user details.

    :param user_details: A dictionary containing details about the user.
    :return: A JWT as a string.
    """
    # Define the token expiration time (e.g., 24 hours from now)
    expiration_time = datetime.utcnow() + timedelta(hours=24)

    # Define your JWT payload
    payload = {"user_details": user_details, "exp": expiration_time}  # Expiration time

    # Encode the JWT
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


import jwt
from chainlit.user import User
from chainlit.user_session import user_session


def generate_jwt(user: User):
    jwt_secret = SECRET_KEY
    # Additional claims based on the user's profile or permissions
    claims = {
        "sub": user.identifier,
        "name": user.metadata.get("name"),
        "roles": user.metadata.get("roles"),
    }
    token = jwt.encode(claims, jwt_secret, algorithm="HS256")
    # Store the token in the user's session for later validation
    user_session.set("jwt_token", token)
    print("token being set: ", token)
    return token


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
    user_roles = raw_user_data.get(
        "https://ella-ai/auth/roles", ["none"]
    )  # Assign 'none' as a default role

    custom_user = cl.User(
        identifier=user_name,
        metadata={
            "auth0_user_id": auth0_user_id,
            "email": user_email,
            "name": user_name,
            "roles": user_roles,
        },
    )
    # user_session.set(identifier=user_name)

    return custom_user


@cl.on_chat_start
async def on_chat_start():
    # Attempt to access user details from the cl.User object
    try:
        app_user = cl.user_session.get("user")  # Simulated retrieval of user session
        roles = app_user.metadata.get("roles", [])
        # Directly check for 'user' role in user roles
        if "user" not in roles:
            await cl.Message(
                content=f"You must be an valid user to use this chat. Roles detected: {roles}",
                author=CHATBOT_NAME,
            ).send()
            return  # Exit if user is not an admin
    except Exception as e:
        await cl.Message(
            "Authentication error. Please try again.", author=CHATBOT_NAME
        ).send()
        logging.error(f"Authentication check failed: {e}")

    user_name = app_user.metadata.get("name", "Unknown Name")
    display_message = f"Successfuly loaded roles: {roles}"
    custom_message = f"Hello {user_name}, {display_message}"

    await cl.Message(content=custom_message, author=CHATBOT_NAME).send()


# Assuming the guardian_agent_analysis function returns a string (the note) or None
def guardian_agent_analysis(message_content):
    print("Guardian Agent Analysis called.")  # Debugging statement
    if "medication" in message_content.lower():
        note = "Note from staff: Remind user to take their meds since it's been over 24 hours."
        print(f"Guardian note generated: {note}")  # Debugging statement
        return note
    return None


# Assuming the guardian_agent_analysis function returns a string (the note) or None
def guardian_agent_analysis2(message_content):
    print("Guardian Agent Analysis called.")  # Debugging statement
    if "tired" in message_content.lower():
        note = "Note from staff: Remind user to get some exercise and fresh air."
        print(f"Guardian note generated: {note}")  # Debugging statement
        return note
    return None


async def handle_message_from_vapi(message_content: str):
    user_api_key = DEFAULT_API_KEY
    agent_id = DEFAULT_AGENT_ID
    user_api = ExtendedRESTClient(base_url, user_api_key)

    print(f"Received message: {message_content}")  # Debugging statement

    # If there's any preprocessing needed for the message, do it here
    # For the sake of simplicity, we'll assume the message is ready to go
    message_for_memgpt = message_content

    # Placeholder for the aggregated assistant's message
    assistant_message = ""

    # Streamed communication with memGPT
    async for part in user_api.send_message_to_agent_streamed(
        agent_id, message_for_memgpt
    ):
        # Handle the different parts of the response
        # For simplicity, we'll focus on appending the assistant messages
        if "assistant_message" in part:
            assistant_message += part["assistant_message"]

    # Return or process the final assistant message
    print(f"Assistant's Response: {assistant_message}")
    return assistant_message


# Example call to the function
# You would replace this with the actual message receiving mechanism from VAPI


@cl.on_message
async def on_message(message: cl.Message):
    user_api_key = DEFAULT_API_KEY
    agent_id = DEFAULT_AGENT_ID
    user_api = ExtendedRESTClient(base_url, user_api_key)

    print(f"Received message: {message.content}")  # Debugging statement
    # Call the guardian agent function to analyze the message and potentially add notes
    guardian_note = guardian_agent_analysis2(message.content)

    # Prepare the message for MemGPT, appending the guardian's note if it exists
    message_for_memgpt = message.content
    if guardian_note:
        print(f"Appending staff note to message: {guardian_note}")  # Debugging
        # Use an async step to visualize the staff note addition
        async with cl.Step(name="Adding Staff Note", type="note") as note_step:
            note_step.input = message.content
            note_step.output = guardian_note
            print("Visualizing staff note addition.")  # Debugging statement

        # Append the note to the user's message, ensuring a clear separation
        message_for_memgpt += f"\n\n{guardian_note}"
    else:
        print("No staff note added.")  # Debugging statement

    async with cl.Step(name=CHATBOT_NAME, type="llm", root=True) as root_step:
        root_step.input = message.content
        assistant_message = ""
        # Adjusted to pass the modified message content, now including the staff note
        async for part in user_api.send_message_to_agent_streamed(
            agent_id, message_for_memgpt
        ):
            if "internal_monologue" in part:
                monologue = part["internal_monologue"]
                async with cl.Step(
                    name="Internal Monologue", type="thought"
                ) as monologue_step:
                    monologue_step.output = monologue
            elif "function_call" in part:
                func_call = part["function_call"]
                async with cl.Step(name="Function Call", type="call") as func_call_step:
                    func_call_step.output = func_call
            elif "function_return" in part:
                func_return = f"Function Return: {part.get('function_return', 'No return value')}, Status: {part.get('status', 'No status')}"
                async with cl.Step(
                    name="Function Return", type="return"
                ) as func_return_step:
                    func_return_step.output = func_return
            elif "assistant_message" in part:
                assistant_message += part["assistant_message"]
                async with cl.Step(
                    name="Assistant Response", type="output"
                ) as assistant_step:
                    assistant_step.output = assistant_message

        root_step.output = assistant_message


# @cl.action_callback("action_button")
# async def on_action(action):
#     await cl.Message(content=f"Executed {action.name} with value {action.value}").send()
#     # Optionally remove the action button from the chatbot user interface
#     await action.remove()

# @cl.on_chat_start
# async def start():
#     # Sending multiple action buttons within a chatbot message
#     actions = [
#         cl.Action(name="action_button_1", value="value_1", description="Click me!"),
#         cl.Action(name="action_button_2", value="value_2", description="Click me too!"),
#         # Add more buttons as needed
#     ]

#     await cl.Message(content="Interact with these action buttons:", actions=actions).send()
