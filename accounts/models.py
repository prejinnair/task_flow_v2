from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from accounts.utils import send_verification_email

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password=None,):
        if not email:
            raise ValueError('User must enter an Email')
        if not username:
            raise ValueError("user must enter a username")
        
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
        )
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self,first_name,last_name ,username, email, password):
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save()
        return user

SUPER_ADMIN = 0
ADMIN = 1
MANAGER = 2
DEVELOPER = 3
QA = 4
VIEWER = 5

ROLE_CHOICES = (
    (SUPER_ADMIN, 'Super Admin'),
    (ADMIN, 'Admin'),
    (MANAGER, 'Manager'),
    (DEVELOPER, 'Developer'),
    (QA, 'QA'),
    (VIEWER, 'Viewer'),
)

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phonenumber = models.CharField(max_length=12)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, blank=True, null=True)

    #required fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return self.username
    
    def has_perm(self, perm_code):
        if self.is_superadmin:
            return True
        if super().has_perm(perm_code, obj=None):
            return True
        return self.manual_permissions.filter(permission=perm_code).exists()
    
    def has_module_perms(self, app_label):
        return True
    



    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', blank=True, null=True)
    avatar = models.ImageField(upload_to='users/profile_pictures', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

class UserPermission(models.Model):
    PERMISSION_CHOICES = [
        ('create_project', 'Create Project'),
        ('manage_projects', 'Manage Projects'),
        ('create_teams', 'Create Teams'),
        ('manage_teams', 'Manage Teams'),
        ('manage_users', 'Manage Users'),
        ('view_all_projects', 'View All Projects'),
        ('view_all_teams', 'View All Teams'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manual_permissions')
    permission = models.CharField(max_length=50, choices=PERMISSION_CHOICES)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'permission')

    def __str__(self):
        return f"{self.user.email} - {self.permission}"