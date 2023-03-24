from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from api import models, serializers


class ConversationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        current_profile = request.user
        conversations = current_profile.conversations.all()
        serializer = serializers.ConversationSerializer(conversations, many=True)
        return Response(serializer.data)
    
    # TODO: retreieve conversation

    def post(self, request, pk=None):
        current_profile = request.user

        try:
            match = models.Match.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Match does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )
            
        profile1 = match.profile1
        profile2 = match.profile2
        
        if current_profile is not profile1 and current_profile is not profile2:
            return Response({"detail": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED)

        # check if the two profiles of the match already have a conversation
        conversation = models.Conversation.objects.filter(
            Q(participants=profile1) & Q(participants=profile2)
        ).first()
        
        if conversation:
            serializer = serializers.ConversationSerializer(conversation, many=False)
            return Response(serializer.data)
        
        new_conversation = models.Conversation.objects.create(type="private")
        new_conversation.participants.add(profile1)
        new_conversation.participants.add(profile2)
        new_conversation.save()
        
        serializer = serializers.ConversationSerializer(new_conversation, many=False)
        return Response(serializer.data)
    
    

        # TODO: delete conversation

class MessageModelViewSet(ModelViewSet):
    queryset = models.Message.objects.all()
    serializer_class = serializers.MessageSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path=r"actions/delete-all")
    def delete_all(self, request):
        messages = models.Message.objects.all()
        for msg in messages:
            msg.delete()
        return Response({"detail": "success"}, status=status.HTTP_200_OK)
