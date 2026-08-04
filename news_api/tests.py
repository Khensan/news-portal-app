from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from django.core import mail
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch

from .models import CustomUser, Publisher, Article, Newsletter

class NewsPlatformAPITests(APITestCase):

    def setUp(self):
        # Create core application RBAC Group architectures
        Group.objects.get_or_create(name='Reader')
        Group.objects.get_or_create(name='Editor')
        Group.objects.get_or_create(name='Journalist')

        # 1. Instantiate Users across separate permission paths
        self.reader = CustomUser.objects.create_user(username='reader_user', password='password123', email='reader@news.local', role='READER')
        self.journalist = CustomUser.objects.create_user(username='writer_user', password='password123', email='journalist@news.local', role='JOURNALIST')
        self.editor = CustomUser.objects.create_user(username='editor_user', password='password123', email='editor@news.local', role='EDITOR')

        # Generate standard access authorization tokens
        self.reader_token = Token.objects.create(user=self.reader)
        self.journalist_token = Token.objects.create(user=self.journalist)
        self.editor_token = Token.objects.create(user=self.editor)

        # 2. Instantiate Base structures
        self.publisher = Publisher.objects.create(name='Global News Corp')
        self.publisher.journalists.add(self.journalist)

        # Connect the Reader to this specific publisher stream
        self.reader.subscribed_publishers.add(self.publisher)

        # 3. Instantiate base asset entities
        self.approved_article = Article.objects.create(
            title='Global Market Trends', content='Market expansion...', author=self.journalist, publisher=self.publisher, approved=True
        )
        self.unapproved_article = Article.objects.create(
            title='Draft Breaking Leak', content='Unverified rumors...', author=self.journalist, publisher=self.publisher, approved=False
        )

        self.newsletter = Newsletter.objects.create(title='Weekly Digest', description='Curated reads', author=self.journalist)
        self.newsletter.articles.add(self.approved_article)

    # =========================================================================
    # ROLE AUTHENTICATION & ACCESS PROTECTION TESTS
    # =========================================================================

    def test_unauthenticated_requests_are_denied(self):
        """Verify that basic unauthenticated calls face hard rejections."""
        response = self.client.get(reverse('article_list_create'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_journalist_can_create_article_successfully(self):
        """Ensure authenticated creators can post raw drafts into the workflow queue."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.journalist_token.key)
        payload = {'title': 'New Breakthrough', 'content': 'Labs find cures', 'author': self.journalist.id}
        response = self.client.post(reverse('article_list_create'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['approved']) # New articles must default to unapproved

    def test_reader_cannot_create_article(self):
        """Prevent readers from generating content entries."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.reader_token.key)
        payload = {'title': 'Illegal Post', 'content': 'Spam content', 'author': self.journalist.id}
        response = self.client.post(reverse('article_list_create'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # RESOURCE EXTRACTION & FILTERS TESTS
    # =========================================================================

    def test_get_articles_returns_approved_content_only(self):
        """Verify standard public channel routes filter away unvetted records."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.reader_token.key)
        response = self.client.get(reverse('article_list_create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.approved_article.id)

    def test_reader_subscribed_filter_logic(self):
        """Ensure personalized feeds return content matching user subscriptions."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.reader_token.key)
        response = self.client.get(reverse('article_subscribed'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Break subscription relation to simulate subscription change
        self.reader.subscribed_publishers.clear()
        response = self.client.get(reverse('article_subscribed'))
        self.assertEqual(len(response.data), 0)

    # =========================================================================
    # STRUCTURAL INTEGRITY & REST DATA MUTATION TESTS
    # =========================================================================

    def test_editor_or_journalist_can_modify_resource(self):
        """Verify modification access rules for writers and desk leads."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.journalist_token.key)
        payload = {'title': 'Updated Title', 'content': 'New text contents', 'author': self.journalist.id}
        url = reverse('article_detail', kwargs={'pk': self.approved_article.id})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reader_cannot_delete_resource(self):
        """Ensure standard audience vectors cannot drop global records."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.reader_token.key)
        url = reverse('article_detail', kwargs={'pk': self.approved_article.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TemplateViewApprovalAndOption2Tests(TestCase):

    def setUp(self):
        Group.objects.get_or_create(name='Editor')
        self.editor = CustomUser.objects.create_user(username='lead_editor', password='securepass123', role='EDITOR')
        self.reader = CustomUser.objects.create_user(username='sub_reader', password='securepass123', email='sub@target.local', role='READER')
        self.journalist = CustomUser.objects.create_user(username='beat_writer', password='securepass123', role='JOURNALIST')
        
        self.publisher = Publisher.objects.create(name='Tech Daily')
        self.reader.subscribed_publishers.add(self.publisher)

        self.article = Article.objects.create(
            title='AI Era', content='Machines think fast', author=self.journalist, publisher=self.publisher, approved=False
        )

    # =========================================================================
    # ACCESS CONTROL & VIEW BUSINESS LOGIC VERIFICATION (OPTION 2)
    # =========================================================================

    def test_anonymous_redirected_from_review_desk(self):
        """Verify unauthenticated traffic is blocked from template routes."""
        client = Client()
        response = client.get(reverse('review_list'))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    @patch('requests.post')
    def test_editor_approval_triggers_webhook_and_emails_correctly(self, mock_post):
        """Simulate an approval step to verify email routing and API loops."""
        mock_post.return_value.status_code = 200
        
        client = Client()
        client.login(username='lead_editor', password='securepass123')
        
        url = reverse('approve_action', kwargs={'article_id': self.article.id})
        response = client.post(url)
        
        # Check database update
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # 1. Verify Option 2 Mail System Integration
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New Article Released", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to[0], 'sub@target.local')

        # 2. Verify Option 2 Internal Webhook loop API simulation
        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        self.assertIn('/api/approved/', called_url)
