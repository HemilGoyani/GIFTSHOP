from django.urls import path
from .views import UserListView,  UserDeleteView, UserProfileView

urlpatterns = [
    path('', UserListView.as_view(), name='user_list'),
    path('<int:pk>/', UserListView.as_view(), name='user_detail'),  # Fetch a specific user by ID
    path('delete/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]

