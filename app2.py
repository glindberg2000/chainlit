import logging
import os

from dotenv import load_dotenv
from memgpt.client.admin import Admin as AdminRESTClient

import chainlit as cl
from ella_memgpt.extendedRESTclient import ExtendedRESTClient
from ella_memgpt.memgpt_api import MemGPTAPI

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

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


@cl.on_chat_start
async def on_chat_start():
    # Attempt to access user details from the cl.User object
    try:
        app_user = cl.user_session.get("user")
        auth0_user_id = app_user.metadata.get("auth0_user_id", "Unknown ID")
        user_email = app_user.metadata.get("email", "Unknown Email")
        user_name = app_user.metadata.get("name", "Unknown Name")
        user_roles = app_user.metadata.get("roles", ["user"])
        use_default = False
    except Exception as e:
        logging.error(f"Error accessing user details: {e}")
        use_default = True
        user_name = "Default User"

    if use_default:
        memgpt_user_id = DEFAULT_USER_ID
        memgpt_user_api_key = DEFAULT_API_KEY
    else:
        print("init logic for db")
        # Database operations and MemGPT initialization logic here
        # This is where you would normally check for existing user details or create new ones

    # Initialize MemGPT or your custom API client with the obtained or default API key
    user_api = ExtendedRESTClient(base_url, memgpt_user_api_key)

    # agents = user_api.list_agents()
    # if not agents or agents.get("num_agents", 0) == 0:
    #     user_api.create_agent(DEFAULT_AGENT_CONFIG)
    #     agents = user_api.list_agents()

    display_message = (
        "Using default configuration."
        if use_default
        else "Your customized settings are loaded."
    )

    custom_message = f"Hello {user_name}, {display_message}"

    await cl.Message(custom_message).send()


# This version only extracts the final messages from the assist
# @cl.on_message
# async def on_message(message: cl.Message):
#     user_api_key = DEFAULT_API_KEY
#     agent_id = DEFAULT_AGENT_ID
#     user_api = ExtendedRESTClient(base_url, user_api_key)

#     # Initialize a variable to store the last message part sent
#     last_message_part = ""

#     async for part in user_api.send_message_to_agent_streamed(agent_id, message.content):
#         if 'assistant_message' in part:
#             assistant_message = part['assistant_message']
#             # Check if the current part is different from the last part sent
#             if assistant_message != last_message_part:
#                 # Update the Chainlit message content with the new part
#                 await cl.Message(assistant_message).send()
#                 # Update the last message part sent
#                 last_message_part = assistant_message


# Sample working code using openAI async client
# from openai import AsyncOpenAI
# import chainlit as cl
# client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# @cl.on_message
# async def main(msg: cl.Message):

#     # Whether to nest the step under the user message
#     root = True

#     async with cl.Step(name="gpt4", type="llm", root=root) as step:
#         step.input = msg.content

#         stream = await client.chat.completions.create(
#             messages=[{"role": "user", "content": msg.content}],
#             stream=True,
#             model="gpt-4",
#             temperature=0,
#         )

#         async for part in stream:
#             delta = part.choices[0].delta
#             if delta.content:
#                 # Stream the output of the step
#                 await step.stream_token(delta.content)


# Assuming the guardian_agent_analysis function returns a string (the note) or None
def guardian_agent_analysis(message_content):
    print("Guardian Agent Analysis called.")  # Debugging statement
    if "medication" in message_content.lower():
        note = "Note from staff: Remind user to take their meds since it's been over 24 hours."
        print(f"Guardian note generated: {note}")  # Debugging statement
        return note
    return None


@cl.on_message
async def on_message(message: cl.Message):
    user_api_key = DEFAULT_API_KEY
    agent_id = DEFAULT_AGENT_ID
    user_api = ExtendedRESTClient(base_url, user_api_key)

    print(f"Received message: {message.content}")  # Debugging statement
    # Call the guardian agent function to analyze the message and potentially add notes
    guardian_note = guardian_agent_analysis(message.content)

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

    async with cl.Step(name="Ella", type="llm", root=True) as root_step:
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


# Works great:
# @cl.on_message
# async def on_message(message: cl.Message):
#     user_api_key = DEFAULT_API_KEY
#     agent_id = DEFAULT_AGENT_ID
#     user_api = ExtendedRESTClient(base_url, user_api_key)

#     async with cl.Step(name="Ella", type="llm", root=True) as root_step:
#         root_step.input = message.content

#         assistant_message = ""
#         async for part in user_api.send_message_to_agent_streamed(agent_id, message.content):
#             if 'internal_monologue' in part:
#                 monologue = part['internal_monologue']
#                 async with cl.Step(name="Internal Monologue", type="thought") as monologue_step:
#                     monologue_step.output = monologue

#             elif 'function_call' in part:
#                 func_call = part['function_call']
#                 async with cl.Step(name="Function Call", type="call") as func_call_step:
#                     func_call_step.output = func_call

#             elif 'function_return' in part:
#                 func_return = f"Function Return: {part.get('function_return', 'No return value')}, Status: {part.get('status', 'No status')}"
#                 async with cl.Step(name="Function Return", type="return") as func_return_step:
#                     func_return_step.output = func_return

#             elif 'assistant_message' in part:
#                 assistant_message += part['assistant_message']
#                 async with cl.Step(name="Assistant Response", type="output") as assistant_step:
#                     assistant_step.output = assistant_message

#         root_step.output = assistant_message


@cl.action_callback("action_button")
async def on_action(action):
    await cl.Message(content=f"Executed {action.name} with value {action.value}").send()
    # Optionally remove the action button from the chatbot user interface
    await action.remove()


@cl.on_chat_start
async def start():
    # Sending multiple action buttons within a chatbot message
    actions = [
        cl.Action(name="action_button_1", value="value_1", description="Click me!"),
        cl.Action(name="action_button_2", value="value_2", description="Click me too!"),
        # Add more buttons as needed
    ]

    await cl.Message(
        content="Interact with these action buttons:", actions=actions
    ).send()
