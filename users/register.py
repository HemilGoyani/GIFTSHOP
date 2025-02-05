
from django.contrib.auth import authenticate
from users.models import User
import os


def register_social_user(provider, user_id, email, name):
    filtered_user_by_email = User.objects.filter(email=email).first()

    if filtered_user_by_email:

        if provider == filtered_user_by_email.auth_provider:

            registered_user = authenticate(
                email=email, password=os.environ.get('SOCIAL_SECRET'))

            return {
                'status': True,
                'email': registered_user.email,
                'tokens': registered_user.tokens(),
                'message': 'Login successfully.'
            }

        else:
            return {
                "status": False,
                "message": 'Please continue your login using ' + filtered_user_by_email.auth_provider.title()
            }
   
    else:
        user = {
            'email': email,
            'password': os.environ.get('SOCIAL_SECRET')}
        user = User.objects.create_user(**user)
        user.auth_provider = provider
        user.save()

        new_user = authenticate(
            email=email, password=os.environ.get('SOCIAL_SECRET'))
        return {
            'status': True,
            'email': new_user.email,
            'tokens': new_user.tokens(),
            'message': 'Login successfully.'
        }