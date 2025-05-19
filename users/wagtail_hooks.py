from wagtail.users.views.users import UserViewSet
from wagtail import hooks

from .forms import CustomUserEditForm, CustomUserCreationForm


class CustomUserViewSet(UserViewSet):
    add_form_class = CustomUserCreationForm
    edit_form_class = CustomUserEditForm


@hooks.register('construct_user_viewset')
def override_user_viewset(viewset_class):
    return CustomUserViewSet