import chainlit as cl

from ui.handlers import handle_action, handle_message, handle_start


@cl.on_chat_start
async def on_chat_start():
    await handle_start()


@cl.on_message
async def on_message(message: cl.Message):
    await handle_message(message)


@cl.action_callback("main_cmd")
async def on_action(action: cl.Action):
    await handle_action(action)
