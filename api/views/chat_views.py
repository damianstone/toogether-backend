from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers

import api.utils.gets as g
import api.utils.checks as c


class ConversationViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        # TODO: order the conversations based on the newest messages
        current_profile = request.user
        conversations = current_profile.conversations.all().order_by("-created_at")

        # list all the conversation with at least one message
        conversations_w_messsages = []

        for conv in conversations:
            converation = c.check_conversation_with_messages(conv)
            if converation:
                conversations_w_messsages.append(conv)

        serializer = serializers.ConversationSerializer(
            conversations_w_messsages, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path=r"messages")
    def list_messages(self, request, pk=None):
        current_profile = request.user

        try:
            conversation = models.Conversation.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response({"detail": "Conversation does not exist"})

        participants = conversation.participants.all()

        if current_profile not in participants:
            return Response(
                {"detail": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        messages = models.Message.objects.filter(conversation=conversation)
        serializer = serializers.MessageSerializer(
            messages, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path=r"start")
    def start_conversation(self, request, pk=None):
        current_profile = request.user

        try:
            match = models.Match.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Match does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        profile1 = match.profile1
        profile2 = match.profile2

        if current_profile != profile1 and current_profile != profile2:
            print(current_profile)
            return Response(
                {"detail": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # check if the two profiles of the match already have a conversation
        conversation = g.get_conversation_between(profile1, profile2)

        if conversation:
            serializer = serializers.ConversationSerializer(conversation, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)

        new_conversation = models.Conversation.objects.create(type="private")
        new_conversation.participants.add(profile1)
        new_conversation.participants.add(profile2)
        new_conversation.save()

        serializer = serializers.ConversationSerializer(new_conversation, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        current_profile = request.user
        try:
            conversation = models.Conversation.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Conversation does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participants = conversation.participants.all()

        if current_profile not in participants:
            return Response(
                {"detail": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        conversation.delete()
        return Response({"detail": "deleted"}, status=status.HTTP_200_OK)
