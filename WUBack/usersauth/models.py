from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class WU_UserManager(BaseUserManager):
    def create_user(self, username, code=None, password=None):
        if not username:
            raise ValueError("Users need username!!!!")

        user = self.model(username=username, code=code)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, password, code=None):
        user = self.create_user(
            username=username, code=code, password=password)
        user.is_student = False
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user


class WU_User(AbstractBaseUser):
    username = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=20, null=True)
    last_name = models.CharField(max_length=30, null=True)

    code = models.CharField(max_length=151, null=True)
    code_expiration_date = models.DateTimeField(
        verbose_name="code expiration date", null=True
    )
    date_joined = models.DateTimeField(
        verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_student = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"

    objects = WU_UserManager()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True
