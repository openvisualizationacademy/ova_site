from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.users.forms import UserEditForm, UserCreationForm
from wagtail.images.widgets import AdminImageChooser
from wagtail.images import get_image_model


class CustomUserEditForm(UserEditForm):
    phone = forms.CharField(max_length=30, required=True, label=_("Phone"))
    profile_pic = forms.ModelChoiceField(
        queryset=get_image_model().objects.all(),
        widget=AdminImageChooser(),
        label=_('Profile Picture'),
    )


class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(max_length=30, required=True, label=_("Phone"))
    profile_pic = forms.ModelChoiceField(
        queryset=get_image_model().objects.all(),
        widget=AdminImageChooser(),
        label=_('Profile Picture'),
    )
