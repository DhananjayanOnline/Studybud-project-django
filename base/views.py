

from multiprocessing import context
from urllib import request
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Topic, Message
from .forms import RoomForm

# Create your views here.

# rooms = [
#     {'id':1, 'name':'Lets learn python!'},
#     {'id':2, 'name':'Design with me'},
#     {'id':3, 'name':'Frontend developers'},
# ]


def loginPage(request):

    page = 'login'

    if request.user.is_authenticated:           # if an already logged in user trys to go to the login page; redirect the user to the home page
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()  # these 2 values will be send from the frontend
        password = request.POST.get('password')  #---------------------------------------------#

        try:
            user = User.objects.get(username=username)      # if the user doesnot exist
        except:
            messages.error(request, 'User does not exist')  #-------------------------$

        user = authenticate(request, username=username, password=password)  # authenticate username and password, its either going to give us an error or it's going to return back a user object that matches these credentials

        if user is not None:
            login(request, user)                # login()- thats going to do is, its going to go ahead and add in that session in the database and then inside of our browser and the user wil be officially logged-in.
            return redirect('home')
        else:
            messages.error(request, 'Username OR Password does not exist')

    context = {'page':page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()  #convert the username that enter by the user into lower case
            user.save()
            login(request, user)    # the user that just registed going to log in and send them to the home page
            return redirect('home')
        else:
            messages.error(request, 'An error occured during registration')

    return render(request,'base/login_register.html', {'form':form})


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(               #search bar
        Q(topic__name__icontains=q) | 
        Q(name__icontains=q) |
        Q(discription__icontains=q)
        )                                      #----#

    topics = Topic.objects.all()   #display all topics in the side bar
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms':rooms, 'topics':topics, 'room_count':room_count, 'room_messages':room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()  # message_set.all() :- it's basically saying give us the set of messages that are related to this specific 'room',  message_set.all() -> 'message = Message model' (model name is in uppercase but here we use lower case letter)
    participants = room.participants.all()  # because it is a ManyToMany relationship
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)     # when a new user send a message in the room, then the user will be added in the participants list
        return redirect('room', pk=room.id)
    
    context = {'room':room, 'room_messages':room_messages, 'participants':participants}

    return render(request, 'base/room.html',context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user':user, 'rooms':rooms, 'room_messages':room_messages, 'topics':topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()

    if request.method == 'POST':                    #save form value into the model
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)  # host will be added based on whoever's logged in 
            room.host = request.user
            room.save()                     #-----------------------------------------------#
            return redirect('home')                 #------------------------------#

    context = {'form':form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)      #this from will prefill the value of the selected room


    if request.user != room.host:                           # if a user is not the correct user
        return HttpResponse('You are not allowed here!!')


    if request.method == 'POST':                        #save updated form value into the model
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')                     #---#

    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:                           # if a user is not the correct user
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj':room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:                           # if a user is not the correct user
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj':message})
