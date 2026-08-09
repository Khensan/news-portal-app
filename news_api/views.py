"""
Views Module for the News Portal Application.
Handles public reader HTML template rendering, secure editorial dashboard administration,
and Django REST Framework API endpoints for content syndication.
"""
import requests
from django.db import models
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse

from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse

from .models import Article, Newsletter
from .serializers import ArticleSerializer, NewsletterSerializer
from .permissions import IsJournalist, IsEditor, IsEditorOrJournalist

User = get_user_model()

# ==========================================
# READER-FACING WEB TEMPLATE VIEWS (Issue 3)
# ==========================================

def article_list(request):
    """

    Renders the public homepage view displaying all approved articles.
    
    """
    articles = Article.objects.filter(approved=True).order_by('-created_at')
    return render(request, 'news_api/home.html', {'articles': articles})


def article_detail(request, pk):
    """

    Renders an individual approved article detail layout view for public readers.
    
    """
    article = get_object_or_404(Article, pk=pk, approved=True)
    return render(request, 'news_api/article_detail.html', {'article': article})


def newsletter_list(request):
    """

    Renders the newsletter archive platform index page.
    
    """
    newsletters = Newsletter.objects.all().order_by('-created_at')
    return render(request, 'news_api/newsletter_list.html', {'newsletters': newsletters})


# ==========================================
# TEMPLATE-BASED VIEWS & ACCESS CONTROL
# ==========================================

@api_view(['GET'])
def api_root_landing(request, format=None):
    """

    Core Landing Page Index for the News Portal API engine.
    
    """
    return Response({
        'message': 'Welcome to the News Portal API engine!',
        'documentation': {
            'authenticate_token_login': reverse('api_token_auth', request=request, format=format),
            'all_articles_endpoint': reverse('article_list_create', request=request, format=format),
            'subscribed_feed_endpoint': reverse('article_subscribed', request=request, format=format),
            'approved_logs_endpoint': reverse('api_approved_log', request=request, format=format),
            'review_panel_ui': request.build_absolute_uri('/review/'),
            'portal_html_dashboard': request.build_absolute_uri('/dashboard/'),
        }
    })


def is_editor_check(user):
    return user.is_authenticated and getattr(user, 'role', None) == 'EDITOR'


@login_required
@user_passes_test(is_editor_check)
def portal_html_dashboard(request):
    """
    Render the administrative editorial control panel workspace.
    Accessible only to authenticated users with an 'EDITOR' role profile flag.
    """
    pending_count = Article.objects.filter(approved=False).count()
    approved_count = Article.objects.filter(approved=True).count()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>News Portal - Editorial Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background-color: #f4f7f6; color: #333; margin: 0; }}
            .navbar {{ background-color: #2c3e50; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }}
            .navbar h1 {{ margin: 0; font-size: 24px; }}
            .navbar a {{ color: #ecf0f1; text-decoration: none; font-weight: bold; margin-left: 20px; }}
            .container {{ max-width: 1000px; margin: 40px auto; padding: 0 20px; }}
            .hero {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; margin-bottom: 30px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .card {{ background: white; padding: 25px; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #2c3e50; }}
            .card.alert-card {{ border-top-color: #e74c3c; }}
            .stat-num {{ font-size: 36px; font-weight: bold; margin: 10px 0; color: #2c3e50; }}
            .card.alert-card .stat-num {{ color: #e74c3c; }}
            .btn-action {{ display: inline-block; margin-top: 15px; padding: 10px 20px; background-color: #2c3e50; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px; text-transform: uppercase; }}
            .btn-action:hover {{ background-color: #34495e; }}
            .btn-action.btn-danger {{ background-color: #e74c3c; }}
            .btn-action.btn-danger:hover {{ background-color: #c0392b; }}
        </style>
    </head>
    <body>
        <nav class="navbar">
            <h1>📰 News Portal System</h1>
            <div>
                <a href="/">View Public Site</a>
                <a href="/accounts/logout/">Sign Out ({request.user.username})</a>
            </div>
        </nav>
        <div class="container">
            <div class="hero">
                <h2>Welcome back to the Editorial Control Hub</h2>
                <p>Logged in as: <strong>{request.user.get_full_name() or request.user.username}</strong> ({request.user.role})</p>
            </div>
            
            <div class="grid">
                <div class="card alert-card">
                    <h3>Moderation Queue</h3>
                    <div class="stat-num">{pending_count}</div>
                    <p>Articles awaiting factual authorization and subscriber dispatch notifications.</p>
                    <a href="/review/" class="btn-action btn-danger">Open Review Queue</a>
                </div>
                
                <div class="card">
                    <h3>Published Directory</h3>
                    <div class="stat-num">{approved_count}</div>
                    <p>Live entries currently broadcasted to readers and accessible through public API feeds.</p>
                    <a href="/" class="btn-action">View Live Feed</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content)


@login_required
@user_passes_test(is_editor_check)
def review_articles_list(request):
    unapproved_articles = Article.objects.filter(approved=False)
    return render(request, 'news_api/review_list.html', {'articles': unapproved_articles})


@login_required
@user_passes_test(is_editor_check)
def approve_article_action(request, article_id):
    """
    Process article approval validation states via POST transaction.    
    Triggers automated subscriber email dispatches and web service receipt handshakes.
    """    
    if request.method == 'POST':
        article = get_object_or_404(Article, id=article_id)
        article.approved = True
        article.save()

        recipient_emails = []
        journalist_subs = article.author.journalist_subscribers.all()
        recipient_emails.extend([sub.email for sub in journalist_subs if sub.email])
        
        if article.publisher:
            pub_subs = article.publisher.reader_subscribers.all()
            recipient_emails.extend([sub.email for sub in pub_subs if sub.email])

        recipient_emails = list(set(recipient_emails))

        if recipient_emails:
            send_mail(
                subject=f"New Article Released: {article.title}",
                message=f"Read our latest drop via {article.author.get_full_name()}.",
                from_email="noreply@newsnetwork.local",
                recipient_list=recipient_emails,
                fail_silently=True
            )

        domain = request.build_absolute_uri('/')[:-1]
        try:
            requests.post(f"{domain}/api/approved/", json={"article_id": article.id, "status": "APPROVED"}, timeout=5)
        except requests.exceptions.RequestException:
            pass 

        return HttpResponseRedirect('/review/')


class APIApprovedLogEndpoint(APIView):
    permission_classes = [permissions.AllowAny] 
    def post(self, request):
        return Response({"status": "Receipt acknowledged securely"}, status=status.HTTP_200_OK)


# ==========================================
# RESTFUL API ENDPOINTS
# ==========================================

class APIApprovedLogEndpoint(APIView):
    """
    API receiver endpoint validating external editorial authorization acknowledgements.    
    Accepts safe open POST payloads from system moderation triggers.
    """
    permission_classes = [permissions.AllowAny] 
    def post(self, request):
        return Response({"status": "Receipt acknowledged securely"}, status=status.HTTP_200_OK)


class ArticleListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint for listing published articles or submitting new draft records.    
    Creation features are limited exclusively to authenticated Journalists.
    """
    queryset = Article.objects.filter(approved=True)
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ArticleSubscribedListAPIView(generics.ListAPIView):
    """

    Returns custom timeline of approved articles from subscribed sources.
    
    """
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        subscribed_journalists = user.subscribed_journalists.all()
        subscribed_publishers = user.subscribed_publishers.all()
        
        return Article.objects.filter(
            models.Q(author__in=subscribed_journalists) | 
            models.Q(publisher__in=subscribed_publishers),
            approved=True
        ).distinct().order_by('-created_at')


class ArticleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """

    Handles retrieving, updating, and deleting a single article instance.
    
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsEditorOrJournalist]


class NewsletterListCreateAPIView(generics.ListCreateAPIView):
    """

    Handles listing out newsletters and creating new newsletter collections.
    
    """
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsJournalist]

