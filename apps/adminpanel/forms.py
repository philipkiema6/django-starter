from allauth.account.models import EmailAddress
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.users.models import CustomUser, Profile


class AdminCreateUserForm(forms.ModelForm):
    """Used by staff to provision an Instructor or Student account directly, skipping the
    public signup flow. The created account is active and its email is marked verified —
    staff are vouching for it, so there's no confirmation step to run."""

    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, initial=Profile.ROLE_STUDENT, label=_("Role"))
    password = forms.CharField(widget=forms.PasswordInput, min_length=8, label=_("Initial password"))

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()  # apps.users.signals.create_profile creates user.profile here
            user.profile.role = self.cleaned_data["role"]
            user.profile.save()
            EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
        return user
