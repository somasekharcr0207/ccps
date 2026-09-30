from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import LogoutSerializer, RegisterSerializer, UserSerializer


class AuthThrottle(AnonRateThrottle):
    rate = "30/min"


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (AuthThrottle,)


class LoginView(TokenObtainPairView):
    """Returns access + refresh JWT."""
    throttle_classes = (AuthThrottle,)


class RefreshView(TokenRefreshView):
    throttle_classes = (AuthThrottle,)


class LogoutView(APIView):
    """Blacklists the refresh token so it can no longer be used."""
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveAPIView):
    """Protected route: current user profile."""
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
