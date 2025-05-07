import logging
from fastapi import FastAPI, Request, HTTPException, APIRouter
from handlers.message_handler import MessageHandler

app = FastAPI()
message_handler = MessageHandler()

webhook_router = APIRouter()


@webhook_router.post('/hook/messages')
async def handle_new_messages(request: Request):
    try:
        messages = (await request.json()).get('messages', [])

        for message in messages:
            await message_handler.process_message(message)
        return {"status": "Ok"}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Error")
