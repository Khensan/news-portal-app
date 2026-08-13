# news_api/views.py
"""
Controller views managing core user interaction layers for the news portal ecosystem.

Handles public reader-facing interfaces, custom dynamic registrations linking 
tenant publisher workspaces, and administrative assignment/offboarding views for staff.
"""

import requests
from django.db import models
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.urls import reverse as django_reverse
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import views as auth_views
from django.middleware.csrf import get_token
from django.contrib.auth.mixins import UserPassesTestMixin


# Django REST Framework Components
from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse as drf_reverse  
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from .forms import CustomUserRegistrationForm
from django.http import HttpResponse



# App-Level Components
from .models import Article, Newsletter, Publisher
from .serializers import ArticleSerializer, NewsletterSerializer
from .permissions import IsJournalistUser, IsEditorOrJournalistUser
from .forms import CustomUserCreationForm
from django.contrib.auth.mixins import PermissionRequiredMixin  
from django.views.generic import CreateView, UpdateView, ListView, DetailView 
from .forms import PublisherCreationForm
from django.db import models
from rest_framework import generics, permissions
from .models import Article
from .serializers import ArticleSerializer
from .forms import AdminPublisherInitializationForm
from .forms import CustomUserCreationForm, PublisherCreationForm, ArticleModelForm



User = get_user_model()

# ==========================================
# PUBLIC READER-FACING TEMPLATE VIEWS
# ==========================================
def is_platform_admin_check(user):
    """
    Validates whether the authenticated user holds administrative platform capabilities.

    Checks against a custom role attribute field string or dedicated flag 
    to isolate master setup screens from standard readers or journalists.

    Args:
        user (CustomUser): Target system identity profile object instance under assessment.

    Returns:
        bool: True evaluation verification flags if explicit admin rights match.
    """
    # Replace with your system's exact admin flag property mapping configuration rule
    # Examples: getattr(user, 'is_admin', False) or user.role.lower() == 'admin'
    return user.is_authenticated and (getattr(user, 'role', 'reader').lower() == 'admin' or user.is_staff)


@user_passes_test(is_platform_admin_check)
def admin_initialize_publisher_view(request):
    """
    Initializes a Publisher independently from an Editor workspace session context.

    Saves the corporate profile record atomically and loops over the explicit 
    form arrays to assign designated editors and journalists to the organization.

    Args:
        request (HttpRequest): System container mapping context variables, profile roles, 
            and POST multi-attribute form data packages.

    Returns:
        HttpResponse: A redirected target loop routing back to the live landing directory, 
            or a rendered tabular entry form screen.
    """
    if request.method == 'POST':
        form = AdminPublisherInitializationForm(request.POST)
        if form.is_valid():
            # Wrap mutations inside an atomic block to protect multi-table data matrices
            with transaction.atomic():
                # 1. Establish the standalone publisher brand model row down to storage
                publisher = form.save()
                
                # 2. Extract and assign chosen Editor accounts cleanly
                selected_editors = form.cleaned_data.get('assign_editors')
                if selected_editors:
                    publisher.editors.add(*selected_editors)
                    
                # 3. Extract and assign chosen Staff Journalist accounts cleanly
                selected_journalists = form.cleaned_data.get('assign_journalists')
                if selected_journalists:
                    publisher.journalists.add(*selected_journalists)
                    
                # Persist modifications explicitly down to database storage tables
                publisher.save()
                
            return redirect('news_api:article_list')
    else:
        form = AdminPublisherInitializationForm()
        
    return render(request, 'news_api/admin_init_publisher.html', {'form': form})


def article_list(request):
    """
    Renders the public homepage view displaying all approved articles.

    Args:
        request (HttpRequest): Core incoming transactional payload request object.

    Returns:
        HttpResponse: Rendered homepage structural template populated with approved content items.
    """
    articles = Article.objects.filter(approved=True).order_by('-created_at')
    return render(request, 'news_api/home.html', {'articles': articles})


def article_detail(request, pk):
    """
    Renders an individual approved article detail layout view for public readers.

    Args:
        request (HttpRequest): Core incoming transactional payload request object.
        pk (int): Primary key identifier targeting a distinct database table article entry row.

    Returns:
        HttpResponse: Rendered narrative layout context view mapping the selected story.
    """
    article = get_object_or_404(Article, pk=pk, approved=True)
    return render(request, 'news_api/article_detail.html', {'article': article})


def newsletter_list(request):
    """
    Renders the newsletter archive platform index page.

    Args:
        request (HttpRequest): Core incoming transactional payload request object.

    Returns:
        HttpResponse: Rendered view housing the complete historical collection of dispatched digests.
    """
    newsletters_queryset = Newsletter.objects.all().order_by('-created_at')
    return render(request, 'news_api/newsletter_list.html', {'newsletters': newsletters_queryset})


def register_view(request):
    """
    Handles joint user registration and automated publisher profile provisioning.

    Processes incoming credentials. If a profile signs up under an organizational tier 
    and provides a brand title, an isolated Publisher row is generated atomically.

    Args:
        request (HttpRequest): Core incoming frame holding form parameters and session context.

    Returns:
        HttpResponse: A redirected routing instruction targeting the role dashboard, 
            or a re-rendered registration form block containing field error diagnostics.
    """
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # 1. Commit the core user account row first
                user = form.save()
                role = getattr(user, 'role', 'reader').lower()
                pub_name = form.cleaned_data.get('new_publisher_name', '').strip()

                # --- ATOMIC WORKSPACE PROVISIONING ---
                # Check for BOTH the role flag and an explicit text input entry string
                if (role == 'publisher' or role == 'editor') and pub_name:
                    publisher = Publisher.objects.create(name=pub_name)
                    # Automatically link the creating profile user into the management list
                    publisher.editors.add(user)
                    publisher.save()
                
                # --- PROCESS SECURITY GROUP SCHEMAS ---
                if role == 'journalist':
                    group, _ = Group.objects.get_or_create(name='Journalists')
                    content_type = ContentType.objects.get_for_model(Article)
                    try:
                        add_perm = Permission.objects.get(codename='add_article', content_type=content_type)
                        group.permissions.add(add_perm)
                    except Permission.DoesNotExist:
                        pass
                    user.groups.add(group)
                    
                elif role == 'reader':
                    group, _ = Group.objects.get_or_create(name='Readers')
                    article_ct = ContentType.objects.get_for_model(Article)
                    newsletter_ct = ContentType.objects.get_for_model(Newsletter)
                    
                    try:
                        view_art = Permission.objects.get(codename='view_article', content_type=article_ct)
                        group.permissions.add(view_art)
                        view_news = Permission.objects.get(codename='view_newsletter', content_type=newsletter_ct)
                        group.permissions.add(view_news)
                    except Permission.DoesNotExist:
                        pass
                    
                    user.groups.add(group)
            
            # Establish live system authentication loops smoothly
            login(request, user)
            return redirect('news_api:dashboard_redirect')
    else:
        form = CustomUserRegistrationForm()
        
    return render(request, 'news_api/register.html', {'form': form})


# ==========================================
# STAFF WORKSPACE CONTROL VIEWS
# ==========================================

@login_required
def assign_staff_view(request):
    """
    Manages workspace staff rosters for a logged-in Editor's Publisher organization.

    Processes incoming transactional instructions to add new personnel (Editors or Journalists) 
    to the publication network, offboard existing active staff entries smoothly, and extract 
    available unassigned pools.

    Args:
        request (HttpRequest): Core framework context capturing HTTP environment values, session 
            state lookups, and multi-attribute dictionary transaction properties.

    Returns:
        HttpResponse: A redirected loop instruction routing to the team status view pane, or 
            a rendered control screen summarizing active team rosters.
    """
    # Locate the target corporate organization profile where the active editor holds administrative status
    user_publisher = Publisher.objects.filter(editors=request.user).first()
    
    if not user_publisher:
        return render(request, 'news_api/error.html', {'message': "You are not assigned to a valid publisher workspace."})

    if request.method == 'POST':
        action_type = request.POST.get('action_type', 'assign')  # Values: 'assign' or 'remove'
        target_user_id = request.POST.get('user_id')
        
        try:
            staff_member = User.objects.get(id=target_user_id)
            
            # --- PROCESS STAFF ROLE WORKFORCE INGESTION ---
            if action_type == 'assign':
                action_role = request.POST.get('assign_as')  # Values: 'editor' or 'journalist'
                
                if action_role == 'editor':
                    staff_member.role = 'editor'
                    staff_member.save()
                    user_publisher.editors.add(staff_member)
                    
                elif action_role == 'journalist':
                    staff_member.role = 'journalist'
                    staff_member.save()
                    user_publisher.journalists.add(staff_member)
            
            # --- PROCESS STAFF REMOVAL / RETIREMENT LOOP ---
            elif action_type == 'remove':
                if user_publisher.editors.filter(id=staff_member.id).exists():
                    user_publisher.editors.remove(staff_member)
                if user_publisher.journalists.filter(id=staff_member.id).exists():
                    user_publisher.journalists.remove(staff_member)
                
                # Gracefully reset the unlinked staff asset back into a standard base reader layout
                staff_member.role = 'reader'
                staff_member.save()
                
            user_publisher.save()
            return redirect('news_api:manage_team')
            
        except User.DoesNotExist:
            pass

    # Extract clean profiles eligible to join a workspace, excluding active competitors or pre-assigned managers
    unassigned_users = User.objects.exclude(
        publisher_editors=user_publisher
    ).exclude(
        publisher_journalists=user_publisher
    ).exclude(
        role__iexact='editor'
    )
    
    context = {
        'publisher': user_publisher,
        'current_editors': user_publisher.editors.all(),
        'current_journalists': user_publisher.journalists.all(),
        'available_users': unassigned_users
    }
    return render(request, 'news_api/manage_team.html', context)

# news_api/views.py

# news_api/views.py

@login_required
def dashboard_redirect_view(request):
    """
    Evaluates an authenticated user profile's designation and routes them to their portal interface.

    CRITICAL FIX: Strips out hard-cached browser next redirects and forces 
    the active Publisher role completely away from the editor gate line.

    Args:
        request (HttpRequest): Session matrix transaction containing user profile details.

    Returns:
        HttpResponseRedirect: Dynamic path instruction mapping to an administrative, writer, or subscriber route.
    """
    # Force a fresh evaluation of the user role string values
    role = getattr(request.user, 'role', 'reader').lower().strip()
    
    if role == 'publisher':
        # Safely direct publishers straight to their own independent dash room panel view
        return redirect('news_api:publisher_dashboard')
    elif role == 'editor':
        return redirect('news_api:editorial_dashboard')
    elif role == 'journalist':
        return redirect('news_api:journalist_dashboard')
    else:
        return redirect('news_api:reader_dashboard')


    
def is_journalist_check(user):
    """
    Validates whether the incoming user context matches a valid active Journalist profile.

    Args:
        user (CustomUser): Target system identity profile object instance under assessment.

    Returns:
        bool: True evaluation verification flags if explicit journalist roles match.
    """
    return user.is_authenticated and getattr(user, 'role', 'reader').lower() == 'journalist'


def is_editor_check(user):
    """
    Validates whether the user is strictly an Editor.
    """
    return user.is_authenticated and getattr(user, 'role', 'reader').lower() == 'editor'


def is_publisher_check(user):
    """
    Validates whether the user is strictly a Publisher account role.
    """
    # 'publisher' role pass this check, clearing any security redirects.
    return user.is_authenticated and getattr(user, 'role', 'reader').lower() == 'publisher'


@login_required
@user_passes_test(is_publisher_check)
def publisher_dashboard_view(request):
    """
    Renders a premium administrative control console for the Publisher role.

    Tracks workforce statistics and content moderation metrics in a polished dashboard,
    ensuring a pure server-side implementation free of client-side script overhead.

    Args:
        request (HttpRequest): Session matrix tracking authenticated publisher context.

    Returns:
        HttpResponse: Clean HTML string payload containing the polished workspace console.
    """
    csrf_token = get_token(request)
    
    # Extract the publisher organization where this user account is a listed manager
    user_publisher = Publisher.objects.filter(editors=request.user).first()

    if user_publisher:
        editors_count = user_publisher.editors.count()
        journalists_count = user_publisher.journalists.count()
        
        # Calculate content metrics specific to this publisher's workspace
        pending_count = Article.objects.filter(publisher=user_publisher, approved=False).count()
        approved_count = Article.objects.filter(publisher=user_publisher, approved=True).count()
        
        # COMPREHENSIVE RESTORATION: Every multi-tenant panel operation card is fully mapped here
        publisher_html_content = f"""
        <div class="panel-header">
            
                <span class="brand-icon">🏢</span>
                <div>
                    <h3>{user_publisher.name}</h3>
                    <p>Master Workspace Agency Portal</p>
                </div>
            </div>
            <span class="badge badge-active">Active Operation</span>
        </div>
        
        <p class="panel-description">
            You are authenticated as the <strong>Master Managing Publisher</strong>. Use this secure control panel 
            to organize content moderation rules, analyze data streams, and onboard media staff.
        </p>
        
        <div class="grid-metrics">
            <div class="metric-card card-editors">
                <div class="metric-title">Linked Editors</div>
                <div class="metric-num">{editors_count}</div>
                <div class="metric-sub">Roster managers assigned</div>
            </div>
            <div class="metric-card card-journalists">
                <div class="metric-title">Staff Writers</div>
                <div class="metric-num">{journalists_count}</div>
                <div class="metric-sub">Active platform journalists</div>
            </div>
            <div class="metric-card card-pending">
                <div class="metric-title">Pending Moderation</div>
                <div class="metric-num">{pending_count}</div>
                <div class="metric-sub">Drafts awaiting approval</div>
            </div>
            <div class="metric-card card-approved">
                <div class="metric-title">Live Publications</div>
                <div class="metric-num">{approved_count}</div>
                <div class="metric-sub">Global broadcast feeds</div>
            </div>
        </div>
        
        <div class="action-footer">
            <a href="{django_reverse('news_api:manage_team')}" class="btn-primary">
                Configure Staff & Onboard Writers <span style="margin-left: 8px;">→</span>
            </a>
        </div>
        """
    else:
        # Fallback setup interface if an identity row doesn't match yet
        publisher_html_content = f"""
        <div class="panel-header">
            
                <span class="brand-icon" style="background: var(--warning-light); color: var(--warning);">⚠️</span>
                <div>
                    <h3>Organization Setup Required</h3>
                    <p>Tenant Configuration Pending</p>
                </div>
            </div>
        </div>
        <p class="panel-description" style="margin-bottom: 30px;">
            Your account role is fully authenticated as a Publisher, but you have not established your 
            corporate media network footprint yet. Initialize your standalone publisher row to activate your system features.
        </p>
        <div style="text-align: center;">
            <a href="{django_reverse('news_api:create_publisher_standalone')}" class="btn-primary" style="background: var(--warning); display: inline-block; width: auto; padding: 14px 35px;">
                Initialize Corporate Brand Workspace
            </a>
        </div>
        """
    # news_api/views.py (Inside your publisher_dashboard_view function string)
    
    # Generate the Premium Master Layout Screen String Injection
    html_layout = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Publisher Center - News Portal</title>
        <style>
            :root {{
                --bg-main: #f8fafc;
                --surface: #ffffff;
                --text-main: #1e293b;
                --text-muted: #64748b;
                --primary: #2563eb;
                --primary-hover: #1d4ed8;
                --success: #10b981;
                --success-light: #ecfdf5;
                --warning: #f59e0b;
                --warning-light: #fffbeb;
                --border-color: #e2e8f0;
                --danger: #ef4444;
            }}
            
            body {{
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                background-color: var(--bg-main);
                color: var(--text-main);
                margin: 0;
                padding: 0;
                min-height: 100vh;
            }}
            
            .navbar {{
                background-color: #0f172a;
                color: white;
                padding: 16px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            }}
            
            .navbar h1 {{
                margin: 0;
                font-size: 20px;
                font-weight: 700;
                letter-spacing: -0.5px;
            }}
            
            .navbar a {{
                color: #94a3b8;
                text-decoration: none;
                font-weight: 600;
                font-size: 14px;
                transition: color 0.2s;
            }}
            
            .navbar a:hover {{
                color: white;
            }}
            
            .container {{
                max-width: 1040px;
                margin: 40px auto;
                padding: 0 24px;
            }}
            
            .header-split {{
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                margin-bottom: 32px;
                gap: 20px;
            }}
            
            .hero-greeting {{
                margin: 0;
            }}
            
            .hero-greeting h2 {{
                margin: 0;
                font-size: 28px;
                font-weight: 800;
                letter-spacing: -0.75px;
                color: #0f172a;
            }}
            
            .hero-greeting p {{
                margin: 6px 0 0 0;
                color: var(--text-muted);
                font-size: 15px;
            }}
            
            .logout-panel {{
                text-align: right;
                flex-shrink: 0;
            }}
            
            .btn-logout-link {{
                background: none;
                border: 1px solid #cbd5e1;
                color: #475569;
                font-weight: 700;
                cursor: pointer;
                font-family: inherit;
                font-size: 13px;
                padding: 8px 16px;
                border-radius: 6px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                transition: all 0.2s;
            }}
            
            .btn-logout-link:hover {{
                background-color: #f1f5f9;
                color: var(--danger);
                border-color: #fca5a5;
            }}
            
            .main-panel {{
                background: var(--surface);
                border-radius: 12px;
                border: 1px solid var(--border-color);
                box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05);
                padding: 35px;
            }}
            
            .panel-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 24px;
                margin-bottom: 24px;
            }}
            
            .brand-identity {{
                display: flex;
                align-items: center;
                gap: 16px;
            }}
            
            .brand-icon {{
                font-size: 24px;
                background: #f1f5f9;
                padding: 12px;
                border-radius: 10px;
                display: inline-block;
            }}
            
            .brand-identity h3 {{
                margin: 0;
                font-size: 22px;
                font-weight: 700;
                color: #0f172a;
            }}
            
            .brand-identity p {{
                margin: 2px 0 0 0;
                font-size: 13px;
                color: var(--text-muted);
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            
            .badge {{
                padding: 6px 14px;
                border-radius: 9999px;
                font-size: 13px;
                font-weight: 700;
                text-transform: uppercase;
            }}
            
            .badge-active {{
                background-color: var(--success-light);
                color: var(--success);
                border: 1px solid #a7f3d0;
            }}
            
            .panel-description {{
                color: #475569;
                font-size: 15px;
                line-height: 1.6;
                margin: 0 0 32px 0;
            }}
            
            .grid-metrics {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 35px;
            }}

            /* --- RESTORED ACCENT AND CONTAINER CLASSES --- */
            .metric-card {{
                background: #f8fafc;
                border: 1px solid var(--border-color);
                border-radius: 10px;
                padding: 20px;
                text-align: left;
            }}
            
            .metric-title {{
                font-size: 13px;
                font-weight: 700;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .metric-num {{
                font-size: 32px;
                font-weight: 800;
                color: #0f172a;
                margin: 12px 0 6px 0;
                line-height: 1;
            }}
            
            .metric-sub {{
                font-size: 12px;
                color: var(--text-muted);
            }}
            
            .card-editors {{ border-left: 4px solid var(--primary); }}
            .card-journalists {{ border-left: 4px solid var(--success); }}
            .card-pending {{ border-left: 4px solid var(--warning); }}
            .card-approved {{ border-left: 4px solid #8b5cf6; }}
            
            .action-footer {{
                border-top: 1px solid var(--border-color);
                padding-top: 24px;
                display: flex;
                justify-content: flex-end;
            }}
            
            .btn-primary {{
                display: inline-flex;
                align-items: center;
                background-color: var(--primary);
                color: white;
                text-decoration: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 14px;
                text-transform: uppercase;
                border: none;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            
            .btn-primary:hover {{
                background-color: var(--primary-hover);
            }}
            
            @media (max-width: 900px) {{
                .grid-metrics {{ grid-template-columns: repeat(2, 1fr); }}
            }}
            @media (max-width: 650px) {{
                .header-split {{ flex-direction: column; align-items: flex-start; gap: 16px; }}
                .logout-panel {{ text-align: left; width: 100%; }}
                .btn-logout-link {{ width: 100%; text-align: center; }}
                .grid-metrics {{ grid-template-columns: 1fr; }}
            }}
        </style>
    </head>
    <body>
        <nav class="navbar">
            <h1>📰 Publisher Workspace Console</h1>
            <div>
                <a href="{django_reverse('news_api:system_landing_page')}">View Public Site</a>
            </div>
        </nav>
        
        <div class="container">
            <div class="header-split">
                <div class="hero-greeting">
                    <h2>Welcome Back, Operations Controller</h2>
                    <p>System Matrix Gateway Instance</p>
                </div>
                <div class="logout-panel">
                    <form action="{django_reverse('news_api:logout')}" method="POST" style="margin: 0;">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                        <button type="submit" class="btn-logout-link">
                            Sign Out Account
                        </button>
                    </form>   
                </div>
            </div>
            
            <!-- FIXED: Re-enclosed the panel block wrapper around your data fields -->
            <main class="main-panel">
                {publisher_html_content}
            </main>
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(html_layout)

    
@login_required
@user_passes_test(is_editor_check)
def portal_html_dashboard(request):
    """
    Renders an isolated, master Editorial Dashboard layout view strictly for Content Editors.

    Displays real-time system moderation parameters, tracking unapproved drafts 
    and live global publications completely separated from Publisher workspace controls.

    Args:
        request (HttpRequest): System context capturing active user credentials, 
            authentication tokens, and framework meta parameters.

    Returns:
        HttpResponse: Generated raw HTML string payload rendering the moderation console.
    """
    # 1. Fetch system-wide content moderation statistics parameters
    pending_count = Article.objects.filter(approved=False).count()
    approved_count = Article.objects.filter(approved=True).count()

    # 2. Extract standard request verification parameters
    csrf_token = get_token(request)

    # 3. Generate the absolute master administrative workspace layout payload
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
            .card {{ background: white; padding: 25px; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #2c3e50; box-sizing: border-box; }}
            .card.alert-card {{ border-top-color: #e74c3c; }}
            .stat-num {{ font-size: 36px; font-weight: bold; margin: 10px 0; color: #2c3e50; }}
            .card.alert-card .stat-num {{ color: #e74c3c; }}
            .btn-action {{ display: inline-block; margin-top: 15px; padding: 10px 20px; background-color: #2c3e50; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px; text-transform: uppercase; border: none; cursor: pointer; }}
            .btn-action:hover {{ opacity: 0.9; }}
            .btn-action.btn-danger {{ background-color: #e74c3c; }}
        </style>
    </head>
    <body>
        <nav class="navbar">
            <h1>📰 News Portal System</h1>
            <div>
                <a href="{django_reverse('news_api:system_landing_page')}">View Public Site</a>
                <form action="{django_reverse('news_api:logout')}" method="POST" style="display: inline; margin-left: 20px;">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                    <button type="submit" style="background: none; border: none; color: #ecf0f1; font-weight: bold; cursor: pointer; font-family: inherit; font-size: 16px; padding: 0;">
                        Sign Out ({request.user.username})
                    </button>
                </form>            
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
                    <a href="{django_reverse('news_api:review_list')}" class="btn-action btn-danger">Open Review Queue</a>
                </div>
                
                <div class="card">
                    <h3>Published Directory</h3>
                    <div class="stat-num">{approved_count}</div>
                    <p>Live entries currently broadcasted to readers and accessible through public API feeds.</p>
                    <a href="{django_reverse('news_api:system_landing_page')}" class="btn-action">View Live Feed</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content)

@login_required
@user_passes_test(is_editor_check)
@require_POST
def approve_article_action(request, article_id):
    """
    Flips validation flags for a draft article after verifying corporate workspace ownership.

    Args:
        request (HttpRequest): Active thread configuration request instance.
        article_id (int): Primary key row identifier targeting the article record.

    Returns:
        HttpResponseRedirect: Action complete re-route target back to the review queue index.
    """
    # Find the editor's active corporate workspace profile
    user_publisher = Publisher.objects.filter(editors=request.user).first()
    
    # Secure Lookup: Ensure the article exists AND belongs explicitly to the editor's workspace
    article = get_object_or_404(Article, id=article_id, publisher=user_publisher)
    
    # Flip the verification flags
    article.approved = True
    article.save()

    # --- PROCESS SUBSCRIBER NOTIFICATIONS LAYER ---
    recipient_emails = []
    if article.author_id:
        journalist_subs = article.author.journalist_subscribers.all()
        recipient_emails.extend([sub.email for sub in journalist_subs if sub.email])
    
    if article.publisher_id:
        pub_subs = article.publisher.reader_subscribers.all()
        recipient_emails.extend([sub.email for sub in pub_subs if sub.email])

    recipient_emails = list(set(recipient_emails))

    if recipient_emails:
        author_name = article.author.username if article.author_id else user_publisher.name
        send_mail(
            subject=f"New Article Released: {article.title}",
            message=f"Read our latest drop from {user_publisher.name} via {author_name}.",
            from_email="noreply@newsnetwork.local",
            recipient_list=recipient_emails,
            fail_silently=True
        )

    # Fire logging webhook dispatch hook
    domain = request.build_absolute_uri('/')[:-1]
    try:
        requests.post(f"{domain}/api/approved/", json={"article_id": article.id, "status": "APPROVED"}, timeout=5)
    except requests.exceptions.RequestException:
        pass 

    return redirect('news_api:review_list')

@login_required
@user_passes_test(is_editor_check)
def review_articles_list(request):
    """
    Renders the moderation queue table view filtered strictly by the Editor's Publisher workspace.

    Args:
        request (HttpRequest): Core incoming transactional payload request object.

    Returns:
        HttpResponse: A template layout rendering unapproved drafts belonging only 
            to the editor's corporate publication.
    """
    # Find the corporate organization workspace where this active editor belongs
    user_publisher = Publisher.objects.filter(editors=request.user).first()
    
    if not user_publisher:
        return render(request, 'news_api/error.html', {
            'message': "Access Denied: You must be linked to a Publisher organization to moderate articles."
        })

    # FIXED: Restrict the query pool to articles matching the editor's publisher ID
    unapproved_articles = Article.objects.filter(
        publisher=user_publisher,
        approved=False
    ).order_by('-created_at')
    
    return render(request, 'news_api/review_list.html', {'articles': unapproved_articles})

@login_required
def reader_dashboard(request):
    """
    Renders the custom profile landing control layout for standard readers.

    Args:
        request (HttpRequest): Session context capturing active user authentication profiles.

    Returns:
        HttpResponse: Rendered baseline reading summary interface template layout.
    """
    if getattr(request.user, 'role', 'reader').lower() != 'reader':
        return redirect('news_api:dashboard_redirect')
        
    return render(request, 'news_api/reader.html')


@login_required
def journalist_dashboard(request):  # Maintained exact typo signature from core source tree
    """
    Renders the landing console template dashboard workspace for Journalists.

    Args:
        request (HttpRequest): Session thread tracking authenticated writer context.

    Returns:
        HttpResponse: Rendered reporter writing operations station control layout.
    """
    return render(request, 'news_api/journalist.html')


@login_required
@user_passes_test(is_editor_check)
def editor_dashboard(request):
    """
    Renders the administrative moderation template feed view for corporate Editors.

    Args:
        request (HttpRequest): Core incoming dashboard validation transaction payload.

    Returns:
        HttpResponse: Rendered workspace review template mapping pending article counts.
    """
    pending_articles = Article.objects.filter(approved=False).order_by('-created_at')
    return render(request, 'news_api/editor.html', {'articles': pending_articles})


# ==========================================
# CLASS-BASED CREATION & DELETION VIEWS
# ==========================================

# news_api/views.py

class ArticleCreateView(PermissionRequiredMixin, CreateView):
    """
    Handles graphic form submissions creating new isolated Article entries.
    """
    model = Article
    form_class = ArticleModelForm
    template_name = 'news_api/article_form.html'
    permission_required = 'news_api.add_article'

    def get_form_kwargs(self):
        """
        Injects the active authenticated user into form validation loops.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        Evaluates form fields to preserve strict data single-source mutual exclusivity.
        """
        # 1. Build the model instance in memory without saving to disk yet
        self.object = form.save(commit=False)
        
        # 2. Enforce the tenant separation criteria checks
        if form.cleaned_data.get('publisher'):
            # It's an authorized publisher content stream item -> Clear author reference field
            self.object.author = None
        else:
            # Dropdown choice is empty -> It's a clean independent article post by the active writer
            self.object.author = self.request.user

        # 3. Force the new draft directly to an unapproved state for editorial review
        self.object.approved = False 
        
        # 4. Save the object instance down to disk storage rows
        self.object.save()
        
        # naturally execute your get_success_url() method mapping!
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirect target back to the journalist console dashboard room workspace.
        """
        return django_reverse('news_api:journalist_dashboard')



class ArticleUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Manages interactive content modifications across existing article entries.
    """
    model = Article
    fields = ['title', 'content', 'publisher']
    template_name = 'news_api/article_form.html'
    permission_required = 'news_api.change_article'
    
    def get_success_url(self):
        """
        Calculates path loops to route back to detail displays upon saving modifications.
        """
        return django_reverse('news_api:article_detail', kwargs={'pk': self.object.pk})


class ArticleDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Handles absolute content block removal and database entry row destruction actions.
    """
    model = Article
    template_name = 'news_api/article_confirm_delete.html'
    permission_required = 'news_api.delete_article'
    success_url = reverse_lazy('news_api:system_landing_page')


# ==========================================
# DJANGO REST FRAMEWORK CONTROLLERS (APIs)
# ==========================================

class ArticleListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint tracking approved listing payloads and accepting fresh content drafts.
    """
    queryset = Article.objects.filter(approved=True)
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsEditorOrJournalistUser]
    
    def perform_create(self, serializer):
        """
        Intercepts serialization pipelines to block rogue multi-tenant publisher assignments.
        """
        user = self.request.user
        chosen_publisher = serializer.validated_data.get('publisher')

        if chosen_publisher:
            # FIXED: Verify the journalist belongs to the publisher passed in the JSON payload
            is_authorized = chosen_publisher.journalists.filter(id=user.id).exists()
            if not is_authorized:
                from rest_framework.exceptions import ValidationError as APIValidationError
                raise APIValidationError(
                    {"publisher": f"Security Exception: You do not hold writing permissions for '{chosen_publisher.name}'."}
                )
            
            # Safe: Strip author link out since it belongs to a verified publisher stream layout
            serializer.save(publisher=chosen_publisher, author=None, approved=False)
        else:
            # Safe: No publisher provided -> Process cleanly as an independent post
            serializer.save(author=user, publisher=None, approved=False)


@method_decorator(csrf_exempt, name='dispatch') 
class LegacyLogoutView(auth_views.LogoutView):
    """
    Safely permits legacy GET request methods and handles CSRF-free logout loops.
    """
    def get(self, request, *args, **kwargs):
        """
        Maps fallthrough GET instructions cleanly into the standard POST handler block.
        """
        return self.post(request, *args, **kwargs)


class ArticleSubscribedListAPIView(generics.ListAPIView):
    """
    Extracts custom text timeline feeds containing records from subscribed sources.

    Queries the authenticated user's profile configuration settings to extract 
    lists of followed independent journalists and corporate publishers, returning 
    a distinct pool of approved articles.
    """
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filters the general content repository matrix based on a user's subscription profile.

        Evaluates many-to-many relationship tracking matrices utilizing complex OR 
        statements via models.Q before purging duplicates and ordering by timestamp metrics.

        Returns:
            QuerySet: An evaluated, distinct dataset pool containing approved articles matching 
                the user's subscription tracking profiles.
        """
        user = self.request.user
        
        # Extract individual tracking lists from the authenticated session user
        subscribed_journalists = user.subscribed_journalists.all()
        subscribed_publishers = user.subscribed_publishers.all()
        
        # Construct and return the evaluated relational query stream
        return Article.objects.filter(
            models.Q(author__in=subscribed_journalists) | models.Q(publisher__in=subscribed_publishers),
            approved=True
        ).distinct().order_by('-created_at')

                                      
class ArticleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Processes single entry mutations, read lookups, or entry destruction cycles via API paths.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsEditorOrJournalistUser]


class NewsletterListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint managing index collection readings or generating new periodic digest newsletters.
    """
    queryset = Newsletter.objects.all().order_by('-created_at')
    serializer_class = NewsletterSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsJournalistUser]

    def perform_create(self, serializer):
        """
        Automatically sets the currently authenticated writer as the author during creation.
        """
        serializer.save(author=self.request.user)


class APIApprovedLogEndpoint(APIView):
    """
    Exposes a webhook validation endpoint logging article status changes.
    """
    permission_classes = [permissions.AllowAny] 

    def post(self, request, *args, **kwargs):
        """
        Captures structural JSON payload updates from dispatch workers.
        """
        article_id = request.data.get("article_id")
        status_text = request.data.get("status")
        
        # Log payload data details to system output for tracking and telemetry analysis
        print(f"[WEBHOOK RECEIVED] Article {article_id} status updated to: {status_text}")
        
        return Response(
            {
                "success": True, 
                "message": f"Article {article_id} verification processed successfully."
            }, 
            status=status.HTTP_201_CREATED
        )

    def get(self, request, *args, **kwargs):
        """
        Provides online confirmation monitoring checks for diagnostic verification tools.
        """
        return Response(
            {"status": "Logging endpoint online. Send a POST webhook payload to track data."},
            status=status.HTTP_200_OK
        )


# ==========================================
# CLASS-BASED TEMPLATE VIEWS (GUI)
# ==========================================

class NewsletterCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Handles template-based workspace form submissions to compile and draft Newsletters.
    """
    model = Newsletter
    fields = ['title', 'description', 'articles']
    template_name = 'news_api/newsletter_form.html'

    def test_func(self):
        """
        Enforces access security parameters to isolate input screens from standard Readers.

        Returns:
            bool: True validation confirmation if the profile holds Journalist or Editor privileges.
        """
        role = getattr(self.request.user, 'role', 'reader').lower()
        return role in ['journalist', 'editor']

    def form_valid(self, form):
        """
        Automatically captures the active authenticated user to bind them as content Author.

        Args:
            form (ModelForm): Generated visual interface input validation map.

        Returns:
            HttpResponseRedirect: Redirection processing block targeting the system list view page.
        """
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """
        Calculates redirect route targets back to the index library view upon successful saves.
        """
        return django_reverse('news_api:newsletter_list')

@login_required
def create_publisher_standalone_view(request):
    """
    Handles separate registration of a Publisher profile independent of user signup.
    """
    existing_publisher = Publisher.objects.filter(editors=request.user).first()
    if existing_publisher:
        return redirect('news_api:editorial_dashboard')

    if request.method == 'POST':
        form = PublisherCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                publisher = form.save()
                
                # Link the creating user as an Editor role profile
                request.user.role = 'editor'
                request.user.save()
                publisher.editors.add(request.user)
                
                # Unpack selected multi-choice variables out of form parameters
                selected_editors = form.cleaned_data.get('editors')
                if selected_editors:
                    publisher.editors.add(*selected_editors)
                    
                selected_journalists = form.cleaned_data.get('journalists')
                if selected_journalists:
                    publisher.journalists.add(*selected_journalists)
                
                publisher.save()
            return redirect('news_api:editorial_dashboard')
    else:
        form = PublisherCreationForm()
        
    return render(request, 'news_api/create_publisher.html', {'form': form})
