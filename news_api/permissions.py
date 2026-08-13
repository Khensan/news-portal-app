# news_api/permissions.py
from rest_framework import permissions

class IsJournalistUser(permissions.BasePermission):
    """Allows write-access strictly to users with Journalist permissions."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm('news_api.add_article')

class IsEditorOrJournalistUser(permissions.BasePermission):
    """Allows updates and deletions strictly to Editors or the specific Journalist who authored the piece."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.has_perm('news_api.change_article') or 
            request.user.has_perm('news_api.add_article')
        )

    def has_object_permission(self, request, view, obj):
        # Editors can touch any record; Journalists can only update their independent creations
        if request.user.has_perm('news_api.change_article') and not request.user.has_perm('news_api.add_article'):
            return True
        return obj.author == request.user
