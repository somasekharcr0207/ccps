from rest_framework import generics, status
from rest_framework.response import Response

from .models import Card
from .serializers import CardCreateSerializer, CardSerializer


class CardListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return CardCreateSerializer if self.request.method == "POST" else CardSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = serializer.save(user=request.user)
        return Response(CardSerializer(card).data, status=status.HTTP_201_CREATED)


class CardDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = CardSerializer

    def get_queryset(self):
        # users can only ever touch their own cards
        return Card.objects.filter(user=self.request.user)
