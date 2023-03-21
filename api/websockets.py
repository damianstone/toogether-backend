from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message
import json


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # get scope from middleware
        self.sender_in_match = self.scope["profile_in_match"]

        # prevents someone from sending a message to any profile having a match id
        if not self.sender_in_match:
            await self.close()

        # get scope from middleware
        self.sender = self.scope["profile"]

        # get the scope from middleware
        self.match = self.scope["match"]

        # chat_room: this can be a match_id or chat_id
        self.chat_room = self.scope["url_route"]["kwargs"]["match_id"]

        # check if the user is authenticated, and if not, close the WebSocket connection
        if not self.sender.is_authenticated:
            await self.close()

        await self.channel_layer.group_add(self.chat_room, self.channel_name)

        # accept the WebSocket connection
        await self.accept()

    async def receive(self, text_data):
        message = text_data

        # create a message object
        model =  await sync_to_async(Message.objects.create)(
            match=self.match,
            sender=self.sender,
            message=message,
        )
        
        # Broadcast the message to all WebSocket connections in the chat room group
        await self.channel_layer.group_send(
            self.chat_room,
            {
                "type": "chat_message",
                "id": str(model.id),
                "sender": model.sender.name,
                "message": model.message,
                "sent_at": model.get_sent_time()
            },
        )

    async def disconnect(self, close_code):
        # Remove the consumer from the chat room group
        await self.channel_layer.group_discard(self.chat_room, self.channel_name)


    async def chat_message(self, event):
        # send a message to the WebSocket connection that triggered the receive() method
        await self.send(text_data=json.dumps(event))
