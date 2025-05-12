from rest_framework import generics, authentication
from rest_framework import permissions
from rest_framework.authtoken import views
from rest_framework.settings import api_settings

from .serializers import AuthTokenSerializer, UserSerializer


class UserCreateView(generics.CreateAPIView):
    serializer_class = UserSerializer


class CreateTokenView(views.ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    # queryset = get_user_model().objects.all()
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
