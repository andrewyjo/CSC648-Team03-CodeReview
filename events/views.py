###################################################################
#░█▀▀░█▀█░█▀▄░█▀▀░░░█▀▄░█▀▀░█░█░▀█▀░█▀▀░█░█░░░█▀█░█▀█░█▀▄░▀█▀░░░▀▀▄
#░█░░░█░█░█░█░█▀▀░░░█▀▄░█▀▀░▀▄▀░░█░░█▀▀░█▄█░░░█▀▀░█▀█░█▀▄░░█░░░░▄▀░
#░▀▀▀░▀▀▀░▀▀░░▀▀▀░░░▀░▀░▀▀▀░░▀░░▀▀▀░▀▀▀░▀░▀░░░▀░░░▀░▀░▀░▀░░▀░░░░▀▀▀
####################################################################
# Contributors: Soujanya N, Andy C
# Version: 1.8.0
# Last Updated: July 25, 2022
# Description: This file contains all event CRUD functionalities which encompasses public, group, and general events.


#Code-Review Part 2: Usability Testing: This file was generated for the sole purpose of code review. To reduce the 
#sheer size of the file, this file is an amalgamation of events/views.py and groups/views.py and contains functionalities we used to test events.

# 2.a) Creating Group/Public/General Events that can be queried based on certain parameters like category(kids or pets), location, keywords. 

#############################################

from multiprocessing import Event
from unicodedata import category
from unittest import result
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from home.forms import addressForm
from events.forms import eventForm
from events.forms import GroupEventForm, PublicEventForm
from events.models import Publicevent, Address, Event
from django.views.decorators.csrf import csrf_exempt
import requests

# Code Review #1 - Usability Test - CRUD Operations on Events
# eventSearch - this function is used to search for  public events based on filter criteria(category, location, etc).
def eventSearch(request):
    if request.method == 'GET':
        query = request.GET.get('q')
        filter = request.GET.get('category')

        submitbutton = request.GET.get('submit')
        print(query)

        # The following has 3 cases: When the filter returns events pertaining to ALL categories, Only Kids, or Only Pets
        if query is not None:
            if filter == 'All':
               # query databse to check if matching city, zipcode, or street

                lookups = Q(address__city__icontains=query) | Q(address__zipcode__icontains=query) | Q(
                    address__country__icontains=query) | Q(address__street__icontains=query)

                results = Publicevent.objects.filter(lookups)

            elif filter == 'Kids':
                # query databse to check if matching city, zipcode, or street

                lookups = Q(address__city__icontains=query) | Q(address__zipcode__icontains=query) | Q(
                    address__country__icontains=query) | Q(address__street__icontains=query)

                results = Publicevent.objects.filter(
                    lookups).filter(Q(category__icontains='kids'))
                print(filter)
            else:
                lookups = Q(address__city__icontains=query) | Q(address__zipcode__icontains=query) | Q(
                    address__country__icontains=query) | Q(address__street__icontains=query)

                results = Publicevent.objects.filter(
                    lookups).filter(Q(category__icontains='pets'))
                print(filter)

            context = {'results': results,
                       'submitbutton': submitbutton}
            return render(request, 'events/events.html', context)

    # If NONE value is POSTed, re-render the page.
    else:
        return render(request, 'events/events.html')
    return render(request, 'events/events.html')


# Filter - a helper function for search-related functions that retrieves query data.
def filter(request):
    if request.method == 'POST':
        select = request.GET.get('select')


# createPublicEvent - redirects the user to a form to create a PublicEvent object
def createPublicEvent(request):
    form = PublicEventForm()
    if request.method == 'POST':
        form = PublicEventForm(request.POST, request.FILES)
        if form.is_valid():
            instancePE = form.save(commit=False)
            instancePE.banner = None
            instancePE.banner = request.FILES['banner']
            instancePE.save()

            PublicEvent = Publicevent.objects.get(
                public_event_id=instancePE.public_event_id)
            return render(request, 'events/createPublicEventSuccess.html', {'PublicEvent': PublicEvent})

    return render(request, 'events/createPublicEventForm.html', {'publicEventForm': form})


# For creating a group event
def createGroupEvent(request):
    #Initialize context variables that are to be passed into the djangoHTML page
    group = models.Group.objects.get(group_id=request.session['group_id'])
    member_list = models.Member.objects.filter(group_id=group.group_id)
    isMember = True
    groupEvents = models.GroupEvent.objects.filter(group=group)
    groupPosts = models.Post.objects.filter(group=group)

    createGroupEventForm = forms.createGroupEventForm()

    #Handling the POST request for a new Group Event.
    if request.method == 'POST':
        createGroupEventForm = forms.createGroupEventForm(
            request.POST, request.FILES)
        # for debugging
        # print(request.FILES)
        # print(len(request.FILES))
        if createGroupEventForm.is_valid():
            instanceGroupEvent = createGroupEventForm.save(commit=False)
            instanceGroupEvent.user = request.user
            instanceGroupEvent.group = group

            # banner upload process
            instanceGroupEvent.banner = None
            if len(request.FILES) == 0:
                instanceGroupEvent.banner = None
            else:
                instanceGroupEvent.banner = request.FILES['banner']

            instanceGroupEvent.save()

            # Group/member/isMember is stored inside the session
            return render(request, "groups/groups.html", {'group': group, 'member_list': member_list, 'isMember': isMember, 'groupEvents': groupEvents, 'groupPosts': groupPosts})

        elif not createGroupEventForm.is_valid():
            #Print Console Errors for debugging
            print("FORM NOT VALID:", createGroupEventForm.errors,
                  "non-field errors:", createGroupEventForm.non_field_errors)

    return render(request, "groups/createGroupEvent.html", {"createGroupEventForm": createGroupEventForm})


# createEvent - redirects the user to a form for creating general events.
def createEvent(request):
    #initialize variables
    context = {}
    user = request.user

    #handling the form data via POST request
    if request.method == 'POST':
        eventform = eventForm(request.POST)
        addressform = addressForm(request.POST)

        if addressform.is_valid() and eventform.is_valid():
            address = addressform.save()
            print("**********")
            event = eventform.save(commit=False)
            event.user = user
            event.address = address
            event.save()
            print(event.event_id)

            return HttpResponseRedirect('/events/%s/' % event.event_id)

    #otherwise issue a blank form.
    else:
        eventform = eventForm()
        addressform = addressForm()
    # context['form']=form
    return render(request, 'createEvent.html', {'eventform': eventform, 'addressform': addressform})



