from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, default=False)
    phone = models.CharField(max_length=15, default=False)
    username = models.CharField(max_length=15, default=False)
    
    role = models.CharField(max_length=20, choices=[('Board Manager', 'Board Manager'), ('Developer', 'Developer')])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name', 'phone', 'role']

    def __str__(self):
        return self.email

    # Specify unique related_name for groups
    groups = models.ManyToManyField(
        to='auth.Group',
        related_name='custom_user_groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups'
    )

    # Specify unique related_name for user_permissions
    user_permissions = models.ManyToManyField(
        to='auth.Permission',
        related_name='custom_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

class SomeModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    developers = models.ManyToManyField(User, related_name='projects')
    board_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='board_projects')


class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    categories = models.ManyToManyField('Category', blank=True)
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    priority = models.CharField(max_length=20, choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')])
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=20, choices=[('Not Started', 'Not Started'), ('In Progress', 'In Progress'), ('Completed', 'Completed')])


class Category(models.Model):
    name = models.CharField(max_length=50)


class Comment(models.Model):
    text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    file = models.FileField(upload_to='comments/', null=True, blank=True)
