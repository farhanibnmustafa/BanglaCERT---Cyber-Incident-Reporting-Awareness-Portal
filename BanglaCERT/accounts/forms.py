from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm


User = get_user_model()


def build_unique_username(email):
    base = email.split("@", 1)[0] or "user"
    base = "".join(ch for ch in base if ch.isalnum() or ch in {"_", "."}) or "user"
    base = base[:150]
    candidate = base
    index = 1
    while User.objects.filter(username=candidate).exists():
        suffix = f"_{index}"
        candidate = f"{base[:150 - len(suffix)]}{suffix}"
        index += 1
    return candidate


class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(required=False, max_length=150)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].label = "Full Name"
        self.fields["full_name"].widget.attrs.update(
            {
                "placeholder": "Enter your full name",
                "autocomplete": "name",
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "placeholder": "Enter your email",
                "autocomplete": "email",
            }
        )
        self.fields["password1"].widget.attrs.update(
            {
                "placeholder": "Enter password",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "placeholder": "Confirm password",
                "autocomplete": "new-password",
            }
        )

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"]
        user.email = email
        user.username = build_unique_username(email)
        full_name = (self.cleaned_data.get("full_name") or "").strip()
        if full_name:
            name_parts = full_name.split(None, 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ""
        if commit:
            user.save()
        return user


class StaffUserCreationForm(UserRegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].help_text = "This person will sign in using this email or their username."

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        user.is_superuser = False
        if commit:
            user.save()
        return user


class StaffPromotionForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.none(), label="Existing user")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(is_staff=False).order_by("email", "username")
        self.fields["user"].empty_label = "Select a user"


class EmailLoginForm(forms.Form):
    email = forms.CharField(required=True, label="Email or Username")
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    error_message = "Invalid email/username or password."

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.staff_only = kwargs.pop("staff_only", False)
        self.user_cache = None
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update(
            {
                "placeholder": "Enter your email or username",
                "autocomplete": "username",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "placeholder": "Enter password",
                "autocomplete": "current-password",
            }
        )

    def clean(self):
        cleaned_data = super().clean()
        identifier = (cleaned_data.get("email") or "").strip()
        password = cleaned_data.get("password")

        if not identifier or not password:
            return cleaned_data

        user_by_identifier = User.objects.filter(username__iexact=identifier).first()
        if user_by_identifier is None:
            user_by_identifier = User.objects.filter(email__iexact=identifier).first()

        if user_by_identifier is None:
            raise forms.ValidationError(self.error_message)

        user = authenticate(
            request=self.request,
            username=user_by_identifier.get_username(),
            password=password,
        )
        if user is None:
            raise forms.ValidationError(self.error_message)
        if not user.is_active:
            raise forms.ValidationError("This account is inactive.")
        if self.staff_only and not user.is_staff:
            raise forms.ValidationError("This login page is for staff users only.")

        self.user_cache = user
        return cleaned_data

    def get_user(self):
        return self.user_cache

class AdminExcludedPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """
        Exclude staff (admin) users from the password reset flow.
        """
        active_users = super().get_users(email)
        return [u for u in active_users if not u.is_staff]
