import datetime
from typing import Optional

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from common.rest.exceptions import ErrorCodeException, ErrorCode
from common.rest.views import ActiveUserAPIViewMixin, BaseAPIViewMixin
from common.utils import utc_localize

from .serializers import LoginRequestSerializer, LoginResponseSerializer, MeSerializer


class MeView(ActiveUserAPIViewMixin, generics.RetrieveAPIView):
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)


class LoginView(BaseAPIViewMixin, generics.CreateAPIView):
    serializer_class = LoginRequestSerializer

    def post(self, request, *args, **kwargs):
        request_serializer: LoginRequestSerializer = self.get_serializer(data=request.data)
        request_serializer.raise_validation_error_if_any()

        username: str = request_serializer.validated_data["username"]
        password: str = request_serializer.validated_data["password"]

        user: Optional[User] = authenticate(username=username, password=password)
        if user is None:
            raise ErrorCodeException(ErrorCode.bad_request)

        token: AccessToken = AccessToken.for_user(user)
        response_serializer: LoginResponseSerializer = LoginResponseSerializer(
            data={"session_token": str(token), "expire_time": self._retrieve_expiry_dt(token)}
        )
        response_serializer.is_valid()

        return self.generate_no_error_response(response_serializer.data)

    def _retrieve_expiry_dt(self, token: AccessToken) -> datetime.datetime:
        expiry_ts: int = token.payload["exp"]
        return utc_localize(datetime.datetime.fromtimestamp(expiry_ts))
