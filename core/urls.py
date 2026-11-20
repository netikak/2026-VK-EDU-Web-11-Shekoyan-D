from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import LoginForm


urlpatterns = [
    path('login/', LoginView.as_view(
        template_name='core/login.html', authentication_form=LoginForm,
        extra_context={'hide_ask': True},
    ), name='login'),
    path('logout/', LogoutView.as_view(next_page='index', http_method_names=['post']), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
]
