from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Project, Task
from .serializers import ProjectSerializer, RegisterSerializer, TaskSerializer, UserSerializer

User = get_user_model()


def _set_auth_cookies(response: Response, request, access_token: str, refresh_token: str) -> None:
    access_max_age = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
    refresh_max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

    response.set_cookie(
        key=settings.AUTH_COOKIE_ACCESS,
        value=access_token,
        max_age=access_max_age,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key=settings.AUTH_COOKIE_REFRESH,
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/api/auth/refresh/",
    )

    # Ensure CSRF cookie is available for subsequent unsafe requests.
    get_token(request)


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=settings.AUTH_COOKIE_ACCESS,
        path="/",
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key=settings.AUTH_COOKIE_REFRESH,
        path="/api/auth/refresh/",
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


class CsrfView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(
            {
                "detail": "CSRF cookie initialisé.",
                "csrfToken": get_token(request),
            }
        )


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        response = Response(
            {
                "user": UserSerializer(user).data,
                "detail": "Inscription réussie.",
            },
            status=status.HTTP_201_CREATED,
        )
        _set_auth_cookies(response, request, str(refresh.access_token), str(refresh))
        return response


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        identifier = request.data.get("username") or request.data.get("email")
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {"detail": "username/email et password sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = identifier
        if "@" in identifier:
            user_by_email = User.objects.filter(email__iexact=identifier).first()
            if user_by_email:
                username = user_by_email.username

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Identifiants invalides."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "user": UserSerializer(user).data,
                "detail": "Connexion réussie.",
            }
        )
        _set_auth_cookies(response, request, str(refresh.access_token), str(refresh))
        return response


class CookieTokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_cookie = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if not refresh_cookie:
            return Response(
                {"detail": "Session expirée. Reconnecte-toi."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            current_refresh = RefreshToken(refresh_cookie)
        except TokenError:
            return Response(
                {"detail": "Refresh token invalide."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh_to_set = str(current_refresh)
        access_to_set = str(current_refresh.access_token)

        if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False):
            user_id = current_refresh.payload.get("user_id")
            if user_id is None:
                return Response(
                    {"detail": "Refresh token invalide."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": "Utilisateur introuvable."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            try:
                current_refresh.blacklist()
            except AttributeError:
                pass

            rotated_refresh = RefreshToken.for_user(user)
            refresh_to_set = str(rotated_refresh)
            access_to_set = str(rotated_refresh.access_token)

        response = Response({"detail": "Session rafraîchie."})
        _set_auth_cookies(response, request, access_to_set, refresh_to_set)
        return response


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_cookie = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if refresh_cookie:
            try:
                RefreshToken(refresh_cookie).blacklist()
            except (AttributeError, TokenError):
                pass

        response = Response(status=status.HTTP_204_NO_CONTENT)
        _clear_auth_cookies(response)
        return response


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProjectRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_project(self):
        return get_object_or_404(Project, id=self.kwargs["project_id"], owner=self.request.user)

    def get_queryset(self):
        return Task.objects.filter(project=self.get_project())

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class TaskRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_project(self):
        return get_object_or_404(Project, id=self.kwargs["project_id"], owner=self.request.user)

    def get_queryset(self):
        return Task.objects.filter(project=self.get_project())
