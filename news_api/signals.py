"""
Signal receivers for the news ecosystem application layer.

Handles lifecycle events for user profiles, ensuring that authorization 
groups stay synchronized with structural user roles whenever profiles are 
created or modified.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def assign_user_to_permission_group(sender, instance, created, **kwargs):
    """
    Synchronizes Django permission groups based on the user's profile role.

    Triggers upon user creation or when a role configuration changes. It clears 
    stale role-group assignments and re-assigns the user to the matching structural 
    group without disrupting publisher-staff associations.

    Args:
        sender (Model): The model class invoking the signal interface (CustomUser).
        instance (CustomUser): The explicit user profile instance record being written.
        created (bool): Flag indicating if this is a fresh database row addition.
        **kwargs: Flexible metadata parameters captured during the post_save stack execution.
    """
    # Check if this is a new user or if the role field has explicitly changed
    has_role_changed = False
    if hasattr(instance, 'tracker'):
        has_role_changed = instance.tracker.has_changed('role')
    else:
        # Fallback safeguard if the tracking helper is absent during evaluation steps
        has_role_changed = True

    if created or has_role_changed:
        # Clear out historical authorization groups smoothly to prevent overlapping roles
        instance.groups.clear()
        
        # Dynamically map the chosen profile configuration to a database Group name
        # Example: 'editor' turns into 'Editor', 'journalist' turns into 'Journalist'
        group_name = instance.role.capitalize()
        group, _ = Group.objects.get_or_create(name=group_name)
        
        # Bind the user to the structural authorization group
        instance.groups.add(group)