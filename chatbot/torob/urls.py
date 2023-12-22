from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import signup, login_view, chat_list, custom_logout, create_chat, create_bot, chat_details, like_message, \
    dislike_message, send_message, create_bot, edit_bot,new_conversation, search_result

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),
    path('', chat_list, name='chat_list'),
    path('logout/', custom_logout, name='logout'),
    path('create_chat/', create_chat, name='create_chat'),
    path('create-bot/', create_bot, name='create-bot'),
    path('chat_details/', chat_details, name='chat_details'),
    path('like_message/<int:message_id>', like_message, name='like_message'),
    path('dislike_message/<int:message_id>', dislike_message, name='dislike_message'),
    path('send_message/',send_message, name='send_message'),
    path('edit-bot/', edit_bot, name="edit-bot"),
    path('new-conversation/',new_conversation,name='new-conversation'),
    path('search-result/', search_result, name='search-result'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
