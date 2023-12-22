from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
import os


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30)
    full_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


def generate_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('images/', filename)


class ChatBot(models.Model):
    id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    chat_conf = models.TextField(max_length=800)
    is_active = models.BooleanField(default=True)
    like_cnt = models.IntegerField(default=0)
    dislike_cnt = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to=generate_filename,default="images/default.png")

    # Like Increment
    def like_inc(self, check):
        if check:
            self.like_cnt += 1
        else:
            self.like_cnt -= 1
        self.save()

    # DisLike Increment
    def dislike_inc(self, check):
        if check:
            self.dislike_cnt += 1
        else:
            self.dislike_cnt -= 1

        self.save()

    def __str__(self):
        return self.name


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=40)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chatbot = models.ForeignKey(ChatBot, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Message(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_user = models.BooleanField(default=True)
    is_liked = models.BooleanField(default=False)
    is_disliked = models.BooleanField(default=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    embedding = models.TextField()
