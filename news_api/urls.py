"""
URL Routing Configuration for the News Portal.

Maps address paths to corresponding public template views, authenticated 
editor dashboard areas, browser logouts, and REST API network endpoints.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    #  Root path mapping (Can serve as your reader homepage)
    path('', views.article_list_html, name='system_landing_page'),
    
    #  Reader Web Template Paths (Fixes Issue 3)
    path('articles/<int:pk>/', views.article_detail, name='article_detail_html'),
    path('newsletters/', views.newsletter_list, name='newsletter_list_html'),

    #  Editor Dashboard & Review Panels (Fixes Issue 1)
    path('dashboard/', views.portal_html_dashboard, name='editorial_dashboard'),
    path('review/', views.review_articles_list, name='review_list'),
    path('review/approve/<int:article_id>/', views.approve_article_action, name='approve_action'),

    #  Web Browser Authentication Routes (Fixes Issue 2)
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # REST Framework Token Endpoints & Core API Channels
    path('api/login/', obtain_auth_token, name='api_token_auth'),
    path('api/approved/', views.APIApprovedLogEndpoint.as_view(), name='api_approved_log'),
    path('api/articles/', views.ArticleListCreateAPIView.as_view(), name='article_list_create'),
    path('api/articles/subscribed/', views.ArticleSubscribedListAPIView.as_view(), name='article_subscribed'),
    path('api/articles/<int:pk>/', views.ArticleDetailAPIView.as_view(), name='article_detail'),
]
