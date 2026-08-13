# news_api/serializers.py
"""
Data serialization layer for the news ecosystem application.

Transforms Django database model instances into portable JSON payloads 
and handles incoming validation schemas for REST API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Publisher, Article, Newsletter

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Transforms custom user account profiles into secure external JSON structures.

    Exposes base identity properties, designated system routing roles, and 
    associated follow/subscription matrices for client profiles.
    """
    class Meta:
        """
        Maps user profile serialization options directly onto the system's active User model.
        """
        model = User
        fields = ['id', 'username', 'email', 'role', 'subscribed_publishers', 'subscribed_journalists']


class PublisherSerializer(serializers.ModelSerializer):
    """
    Handles serialization and validation configurations for corporate Publisher entities.

    Transforms tenant agency fields including administrative collections like associated 
    editors and journalists into readable arrays.
    """
    class Meta:
        """
        Binds all database columns on the Publisher model to public API channels.
        """
        model = Publisher
        fields = '__all__'


class ArticleSerializer(serializers.ModelSerializer):
    """
    Manages structural data transformations and write restrictions for Article entries.

    Provides readable author and publisher metadata using source lookups 
    while preserving strict access boundaries over administrative fields.

    Attributes:
        author_username (ReadOnlyField): Extracts and prints the author's display name string.
        publisher_name (ReadOnlyField): Extracts and prints the parent organization's corporate title.
    """
    author_username = serializers.ReadOnlyField(source='author.username')
    publisher_name = serializers.ReadOnlyField(source='publisher.name')

    class Meta:
        """
        Defines fields, relationships, and unalterable administrative boundaries for article payloads.
        """
        model = Article
        fields = ['id', 'title', 'body', 'is_approved', 'created_at', 'author', 'author_username', 'publisher', 'publisher_name']
        read_only_fields = ['is_approved', 'author']


class NewsletterSerializer(serializers.ModelSerializer):
    """
    Handles payload nesting and structure definitions for curated Newsletter digests.

    Flattens related primary keys into explicit sub-objects to let client interfaces 
    render nested article text streams effortlessly.

    Attributes:
        articles_details (ArticleSerializer): Recursively loops and reads details for linked article rows.
    """
    articles_details = ArticleSerializer(source='articles', many=True, read_only=True)

    class Meta:
        """
        Configures data serialization pipelines across periodic publication items.
        """
        model = Newsletter
        fields = ['id', 'title', 'description', 'created_at', 'author', 'articles', 'articles_details']
