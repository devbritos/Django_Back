# proyecto/urls.py (el urls.py raíz)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('personal/', include('personal.urls')),
]