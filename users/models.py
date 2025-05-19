
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(verbose_name='phone', max_length=30)
    profile_pic = models.ImageField(upload_to='upload_folder_path', blank=True, null=True)