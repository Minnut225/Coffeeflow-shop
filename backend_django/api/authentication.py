from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import jwt
from django.conf import settings
from rest_framework import authentication, exceptions, permissions
from .models import User, UserRole

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request) -> Optional[Tuple[User, str]]:
        if request.path.endswith(('/auth/login', '/auth/login/')):
            return None

        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        token = parts[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if not username:
                raise exceptions.AuthenticationFailed("Invalid token payload")
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired")
        except jwt.PyJWTError:
            raise exceptions.AuthenticationFailed("Could not validate credentials")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")

        if not user.is_active:
            raise exceptions.PermissionDenied("User account is disabled")

        return (user, token)


class IsManager(permissions.BasePermission):
    message = "Operation not permitted. Requires MANAGER role."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.MANAGER)


class IsCashierOrManager(permissions.BasePermission):
    message = "Operation not permitted. Authentication required."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in [UserRole.MANAGER, UserRole.CASHIER]
        )
