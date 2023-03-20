import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Match, Chat, Message

class ChatConsumer(AsyncJsonWebsocketConsumer):
  
  
  async def connect(self):
      # Connection with the websocket is established, 
      # room_name is given by the client passing the match_id as 'room_name'
      self.room_name = self.scope['url_route']['kwargs']['room_name']
      self.room_group_name = 'chat_'+str(self.room_name)
      # Room is added to the channel layer, layers allow the transfer of data throughout
      # the websocket for each participant in the current channel
      await (self.channel_layer.group_add(self.room_group_name, self.channel_name))
      await self.accept()
      
      
  async def receive(self, text_data=None, bytes_data=None):
      data = json.loads(text_data)
      message = data['message']
      sender = data['sender']
      
      # Here the message is created in the DB linking to its match, getting the match by its id.
      # await sync_to_async(Match.objects.get(id=data["match"]).exists())()
      await sync_to_async(Chat(match_id=self.room_name, message=message, sender=sender).save)()
      # The received message is sent back so it can be returned to all participants in the channel
      await self.channel_layer.group_send(
          self.room_group_name,
          {
              'type': 'send_back',
              'message': message,
              'sender': sender
          },
      )
      
  # This is the function that specifies the way data will be sent back to the websocket
  async def send_back(self, event):
      message = event['message']
      sender = event['sender']
      await self.send(text_data=json.dumps({
          'message': message,
          'sender': sender,
      }))
  async def disconnect(self, code):
      # Shuts down connection to the websocket
      self.channel_layer.group_discard(
          self.room_group_name,
          self.channel_name
      )
  
  
    # async def connect(self):
    #     # Set the sender and receiver based on the currently authenticated user and the recipient specified in the URL route
    #     self.sender = self.scope['user']
    #     print(self.sender)
        
    #     self.receiver = self.scope['url_route']['kwargs']['receiver']
        
    #     # Find the match object that connects the sender and receiver
    #     match = Match.objects.filter(user1=self.sender, user2=self.receiver).first() or Match.objects.filter(user1=self.receiver, user2=self.sender).first()
    #     self.match = match
        
    #     # Create a unique chat room name based on the match ID and join the room
    #     self.chat = None
    #     self.chat_room = f'chat_{self.match.id}'
    #     await self.channel_layer.group_add(
    #         self.chat_room,
    #         self.channel_name
    #     )
        
    #     # Accept the WebSocket connection
    #     await self.accept()

    # async def disconnect(self, close_code):
    #     # Remove the consumer from the chat room group
    #     await self.channel_layer.group_discard(
    #         self.chat_room,
    #         self.channel_name
    #     )

    # async def receive(self, text_data):
    #     # Deserialize the incoming message and extract the message text
    #     data = json.loads(text_data)
    #     message = data['message']
        
    #     # If this is the first message for the chat, create a new Chat object
    #     if not self.chat:
    #         self.chat = Chat.objects.create(match=self.match)
        
    #     # Create a new Message object with the sender and message text, and associate it with the Chat object
    #     msg = Message.objects.create(chat=self.chat, sender=self.sender, message=message)
        
    #     # Broadcast the message to all WebSocket connections in the chat room group
    #     await self.channel_layer.group_send(
    #         self.chat_room,
    #         {
    #             'type': 'chat_message',
    #             'id': msg.id,
    #             'sender': msg.sender.username,
    #             'message': msg.message,
    #             'timestamp': msg.created_at.isoformat()
    #         }
    #     )

    # async def chat_message(self, event):
    #     # Send a message to the WebSocket connection that triggered the receive() method
    #     await self.send(text_data=json.dumps(event))