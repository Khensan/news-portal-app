# news_api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model  # Fixed: Import dynamic user engine
from .models import Publisher, Article, Newsletter

# Fixed: Resolve reference mappings dynamically
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # Fixed: Target the dynamic user class
        fields = ['id', 'username', 'email', 'role', 'subscribed_publishers', 'subscribed_journalists']

class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = '__all__'

# Fixed: Merged duplicate declarations into a single, comprehensive configuration
class ArticleSerializer(serializers.ModelSerializer):
    author_details = UserSerializer(source='author', read_only=True)
    publisher_details = PublisherSerializer(source='publisher', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'author', 'author_details', 
            'publisher', 'publisher_details', 'created_at', 'approved'
        ]
        read_only_fields = ['approved', 'created_at']

# Fixed: Merged duplicate declarations into a single configuration
class NewsletterSerializer(serializers.ModelSerializer):
    articles_details = ArticleSerializer(source='articles', many=True, read_only=True)

    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'description', 'created_at', 'author', 'articles', 'articles_details']
