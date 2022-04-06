from django.contrib.auth.models import User

from rest_framework_simplejwt import authentication
from rest_framework_simplejwt.exceptions import InvalidToken


class JWTTokenUserAuthentication(authentication.JWTTokenUserAuthentication):
    def get_user(self, validated_token):
        """
        Returns a model user object which is backed by the given validated token.
        """
        token_user = super().get_user(validated_token)
        user = User.objects.filter(id=token_user.id).first()
        if not user:
            raise InvalidToken(detail="No matching user")
        return user
