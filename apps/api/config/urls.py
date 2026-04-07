from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Vibe Engine 어드민"
admin.site.site_title = "Vibe Engine Admin"
admin.site.index_title = "운영 관리"

urlpatterns = [
    path('admin/', admin.site.urls),
    path(route='api/', view=include('core.urls')),
]
