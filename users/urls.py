from django.urls import path
from .views import (
    artisan_register, 
    client_register,
    user_login,
    get_user_profile,
    update_user_profile,
    get_logged_in_user,
)


urlpatterns = [
    path('artisan/register/', artisan_register, name='artisan-register'),
    path('client/register/', client_register, name='client-register'),
    path('login/', user_login, name='user-login'),
    path('profile/', get_user_profile, name='get-user-profile'),
    path('profile/update/', update_user_profile, name='update-user-profile'),
    path('me/', get_logged_in_user, name='get_logged_in_user'),
]
