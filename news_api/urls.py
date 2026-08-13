"""
Defines routing patterns linking deterministic string paths directly onto targeted views.

Establishes structural boundaries between reader templates, role-based workspaces, 
multi-tenant publisher utilities, and Django REST Framework API resources.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from . import api_views

class LegacyLogoutView(auth_views.LogoutView):
    """
    Safely permits legacy GET request methods to trigger system logout loops.
    """
    def get(self, request, *args, **kwargs):
        """
        Maps a fallback GET invocation directly into a standard POST execution routine.
        """
        return self.post(request, *args, **kwargs)

# news_api/urls.py

# ... keep your standard auth, tokens, and mixin class imports here ...

app_name = 'news_api' 

urlpatterns = [
    # ==========================================
    # 1. CORE PUBLIC TEMPLATE INTERFACES
    # ==========================================
    path('', views.article_list, name='system_landing_page'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('newsletters/', views.newsletter_list, name='newsletter_list'),

    # ==========================================
    # 2. USER ACCESS, ACCREDITATION & REDIRECTS
    # ==========================================
    path('register/', views.register_view, name='register'),
    path('dashboard/redirect/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='news_api/login.html'), name='login'),
    path('accounts/logout/', LegacyLogoutView.as_view(), name='logout'),

    # ==========================================
    # 3. ROLE-BASED DASHBOARDS & WORKSPACES
    # ==========================================
    path('dashboard/editor/', views.portal_html_dashboard, name='editorial_dashboard'),
    path('dashboard/reader/', views.reader_dashboard, name='reader_dashboard'),
    path('dashboard/journalist/', views.journalist_dashboard, name='journalist_dashboard'),
    path('dashboard/publisher/', views.publisher_dashboard_view, name='publisher_dashboard'),
    # ==========================================
    # 4. MULTI-TENANT PUBLISHER ASSIGNMENT UTILITIES
    # ==========================================
    path('publisher/new/', views.create_publisher_standalone_view, name='create_publisher_standalone'),
    path('publisher/manage-team/', views.assign_staff_view, name='manage_team'),
    path('management/publisher/init/', views.admin_initialize_publisher_view, name='admin_initialize_publisher'),

    # ==========================================
    # 5. CONTENT GRAPHICAL CRUD & MODERATION BLOCKS
    # ==========================================
    # CRITICAL VERIFICATION: Confirm this path references review_articles_list
    # and NOT article_list. This separates your data streams completely.
    path('review/', views.review_articles_list, name='review_list'),
    
    path('review/approve/<int:article_id>/', views.approve_article_action, name='approve_article_action'),
    path('articles/create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('articles/<int:pk>/edit/', views.ArticleUpdateView.as_view(), name='article_update'),
    path('articles/<int:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),        
    path('newsletters/create/', views.NewsletterCreateView.as_view(), name='newsletter_create'),

    # ==========================================
    # 6. RESTFUL API ENDPOINTS & LOG pipelines
    # ==========================================
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/login-token/', obtain_auth_token, name='api_token_auth'),
    path('api/approved/', views.APIApprovedLogEndpoint.as_view(), name='api_approved_log'),        

    # DRF Sub-Resource Endpoints
    path('api/articles/', api_views.ArticleListCreateAPIView.as_view(), name='api_article_list_create'),
    path('api/articles/subscribed/', api_views.SubscribedArticlesAPIView.as_view(), name='api_subscribed_articles'),
    path('api/articles/<int:pk>/', api_views.ArticleDetailAPIView.as_view(), name='api_article_detail'),    
    path('api/newsletters/', views.NewsletterListCreateAPIView.as_view(), name='api_newsletters_list_create'),
]
