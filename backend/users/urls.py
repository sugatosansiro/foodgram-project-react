from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import path
from users import views

app_name = 'users'

urlpatterns = [
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'signup/',
        views.SignUp.as_view(),
        name='signup'
    ),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_change_form/',
        PasswordChangeView.as_view(
            template_name='registration/password_change_form.html'
        ),
        name='password_change_form'
    )
]
