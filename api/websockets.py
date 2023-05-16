from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from api import models
import json


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # get scope from middleware
        self.sender_in_model = self.scope["sender_in_model"]

        # prevents someone from sending a message to any profile having a match id
        if not self.sender_in_model:
            await self.close()

        # get from middleware
        self.my_group_chat = self.scope["my_group_chat"]

        # get scope from middleware
        self.sender = self.scope["sender"]

        # get scope from middleware
        self.sender_photo = self.scope["sender_photo"]

        # get the scope from middleware
        self.model = self.scope["model"]

        # chat_room: the conversation id
        self.chat_room = self.scope["room_id"]

        # check if the user is authenticated, and if not, close the WebSocket connection
        if not self.sender.is_authenticated:
            await self.close()

        await self.channel_layer.group_add(self.chat_room, self.channel_name)

        # accept the WebSocket connection
        await self.accept()

    async def receive(self, text_data):
        message = text_data

        if self.my_group_chat:
            model = await sync_to_async(models.MyGroupMessage.objects.create)(
                group=self.model,
                sender=self.sender,
                message=message,
            )
        else:  # create a message object
            model = await sync_to_async(models.Message.objects.create)(
                conversation=self.model,
                sender=self.sender,
                message=message,
            )

        if self.sender_photo is not None:
            self.sender_photo = {
                "id": str(self.sender_photo["id"]),
                "image": str(self.sender_photo["image"]),
                "profile": str(self.sender_photo["profile"]),
            }

        # Broadcast the message to all WebSocket connections in the chat room group
        await self.channel_layer.group_send(
            self.chat_room,
            {
                "type": "chat_message",
                "id": str(model.id),
                "message": model.message,
                "sent_at": model.get_sent_time(),
                "sender_id": str(model.sender.id),
                "sender_name": str(model.sender.name),
                "sender_photo": self.sender_photo,
            },
        )

    async def disconnect(self, close_code):
        # Remove the consumer from the chat room group
        await self.channel_layer.group_discard(self.chat_room, self.channel_name)

    async def chat_message(self, event):
        # send a message to the WebSocket connection that triggered the receive() method
        await self.send(text_data=json.dumps(event))
