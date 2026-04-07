from django.urls import path
from .views import health_check

urlpatterns = [
    path(route='health/', view=health_check, name='health_check'),
    ]