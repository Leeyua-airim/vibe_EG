from django.urls import path
from .views import health_check, app_generator_generate_spec, generated_app_scaffold

urlpatterns = [
    path(route='health/', view=health_check, name='health_check'),
    path(route='app-generator/generate-spec',
        view=app_generator_generate_spec, 
        name='app_generator_generate_spec'),
    
    path(route='app-generator/<int:app_id>/scaffold',
        view=generated_app_scaffold, 
        name='generated_app_scaffold'),
    ]