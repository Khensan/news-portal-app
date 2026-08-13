from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
# Adjust 'news' to match your actual App name where models live
from news_api.models import Article, Newsletter 

def create_role_groups():
    """
    Initializes and provisions Django Authorization Groups matching user system roles.

    Fetches model-level permissions from the content type registry and explicitly 
    assigns them to Reader, Editor, and Journalist structural groups to enforce 
    access boundaries.

    Raises:
        Permission.DoesNotExist: If the default Django permissions have not been 
            generated or populated inside the database migrations history table.
    """
    # 1. Fetch content type references for target models
    article_ct = ContentType.objects.get_for_model(Article)
    newsletter_ct = ContentType.objects.get_for_model(Newsletter)

    # 2. Extract specific model authorization permissions from the registry
    view_art = Permission.objects.get(codename='view_article', content_type=article_ct)
    view_news = Permission.objects.get(codename='view_newsletter', content_type=newsletter_ct)
    
    add_art = Permission.objects.get(codename='add_article', content_type=article_ct)
    add_news = Permission.objects.get(codename='add_newsletter', content_type=newsletter_ct)
    
    change_art = Permission.objects.get(codename='change_article', content_type=article_ct)
    change_news = Permission.objects.get(codename='change_newsletter', content_type=newsletter_ct)
    
    delete_art = Permission.objects.get(codename='delete_article', content_type=article_ct)
    delete_news = Permission.objects.get(codename='delete_newsletter', content_type=newsletter_ct)

    # 3. Initialize and provision structural Group instances
    # ■ Reader Group Setup
    reader_group, _ = Group.objects.get_or_create(name='Reader')
    reader_group.permissions.set([view_art, view_news])

    # ■ Editor Group Setup
    editor_group, _ = Group.objects.get_or_create(name='Editor')
    editor_group.permissions.set([view_art, view_news, change_art, change_news, delete_art, delete_news])

    # ■ Journalist Group Setup
    journalist_group, _ = Group.objects.get_or_create(name='Journalist')
    journalist_group.permissions.set([view_art, view_news, add_art, add_news, change_art, change_news, delete_art, delete_news])
