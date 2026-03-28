from django.urls import path

from .views import (
    CookieTokenRefreshView,
    CsrfView,
    LoginView,
    LogoutView,
    MeView,
    ProjectListCreateView,
    ProjectRetrieveUpdateDestroyView,
    RegisterView,
    TaskListCreateView,
    TaskRetrieveUpdateDestroyView,
)

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", CookieTokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("projects/", ProjectListCreateView.as_view(), name="project-list-create"),
    path("projects/<int:pk>/", ProjectRetrieveUpdateDestroyView.as_view(), name="project-detail"),
    path("projects/<int:project_id>/tasks/", TaskListCreateView.as_view(), name="task-list-create"),
    path("projects/<int:project_id>/tasks/<int:pk>/", TaskRetrieveUpdateDestroyView.as_view(), name="task-detail"),
]
