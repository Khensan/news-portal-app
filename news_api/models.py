from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.conf import settings  # Fixed: Imported settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Publisher(models.Model):
    name = models.CharField(max_length=255)
    # Fixed: Swapped 'CustomUser' for settings.AUTH_USER_MODEL
    editors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='publisher_editors', blank=True)
    journalists = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='publisher_journalists', blank=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('READER', 'Reader'),
        ('EDITOR', 'Editor'),
        ('JOURNALIST', 'Journalist'),
    ]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='READER')
    
    # Reader-specific fields
    subscribed_publishers = models.ManyToManyField(Publisher, related_name='reader_subscribers', blank=True)
    subscribed_journalists = models.ManyToManyField('self', symmetrical=False, related_name='journalist_subscribers', blank=True)

    def clean(self):
        super().clean()
        # Validation checks only run if instance exists in the database
        if self.role != 'READER' and self.pk:
            if self.subscribed_publishers.exists() or self.subscribed_journalists.exists():
                raise ValidationError("Non-readers cannot have active subscriptions.")

    def save(self, *args, **kwargs):
        if self.pk:
            self.full_clean()
        super().save(*args, **kwargs)

class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    # Fixed: Swapped CustomUser for settings.AUTH_USER_MODEL
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'JOURNALIST'}, related_name='authored_articles')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='published_articles')
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.author and self.publisher and self.pk:
            if not self.publisher.journalists.filter(id=self.author.id).exists():
                raise ValidationError("This article must be mapped directly to an independent journalist or their registered publisher.")

    def save(self, *args, **kwargs):
        if self.pk:
            self.full_clean()
        super().save(*args, **kwargs)

class Newsletter(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Fixed: Swapped CustomUser for settings.AUTH_USER_MODEL
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'JOURNALIST'})
    articles = models.ManyToManyField(Article, related_name='newsletters')


# Fixed: Decoupled Group sync logic using a post_save receiver hook
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sync_user_permission_groups(sender, instance, created, **kwargs):
    group_name = instance.role.capitalize()
    group, _ = Group.objects.get_or_create(name=group_name)
    
    if not instance.groups.filter(id=group.id).exists():
        instance.groups.clear()
        instance.groups.add(group)
