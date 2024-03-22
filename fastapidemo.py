from fastapi import FastAPI, Request, Response

import chainlit as cl

# app = FastAPI()  # This assumes FastAPI is the underlying server for Chainlit


@cl.step
def tool():
    return "Response from the tool!"


@cl.on_message
async def main(message: cl.Message):
    # Your existing Chainlit chatbot logic
    tool_response = tool()
    await cl.Message(content=f"Tool said: {tool_response}").send()
    await cl.Message(content="This is the final answer").send()


# @cl.get("/regular-function")
# def regular_function():
#     # An example of a standard FastAPI route within a Chainlit app
#     return {"message": "This is a response from a regular Python function!"}


@cl.on_logout
def handle_logout(request: Request, response: Response):
    # Your logout logic, manipulating the HTTP response directly
    response.delete_cookie("my_cookie")


# The app is run using Chainlit's own mechanism (e.g., 'chainlit run app.py')
# No need to explicitly call uvicorn.run() here, as Chainlit handles it
