# news_api/permissions.py
from rest_framework import permissions

class IsJournalist(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'JOURNALIST'

class IsEditor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'EDITOR'

class IsEditorOrJournalist(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['EDITOR', 'JOURNALIST']
