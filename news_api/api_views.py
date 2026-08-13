"""
REST API resource views for the news ecosystem application layer.

Provides optimized query evaluation structures, nested subscription timelines, 
and field security overrides for individual articles.
"""

from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Article
from .serializers import ArticleSerializer
from .permissions import IsJournalistUser, IsEditorOrJournalistUser


class ArticleListCreateAPIView(generics.ListCreateAPIView):
    """
    API resource view managing public content feeds and new text entries.

    Exposes a public listing stream of verified news reports to all authenticated 
    users while restricting draft generation capabilities to validated Journalists.
    """
    serializer_class = ArticleSerializer

    def get_permissions(self):
        """
        Overrides permissions dynamically based on the incoming request method type.

        Returns:
            list: Instantiated permission objects enforcing endpoint access limits.
        """
        if self.request.method == 'POST':
            return [IsJournalistUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Extracts all live, approved news entries sorted by reverse chronological order.

        Returns:
            QuerySet: Filtered article database records ready for delivery.
        """
        return Article.objects.filter(approved=True).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Intercepts serialization pipeline writes to inject systemic context values.

        Binds the incoming user session profile as the primary author field 
        and routes the new draft directly to an unapproved state for moderation review.

        Args:
            serializer (ModelSerializer): Activated REST configuration validation matrix.
        """
        serializer.save(author=self.request.user, approved=False)


class SubscribedArticlesAPIView(generics.ListAPIView):
    """
    API resource view returning personalized subscription timelines.

    Extracts customized updates from followed news agencies or distinct staff writers, 
    ensuring readers only receive matching news entries.
    """
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Compiles customized feed streams based on user tracking configurations.

        Extracts multi-tenant ID groupings straight from CustomUser tables before 
        running a distinct OR sweep to eliminate layout rendering duplicates.

        Returns:
            QuerySet: Distinct approved database records matching tracked identities.
        """
        user = self.request.user
        
        # Pull tracking relationships straight out of your CustomUser model fields
        subscribed_p_ids = user.subscribed_publishers.values_list('id', flat=True)
        subscribed_j_ids = user.subscribed_journalists.values_list('id', flat=True)
        
        # Evaluates clean OR conditions using the models.Q library matching core columns
        return Article.objects.filter(
            approved=True
        ).filter(
            models.Q(publisher_id__in=subscribed_p_ids) | models.Q(author_id__in=subscribed_j_ids)
        ).distinct().order_by('-created_at')


class ArticleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API resource view managing standalone content blocks.

    Provides granular endpoints to retrieve, update, or completely delete 
    individual article rows while preserving ownership boundaries.
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_permissions(self):
        """
        Protects destructive write actions by overriding permission classes.

        Ensures that while any reader can read details, only managing editors 
        or the authoring writer can run update or deletion routines.

        Returns:
            list: Instantiated permission objects enforcing block security bounds.
        """
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsEditorOrJournalistUser()]
        return [permissions.IsAuthenticated()]
