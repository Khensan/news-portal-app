# news_api/models.py
"""
Data models for the news ecosystem application layer.

Handles entity definitions, role-based mutual exclusivity validations, 
and automatic permission group synchronization through database lifecycle signals.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Publisher(models.Model):
    """
    Represents a tenant news publication house entity.

    Manages centralized editorial content streams and distinct staff association groupings 
    for Editors and Journalists.

    Attributes:
        name (CharField): Unique identifier name of the publishing company.
        editors (ManyToManyField): Affiliated user accounts holding administrative editor rights.
        journalists (ManyToManyField): Affiliated staff writers registered under this agency.
    """
    name = models.CharField(max_length=255)
    editors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='publisher_editors', blank=True)
    journalists = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='publisher_journalists', blank=True)

    def __str__(self):
        """
        Returns a readable string representation matching the publisher's commercial designation.
        """
        return self.name


class CustomUser(AbstractUser):
    """
    Custom user identity model defining specific operational system profiles.

    Controls platform navigation routing limits and access scopes using role assignments. 
    Maintains reader subscriber maps and content creation ownership trees.

    Attributes:
        ROLE_CHOICES (tuple): Constant tracking hardcoded authorization tiers.
        role (CharField): Tracked string dictating application portal routing limits.
        subscribed_publishers (ManyToManyField): Publishers followed by this user.
        subscribed_journalists (ManyToManyField): Self-referential map of followed journalists.
    """
    ROLE_CHOICES = (
        ('reader', 'Reader'),
        ('editor', 'Editor'),
        ('journalist', 'Journalist'),
        ('publisher', 'Publisher'),  
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='reader')
    subscribed_publishers = models.ManyToManyField('Publisher', blank=True, related_name="reader_subscribers")
    subscribed_journalists = models.ManyToManyField('self', blank=True, symmetrical=False, related_name="journalist_subscribers")

    def clean(self):
        """
        Performs structural pre-save validation testing over custom profile properties.
        """
        super().clean()
        pass

    def save(self, *args, **kwargs):
        """
        Commits profile properties while enforcing data isolation constraints between roles.

        Clears reader-specific tracking vectors if the profile becomes a journalist, 
        and disconnects active author relationships if the user transitions to a reader.

        Args:
            *args: Variable length argument list forwarded to the parent model class.
            **kwargs: Arbitrary keyword arguments forwarded to the parent model class.
        """
        # 1. Capture primary key registration status state beforehand
        is_new = self.pk is None
        
        # 2. Commit main database row parameters first
        super().save(*args, **kwargs)
        
        # 3. Assign mutual exclusivity rules safely AFTER the record possesses a row ID
        if not is_new:
            current_role = self.role.lower()
            if current_role == 'journalist':
                # If a user has a Journalist role, clear reader fields (simulates a 'None' assignment layout)
                self.subscribed_publishers.clear()
                self.subscribed_journalists.clear()
            elif current_role == 'reader':
                # If a user has a Reader role, clear out any historical independent content creation ties
                if hasattr(self, 'authored_articles'):
                    self.authored_articles.all().update(author=None)
                if hasattr(self, 'authored_newsletters'):
                    self.authored_newsletters.all().update(author=None)

    def __str__(self):
        """
        Provides a formatted descriptive label identifying the user and account authorization tier.
        """
        return f"{self.username} - {self.role}"


class Article(models.Model):
    """
    Represents an individual text news report created by assigned writers.

    Articles operate under a strictly enforced exclusive single-ownership pattern. 
    They must originate from either an independent journalist or a corporate publisher, 
    but cannot belong to both sources simultaneously.

    Attributes:
        title (CharField): The editorial headline text of the news post.
        content (TextField): The primary body copy text of the coverage item.
        author (ForeignKey): Relationship link pointing to the writing journalist.
        publisher (ForeignKey): Corporate owner tenancy connection linking this post to an agency.
        created_at (DateTimeField): Non-editable registration timestamp marking draft generation.
        approved (BooleanField): Editorial flag tracking publication eligibility status.
    """
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'journalist'}, 
        related_name='authored_articles'
    )
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='published_articles')
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def clean(self):
        """
        Enforces tenant isolation and single-ownership structural layout design rules.
        """
        super().clean()
        
        # 1. Enforce Mutual Exclusivity
        if self.pk and not self.author_id and not self.publisher_id:
            raise ValidationError("An article must be associated either with a journalist (independent) or a publisher.")
        
        if self.author_id and self.publisher_id:
            raise ValidationError("An article cannot belong to both an independent journalist and a publisher simultaneously.")

        # 2. FIXED: Cross-verify that the writing journalist actually belongs to the chosen publisher
        if self.author_id and self.publisher_id:
            # Check if the author is listed under the target publisher's journalists ManyToMany relationship
            is_staff = self.publisher.journalists.filter(id=self.author_id).exists()
            if not is_staff:
                raise ValidationError(
                    f"Access Denied: You are not authorized to publish under '{self.publisher.name}'. "
                    "You can only select your assigned publisher or submit independently."
                )


    def __str__(self):
        """
        Returns a raw headline title identifying the article instance.
        """
        return self.title


class Newsletter(models.Model):
    """
    Represents a periodic digest newsletter compilation.

    Assembled and distributed by independent journalists, grouping multiple articles together.

    Attributes:
        title (CharField): The naming designation for the current subscription newsletter edition.
        description (TextField): Structural introductory summaries detailing publication themes.
        created_at (DateTimeField): Automated stamp logging tracking dispatch sequence timings.
        author (ForeignKey): Linked database identity pointing to the managing writer.
        articles (ManyToManyField): Relational group linking articles enclosed inside the letter.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'journalist'},
        related_name='authored_newsletters'
    )
    articles = models.ManyToManyField(Article, related_name='newsletters')

    def __str__(self):
        """
        Exposes the clear identification text title defining the individual newsletter issue.
        """
        return self.title


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sync_user_permission_groups(sender, instance, created, **kwargs):
    """
    Automates profile role syncing across Django Authorization Groups upon user profile saves.

    Args:
        sender (Model): The model class invoking the signal interface (CustomUser).
        instance (CustomUser): The explicit model instance record being written to disk.
        created (bool): Boolean flag highlighting fresh database row additions.
        **kwargs: Flexible metadata parameters captured during the post_save stack invocation.
    """
    group_name = instance.role.capitalize()
    group, _ = Group.objects.get_or_create(name=group_name)
    
    if not instance.groups.filter(id=group.id).exists():
        instance.groups.clear()
        instance.groups.add(group)
