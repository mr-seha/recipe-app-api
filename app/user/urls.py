from django.urls import path

from .views import CreateTokenView, UserCreateView, ManageUserView

app_name = "user"
urlpatterns = [
    path("create/", UserCreateView.as_view(), name="create"),
    path("token/", CreateTokenView.as_view(), name="token"),
    path("me/", ManageUserView.as_view(), name="me")
]
