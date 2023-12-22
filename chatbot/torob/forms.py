from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, ChatBot
from django import forms

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.TextInput(attrs={'autofocus': True}))

    class Meta:
        model = User  # Your custom user model
        fields = ['username', 'password']


class CreateChatBotForm(forms.ModelForm):
    class Meta:
        model = ChatBot
        fields= ['avatar', 'name', 'chat_conf'] 