from django.urls import path
from django.views.generic import RedirectView

from . import views



app_name = 'accounts'
urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('', RedirectView.as_view(pattern_name='accounts:signin', permanent=False)),
    path('signout/', views.signout, name='signout'),

    
]