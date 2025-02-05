from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserListView, PasswordChangeView, PasswordResetRequestView, PasswordResetConfirmView, UserDeleteView, UserProfileView

urlpatterns = [
    path('', UserListView.as_view(), name='user_list'),
    path('delete/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]