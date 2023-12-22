from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import SignUpForm, LoginForm, CreateChatBotForm
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from .models import Conversation, User, ChatBot, Message
from .aichat import generate_response, get_embedding
import json
from .utils import calc_cosine_similarity

def signup(request):
    if request.user.is_authenticated:
        return redirect('chat_list')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data['email']
            raw_password = form.cleaned_data['password1']
            user = authenticate(email=email, password=raw_password)
            login(request, user)
            return redirect('chat_list')  # Redirect to your home page
        else:
            print(form.errors)
    else:
        form = SignUpForm()
    return render(request, 'torob/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat_list')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('chat_list')  # Redirect to your home page
            else:
                form.add_error(None, 'Invalid credentials. Please try again.')
        else:
            print(form.errors)
    else:
        form = LoginForm()

    return render(request, 'torob/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')


# def chat_list(request):
#     if not request.user.is_authenticated: 
#         return redirect('login_view')

#     # Retrieve all active "ChatBot" records 
#     filtered_records = ChatBot.objects.filter(is_active=True)

#     # Pass the filtered records to the template context
#     context = {'filtered_records': filtered_records}

#     # Render the template with the context
#     return render(request, 'chat-list.html', context) 

def chat_list(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Retrieve user's conversation
    user = User.objects.get(email=request.user)
    user_conversations = Conversation.objects.filter(user=user)

    # Show 10 records per page
    paginator = Paginator(user_conversations, 3)
    page_num = request.GET.get("page")
    if not page_num:
        page_num = 1
    page_obj = paginator.get_page(page_num)
    return render(request, "torob/chat-list.html",
                  {"count": paginator.num_pages, "page_obj": page_obj, "page_num": int(page_num)})


def create_chat(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = User.objects.get(email=request.user)
    user_chatbots = ChatBot.objects.filter(creator=user)

    # Show active chatbots
    chat_bots = ChatBot.objects.filter(is_active=True)
    return render(request, "torob/create-chat.html", {"user_chatbots": user_chatbots, "chat_bots": chat_bots})


def chat_details(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    bot_id = request.GET.get("bot_id")
    if bot_id:
        try:
            bot = ChatBot.objects.get(id=int(bot_id))
            if not bot.is_active:
                return redirect('create_chat')
            return render(request,"torob/chat-details.html",{"conversation_id":"","messages":"","bot_id":bot_id})
        except:
            return redirect('create_chat')

    try:
        conversation_id = request.GET.get("id")
        conversation = Conversation.objects.get(id=conversation_id)
    except:
        return redirect('chat_list')

    user = User.objects.get(email=request.user)
    if conversation.user != user:
        print(user.email)
        print(conversation.chatbot.creator.email)
        return redirect('chat_list')
    else:
        messages = Message.objects.filter(conversation=conversation)
    return render(request, "torob/chat-details.html", {"messages": messages,"conversation_id": conversation_id,"bot_id":""})


def like_message(request,message_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthorized', 'is_liked': ''}, status=403)
    if request.method == 'GET':
        try:
            message = Message.objects.get(id=message_id)
            user = User.objects.get(email=request.user)
            if message.conversation.user == user:
                message.is_liked = not message.is_liked
                message.conversation.chatbot.like_inc(message.is_liked)
                message.save()
                return JsonResponse({'status': 'success', 'is_liked': message.is_liked},status=200)
            else:
                return JsonResponse({'status': 'unauthorized', 'is_liked':''},status=403)
        except:
            return JsonResponse({'status': 'unauthorized','is_liked':''},status=400)

def dislike_message(request,message_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthorized', 'is_disliked': ''}, status=403)
    if request.method == 'GET':
        try:
            message = Message.objects.get(id=int(message_id))
            user = User.objects.get(email=request.user)
            if message.conversation.user == user:
                message.is_disliked = not message.is_disliked
                message.conversation.chatbot.dislike_inc(message.is_liked)
                message.save()

                sent_message = Message.objects.get(id=message_id-1)

                text = f"I asked you this: {sent_message.content}. You responded: {message}. I did not like this response please provide me a different one."
                bot_role = message.conversation.chatbot.chat_conf
                res = generate_response(bot_role, text)

                # Convert embedding array to json str.
                res_embedding = get_embedding(res)

                res_json_str = json.dumps(res_embedding)

                bot_message = Message(is_user=False, content=res, conversation=message.conversation, embedding=res_json_str)
                bot_message.save()

                return JsonResponse({'status': 'success', 'is_disliked': message.is_disliked},status=200)
            else:
                return JsonResponse({'status': 'unauthorized', 'is_disliked':''}, status=403)
        except:
            return JsonResponse({'status': 'unauthorized','is_disliked':''}, status=400)

def send_message(request):
    if not request.user.is_authenticated:
        return redirect('login')
    conversation_id = request.GET.get('conversation_id')
    if request.method == 'POST':
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            user = User.objects.get(email=request.user)
            if conversation.user == user:
                text = request.POST.get("newMessage")
                bot_role = conversation.chatbot.chat_conf
                res = generate_response(bot_role,text)

                text_embedding = get_embedding(text)

                # Convert embedding array to json str.
                text_json_str = json.dumps(text_embedding)

                res_embedding = get_embedding(res)
                res_json_str = json.dumps(res_embedding)

                user_message = Message(content = text,conversation=conversation, embedding=text_json_str)
                user_message.save()

                bot_message = Message(is_user=False,content=res,conversation=conversation, embedding=res_json_str)
                bot_message.save()
                
                return JsonResponse({'status':'success'},status=200)
            else:
                return JsonResponse({'status': 'unauthorized'},status=403)
        except:
            return JsonResponse({"status":'bad request'}, status=400)

def new_conversation(request):
    if not request.user.is_authenticated:
        return redirect('login')
    bot_id = request.GET.get('bot_id')
    if request.method == 'POST':
        try:
            bot = ChatBot.objects.get(id=int(bot_id))
            user = User.objects.get(email=request.user)
            text = request.POST.get("newMessage")
            title = generate_response("create title for user input only less than 3 words",text)
            res = generate_response(bot.chat_conf,text)

            text_embedding = get_embedding(text)

            # Convert embedding array to json str.
            text_json_str = json.dumps(text_embedding)

            res_embedding = get_embedding(res)
            res_json_str = json.dumps(res_embedding)

            conversation = Conversation(name=title,user=user,chatbot=bot)
            conversation.save()
            user_message = Message(content=text, conversation=conversation, embedding=text_json_str)
            user_message.save()
            bot_message = Message(content=res,is_user=False,conversation=conversation, embedding=res_json_str)
            bot_message.save()
            return JsonResponse({'status':'success','conversation_id':conversation.id},status=200)
        except:
             return JsonResponse({"status":'bad request'}, status=400)
    
    return JsonResponse({"status":'bad request'}, status=400)

def create_bot(request):
    if not request.user.is_authenticated: 
        return redirect('login')
    
    if request.method == 'POST':
        bot_id = request.GET.get('id')
        
        if not bot_id: 
            form = CreateChatBotForm(request.POST,request.FILES)
            user = User.objects.get(email=request.user)
            if form.is_valid():
                print(form.cleaned_data['avatar'])
                chatbot = ChatBot(
                    creator = user,
                    name = form.cleaned_data['name'],
                    chat_conf = form.cleaned_data['chat_conf'],
                    avatar = form.cleaned_data['avatar']
                )
                
                chatbot.save()
                
                return redirect('chat_list')
            else: 
                print(form.errors)
        else:
            bot = ChatBot.objects.get(id=int(bot_id))
            form = CreateChatBotForm(request.POST, request.FILES, instance=bot)
                    
            if form.is_valid():
                form.save()
                return redirect('chat_list')
            else: 
                print(form.errors)
        
    else:
        form = CreateChatBotForm()
 
    return render(request, "torob/create-bot.html")
        

def edit_bot(request):
    if not request.user.is_authenticated: 
        return redirect('login')

    bot_id = request.GET.get("id")

    try:
        bot = ChatBot.objects.get(id=int(bot_id))
        user = User.objects.get(email=request.user) 
        if bot.creator != user:
            return redirect("create_chat")
    except:
        return redirect("create_chat")
    
    return render(request, 'torob/edit-bot.html',{'bot':bot })


def search_result(request):
    if not request.user.is_authenticated: 
        return redirect('login')

    if request.method == "GET":
        search_value = request.GET.get("search")
        search_embedding = get_embedding(search_value)

        user = User.objects.get(email=request.user)
        user_conversations = Conversation.objects.filter(user=user)

        top_matches = {}
        for conversation in user_conversations: 
            user_messages = Message.objects.filter(conversation=conversation)

            for message in user_messages:

                message_embedding = json.loads(message.embedding)
                similarity = calc_cosine_similarity(search_embedding, message_embedding)

                if similarity < 0.8: 
                    continue

                if len(top_matches) < 5: 
                    top_matches[message.id] = similarity
                else:
                    min_key = min(top_matches, key=top_matches.get)

                    if similarity > top_matches[min_key]:
                        del top_matches[min_key]
                        top_matches[message.id] = similarity

        search_results = []
        for key in top_matches: 
            foundMsg = Message.objects.get(id=key)
            search_results.append(foundMsg)

    return render(request, 'torob/search-result.html', {"search_results": search_results})