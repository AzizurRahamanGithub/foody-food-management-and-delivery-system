import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """Single WebSocket consumer to handle all chat functionality"""
    
    async def connect(self):
        # Check if user is authenticated
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close(code=4001)  # Unauthorized
            return

        self.current_user = self.scope["user"]
        
        # Join user to their personal room for receiving messages
        self.user_room = f"user_{self.current_user.id}"
        await self.channel_layer.group_add(self.user_room, self.channel_name)
        
        await self.accept()
        
        # Send connection success message
        await self.send(text_data=json.dumps({
            "action": "connected",
            "success": True,
            "message": f"Connected as {self.current_user.username}",
            "user_id": self.current_user.id
        }))

    async def disconnect(self, close_code):
        # Leave user room
        if hasattr(self, 'user_room'):
            await self.channel_layer.group_discard(self.user_room, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action', 'send_message')

            # Handle different actions
            if action == 'send_message':
                await self.handle_send_message(data)
            elif action == 'get_chat_history':
                await self.handle_get_chat_history(data)
            elif action == 'get_chat_users':
                await self.handle_get_chat_users(data)
            elif action == 'mark_as_read':
                await self.handle_mark_as_read(data)
            elif action == 'get_unread_count':
                await self.handle_get_unread_count(data)
            else:
                # Default action is send_message if no action specified
                await self.handle_send_message(data)

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"An error occurred: {str(e)}")

    async def handle_send_message(self, data):
        """Handle sending a message to another user"""
        receiver_id = data.get("receiverId") or data.get("receiver_id")
        message = data.get("message", "").strip()
        
        if not receiver_id:
            await self.send_error("receiverId is required")
            return
            
        if not message:
            await self.send_error("message cannot be empty")
            return

        # Check if receiver exists
        receiver_exists = await self.check_user_exists(receiver_id)
        if not receiver_exists:
            await self.send_error("Receiver not found")
            return

        # Check if trying to send to self
        if int(receiver_id) == self.current_user.id:
            await self.send_error("Cannot send message to yourself")
            return

        # Save message to database
        saved_message = await self.save_message(self.current_user.id, receiver_id, message)

        # Create message data
        message_data = {
            "action": "new_message",
            "message_id": saved_message.id,
            "message": message,
            "sender_id": self.current_user.id,
            "sender_username": self.current_user.username,
            "sender_photo": str(self.current_user.photo) if hasattr(self.current_user, 'photo') and self.current_user.photo else None,
            "receiver_id": int(receiver_id),
            "timestamp": saved_message.timestamp.isoformat(),
            "is_read": False
        }

        # Send to receiver's room
        await self.channel_layer.group_send(
            f"user_{receiver_id}",
            {
                "type": "chat_message",
                "message": message_data
            }
        )

        # Send confirmation back to sender
        await self.send(text_data=json.dumps({
            "action": "received_message",
            "success": True,
            "data": message_data
        }))

    async def handle_get_chat_history(self, data):
        """Get chat history with specific user"""
        other_user_id = data.get("user_id") or data.get("userId")
        
        if not other_user_id:
            await self.send_error("user_id is required")
            return

        # Get chat history
        messages = await self.get_chat_history(self.current_user.id, other_user_id)
        
        # Mark messages from other user as read
        read_count = await self.mark_messages_read(other_user_id, self.current_user.id)
        
        await self.send(text_data=json.dumps({
            "action": "chat_history",
            "success": True,
            "data": messages,
            "count": len(messages),
            "marked_read": read_count
        }))

    async def handle_get_chat_users(self, data):
        """Get list of users current user has chatted with"""
        chat_users = await self.get_chat_users()
        
        await self.send(text_data=json.dumps({
            "action": "chat_users",
            "success": True,
            "data": chat_users,
            "count": len(chat_users)
        }))

    async def handle_mark_as_read(self, data):
        """Mark messages from specific user as read"""
        sender_id = data.get("sender_id") or data.get("senderId")
        
        if not sender_id:
            await self.send_error("sender_id is required")
            return

        count = await self.mark_messages_read(sender_id, self.current_user.id)
        
        await self.send(text_data=json.dumps({
            "action": "marked_as_read",
            "success": True,
            "count": count,
            "sender_id": int(sender_id)
        }))

    async def handle_get_unread_count(self, data):
        """Get total unread messages count"""
        total_unread = await self.get_total_unread_count()
        
        await self.send(text_data=json.dumps({
            "action": "unread_count",
            "success": True,
            "total_unread": total_unread
        }))

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            "action": "error",
            "success": False,
            "error": message
        }))

    # Message handler for receiving messages from channel layer
    async def chat_message(self, event):
        """Handle message broadcast from channel layer"""
        await self.send(text_data=json.dumps(event["message"]))

    # Database operations
    @database_sync_to_async
    def check_user_exists(self, user_id):
        """Check if user exists"""
        return User.objects.filter(id=user_id).exists()

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message):
        """Save message to database"""
        from .models import ChatMessage
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        return ChatMessage.objects.create(
            sender=sender, 
            receiver=receiver, 
            message=message
        )

    @database_sync_to_async
    def get_chat_history(self, user1_id, user2_id):
        """Get chat history between two users"""
        from .models import ChatMessage
        messages = ChatMessage.objects.filter(
            Q(sender_id=user1_id, receiver_id=user2_id) |
            Q(sender_id=user2_id, receiver_id=user1_id)
        ).order_by('timestamp').select_related('sender', 'receiver')

        return [{
            "id": msg.id,
            "message": msg.message,
            #sender
            "sender_id": msg.sender.id,
            "sender_username": msg.sender.username,
            "sender_first_name": msg.sender.first_name,
            "sender_last_name": msg.sender.last_name,
            "sender_photo": str(msg.sender.photo) if hasattr(msg.sender, 'photo') and msg.sender.photo else None,
            #receiver
            "receiver_id": msg.receiver.id,
            "receiver_username": msg.receiver.username,
            "receiver_first_name": msg.receiver.first_name,
            "receiver_last_name": msg.receiver.last_name,
            "receiver_photo": str(msg.receiver.photo) if hasattr(msg.receiver, 'photo') and msg.receiver.photo else None,
            
            "timestamp": msg.timestamp.isoformat(),
            "is_read": msg.is_read
        } for msg in messages]

    @database_sync_to_async
    def get_chat_users(self):
        """Get all users that current user has chatted with"""
        from .models import ChatMessage
        
        # Get all users that have chatted with current user
        chat_user_ids = ChatMessage.objects.filter(
            Q(sender=self.current_user) | Q(receiver=self.current_user)
        ).values_list('sender_id', 'receiver_id')
        
        # Collect unique user IDs (excluding current user)
        user_ids = set()
        for sender_id, receiver_id in chat_user_ids:
            if sender_id != self.current_user.id:
                user_ids.add(sender_id)
            if receiver_id != self.current_user.id:
                user_ids.add(receiver_id)
        
        # Get users with their last message details
        users = User.objects.filter(id__in=user_ids)
        chat_users = []
        
        for user in users:
            # Get last message between current user and this user
            last_message = ChatMessage.objects.filter(
                Q(sender=self.current_user, receiver=user) |
                Q(sender=user, receiver=self.current_user)
            ).order_by('-timestamp').first()
            
            # Get unread count from this user
            unread_count = ChatMessage.objects.filter(
                sender=user,
                receiver=self.current_user,
                is_read=False
            ).count()
            
            chat_users.append({
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "photo": str(user.photo) if hasattr(user, 'photo') and user.photo else None,
                "last_message": last_message.message[:50] + '...' if last_message and len(last_message.message) > 50 else (last_message.message if last_message else None),
                "last_message_time": last_message.timestamp.isoformat() if last_message else None,
                "unread_count": unread_count,
                "is_online": False  
            })
        
        # Sort by last message time (most recent first)
        chat_users.sort(key=lambda x: x['last_message_time'] or '', reverse=True)
        
        return chat_users

    @database_sync_to_async
    def mark_messages_read(self, sender_id, receiver_id):
        """Mark messages as read"""
        from .models import ChatMessage
        return ChatMessage.objects.filter(
            sender_id=sender_id,
            receiver_id=receiver_id,
            is_read=False
        ).update(is_read=True)

    @database_sync_to_async
    def get_total_unread_count(self):
        """Get total unread messages count for current user"""
        from .models import ChatMessage
        return ChatMessage.objects.filter(
            receiver=self.current_user,
            is_read=False
        ).count()
