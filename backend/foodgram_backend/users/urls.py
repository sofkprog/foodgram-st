from django.urls import path
from api.users.views import (
    UserListRegisterView,
    UserDetailView,
    UserMeView,
    AvatarView,
    SetPasswordView,
    CustomAuthToken,
    LogoutView,
)
from api.users.subscriptions import SubscriptionListView, SubscribeView

urlpatterns = [
    path("auth/token/login/", CustomAuthToken.as_view(), name="token-login"),
    path("auth/token/logout/", LogoutView.as_view(), name="token-logout"),
    path("users/", UserListRegisterView.as_view(), name="user-list-register"),
    path("users/<int:id>/", UserDetailView.as_view(), name="user-detail"),
    path("users/me/", UserMeView.as_view(), name="user-me"),
    path("users/me/avatar/", AvatarView.as_view(), name="user-avatar"),
    path("users/set_password/", SetPasswordView.as_view(), name="user-set-password"),
]

urlpatterns += [
    path(
        "users/subscriptions/",
        SubscriptionListView.as_view(),
        name="user-subscriptions",
    ),
    path("users/<int:id>/subscribe/", SubscribeView.as_view(), name="user-subscribe"),
]
