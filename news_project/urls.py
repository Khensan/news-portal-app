# news_project/news_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Admin Interface Panel 
    path('admin/', admin.site.urls),
    
    # Built-in Auth views (login, logout, password resets)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Route all root URL requests directly down to your custom news_api app
    path('', include('news_api.urls')), 
]
