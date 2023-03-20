from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Match, Chat, Message, Profile

import json


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Set the sender and receiver based on the currently authenticated user and the recipient specified in the URL route
        self.sender = self.scope["profile"]
        
        print ("user -> ", self.sender)
        
        self.chat_room = self.scope["url_route"]["kwargs"]["match_id"]
        
        print ("group name -> ", self.chat_room)
        
        await self.channel_layer.group_add(self.chat_room, self.channel_name)
        
        self.chat = None
        # Accept the WebSocket connection
        await self.accept()
        
    async def receive(self, text_data):
        # Deserialize the incoming message and extract the message text
        data = json.loads(text_data)
        message = data["message"]

        # If this is the first message for the chat, create a new Chat object
        if not self.chat:
            self.chat = Chat.objects.create(match=self.match)

        # Create a new Message object with the sender and message text, and associate it with the Chat object
        msg = Message.objects.create(
            chat=self.chat, sender=self.sender, message=message
        )

        # Broadcast the message to all WebSocket connections in the chat room group
        await self.channel_layer.group_send(
            self.chat_room,
            {
                "type": "chat_message",
                "id": msg.id,
                "sender": msg.sender.username,
                "message": msg.message,
                "timestamp": msg.created_at.isoformat(),
            },
        )
        
        
    async def disconnect(self, close_code):
        # Remove the consumer from the chat room group
        await self.channel_layer.group_discard(self.chat_room, self.channel_name)

    async def chat_message(self, event):
        # Send a message to the WebSocket connection that triggered the receive() method
        await self.send(text_data=json.dumps(event))
