from django.contrib import admin
from .models import Conversation, ChatBot, User, Message

# Register your models here.
admin.site.register(ChatBot)
admin.site.register(User)
admin.site.register(Conversation)
admin.site.register(Message)
