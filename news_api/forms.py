"""
Form definitions for account ingestion pipelines and decentralized publisher configuration management.

Provides data capture structures for multi-tenant staff rosters, blended role onboarding setups,
and administrative standalone workspace provisioning workflows.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Publisher, Article


User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    Extends standard Django user creation forms to surface role selections.
    """
    class Meta(UserCreationForm.Meta):
        """
        Maps metadata settings directly onto the custom User model fields.
        """
        model = User
        fields = UserCreationForm.Meta.fields + ('role',)

class CustomUserRegistrationForm(UserCreationForm):
    """
    Extends standard creation flows to handle flexible user tier onboarding.
    """
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True, help_text="Select your platform access tier.")
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'role')

class PublisherCreationForm(forms.ModelForm):
    """
    Form to create a Publisher completely on its own.
    
    Provides multi-selection checklist parameters to assign existing unassigned 
    Editors and staff Journalists to the brand-new organization footprint.
    """
    
    # 1. Multi-selection checklist to assign unassigned Editors
    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(
            role__iexact='editor',
            publisher_editors__isnull=True
        ),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Assign Workspace Managers (Editors)",
        help_text="Select one or more existing unassigned Editors to manage this Publisher."
    )

    # 2. Multi-selection checklist to assign unassigned Journalists
    journalists = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(
            role__iexact='journalist', 
            publisher_journalists__isnull=True
        ),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Assign Staff Writers (Journalists)",
        help_text="Select independent unassigned journalists to bind into this workspace ecosystem."
    )

    class Meta:
        """
        Binds form properties directly onto target operational schema columns.
        """
        model = Publisher
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Daily News Global',
                'required': 'required'
            })
        }

    def clean_name(self):
        """
        Performs unique validations across submitted corporate workspace names.

        Returns:
            str: Validated name text cleaned of duplicate casing anomalies.
            
        Raises:
            ValidationError: If an organization name matches a pre-registered workspace profile designation.
        """
        name = self.cleaned_data.get('name', '').strip()
        if Publisher.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A corporate publishing profile already matches that designation.")
        return name

# news_api/forms.py
"""
Form definitions for the news portal multi-tenant ecosystem layer.

Handles combined user registration with optional corporate profile provisioning,
as well as staff assignment workflows.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Publisher

User = get_user_model()


class CustomUserRegistrationForm(UserCreationForm):
    """
    Form handling the multi-role user registration pipeline.
    
    Includes an optional corporate title string field allowing users to establish 
    and provision an organization brand profile simultaneously during signup.
    """
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES, 
        required=True, 
        help_text="Select your platform access tier profile type."
    )
    new_publisher_name = forms.CharField(
        max_length=255, 
        required=False, 
        label="Publisher Company/Brand Title",
        help_text="Required only if registering an organizational workspace profile.",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Daily Chronicle Global'})
    )

    class Meta(UserCreationForm.Meta):
        """
        Binds form properties directly onto target operational schema columns.
        """
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'role')

    def clean(self):
        """
        Enforces tenant validation constraints, protecting against missing definitions.
        """
        cleaned_data = super().clean()
        role = cleaned_data.get('role', '').lower().strip()
        pub_name = cleaned_data.get('new_publisher_name', '').strip()

        # FIXED: Removed 'or role == 'editor'' so that only the Publisher role 
        # is strictly required to provide an organization brand title upfront.
        if role == 'publisher' and not pub_name:
            self.add_error(
                'new_publisher_name', 
                "An organization brand title must be specified to initialize a publication workspace profile."
            )
            
        if pub_name and Publisher.objects.filter(name__iexact=pub_name).exists():
            self.add_error(
                'new_publisher_name', 
                "A publication workspace brand under this designation already exists."
            )
            
        return cleaned_data


class AdminPublisherInitializationForm(forms.ModelForm):
    """
    Form for System Administrators to initialize a Publisher completely independently.

    Provides multi-selection checklist parameters to query and assign existing, unlinked 
    system-wide Editors and staff Journalists to a brand-new publishing organization footprint.
    """
    assign_editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role__iexact='editor', publisher_editors__isnull=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Assign Workspace Managers (Editors)",
        help_text="Select one or more existing unassigned Editors to link to this new Publisher."
    )
    assign_journalists = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role__iexact='journalist', publisher_journalists__isnull=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Assign Staff Writers (Journalists)",
        help_text="Select staff journalists to bind directly to this media organization pool."
    )

    class Meta:
        """
        Maps standard configuration fields to underlying corporate model fields.
        """
        model = Publisher
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Global News Chronicle',
                'style': 'width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #ccc;'
            })
        }

    def clean_name(self):
        """
        Validates uniqueness constraints across corporate publisher workspace titles.

        Returns:
            str: Sanitized and validated publisher name text string.
            
        Raises:
            ValidationError: If the designated publisher name is already registered in the system database.
        """
        name = self.cleaned_data.get('name', '').strip()
        if Publisher.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A publishing house under this designation already exists.")
        return name


class ArticleModelForm(forms.ModelForm):
    """
    Form layout managing article generation with dynamic tenant query isolation.
    """
    class Meta:
        model = Article
        fields = ['title', 'content', 'publisher']

    def __init__(self, *args, **kwargs):
        # Extract the request user context passed down from the active view session
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.role.lower() == 'journalist':
            self.fields['publisher'].queryset = Publisher.objects.filter(journalists=user)
            self.fields['publisher'].required = False
