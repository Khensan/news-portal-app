from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    #  Django Admin Interface Panel 
    path('admin/', admin.site.urls),
    
    #  Route all root URL requests directly to your custom news_api app
    path('', include('news_api.urls')), 
]
