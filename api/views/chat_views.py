from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers

class ConversationModelViewSet(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None):
        pass
    
    def post(self, request, pk=None):
        current_profile = request.user
        
        try: 
            match = models.Match.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response({"detail": "Match does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        
        # check if the two profiles of the match already have a conversation
        
    
    
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