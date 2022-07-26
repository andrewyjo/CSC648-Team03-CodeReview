#░█▀▀░█▀█░█▀▄░█▀▀░░░█▀▄░█▀▀░█░█░▀█▀░█▀▀░█░█░░░█▀█░█▀█░█▀▄░▀█▀░░░▀█░
#░█░░░█░█░█░█░█▀▀░░░█▀▄░█▀▀░▀▄▀░░█░░█▀▀░█▄█░░░█▀▀░█▀█░█▀▄░░█░░░░░█░
#░▀▀▀░▀▀▀░▀▀░░▀▀▀░░░▀░▀░▀▀▀░░▀░░▀▀▀░▀▀▀░▀░▀░░░▀░░░▀░▀░▀░▀░░▀░░░░▀▀▀
#
# Contributors: William P, Andy C, Soujanya N
# Version: 2.1.0
# Last Updated: July 25, 2022
# Description: This file stores the view functions for various important functions related to authentication, support, and other functionalities
# that are unrelated to particular apps like events and groups.
#
#CODE-REVIEW Part 1: This file contains only the functionality that is used by our Non-Functional Requirement Testing; it is contained within a file called views.py within our home app directory.
#As such, it contains the following cases:
# 1.a) 7.1 : "The application's back-end servers should never display a user's password in cleartext"
# 1.b) 2.1 : "Users shall receive online help from support for any assistance on the application."
#########################################
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from ipware import get_client_ip
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from . import models
from . import forms


# QA Testing - Code Review Part 1.a
# Cases: 
# 7.1 : "The application's back-end servers should never display a user's password in cleartext"

# registrationPage - This view utilizes existing backend django authentication libraries to securely create a user and adhere to existing security practices.
def registrationPage(request):
    #Initialize a session within django's session library
    sessionCreation(request)

    #Debugging statements
    # print(request.session.session_key)
    # print(request.session['visitorIP'])

    #Initialize an empty form
    user_form = forms.userRegistrationForm()
    accountForm = forms.accountForm()

    #Handling the POST request sent by the user upon form completion
    if request.method == 'POST':
        # Prepare the session and the forms.
        sessionCreation(request)
        user_form = forms.userRegistrationForm(request.POST)
        accountForm = forms.accountForm(request.POST)
        profileForm = forms.profileForm(request.POST)
        
        # Check for Validation errors and send them back to the page
        if not user_form.is_valid():
            print(user_form.errors)
            return render(request, 'register.html', {'user_form': user_form, 'accountForm': accountForm, 'feedback': "Error", 'error': user_form.errors})
        elif not accountForm.is_valid():
            print(accountForm.errors)
            return render(request, 'register.html', {'user_form': user_form, 'accountForm': accountForm, 'feedback': "Error", 'error': accountForm.errors})
        elif not profileForm.is_valid():
            print(profileForm.errors)
            return render(request, 'register.html', {'user_form': user_form, 'accountForm': accountForm, 'feedback': "Error", 'error': profileForm.errors})
        else:
            # Save the user, the account, and log in the new user
            user = user_form.save()
            account = accountForm.save(commit=False)
            account.accountID = user
            account.save()
            account.trackingID = request.session.session_key
            username = request.POST['username']
            #The following utilizes Django's authentication libraries to encrypt and store the password in a secure fashion.
            password = request.POST['password1']
            user = authenticate(request, username=username, password=password)
            account.save()
            if user is not None:
                login(request, user)
                # trying to figure out how to put the next 3 lines above 'if user is not None'
                profile = profileForm.save(commit=False)
                profile.profileID = request.user
                profile.save()
                return render(request, "home.html", {'userID': userID, 'fname': fname, 'lname': lname, 'email': email, 'gender': gender, 'dob': dob, 'message': "You've successfully created an account. Welcome to PlayDate!"})
            else:
                # There was an error authenticating the newly registered user.
                return render(request, "invalidLogin.html")
    # If just a GET request, then send them the html.
    return render(request, 'register.html', {'user_form': user_form, 'accountForm': accountForm})


# QA Testing - Code Review Part 1.b
# Cases: "Users shall receive online help from support for any assistance on the application"

# helpPage - this encompasses the support page that a user can access which will redirect them to a form where they can submit their ticket into the
# support-table of the database.
def helpPage(request):
    #initializing variables respective to the user so it can be inputted into the support form.
    if request.method == "GET":
        if request.user.is_authenticated:
            name = request.user.first_name + ' ' + request.user.last_name
            name = name + ' (' + request.user.username + ')'
            email = request.user.email
            print("Support GOT")
            print("Name: "+name)
            print("Email: "+email)
            return render(request, 'helpPage.html', {'name': name, 'email': email})
        return render(request, 'helpPage.html')
    else:
        print('*******************************')
        print('Support Contact form Submitted by ' + request.user.get_username())
        if request.method == 'POST':
            data = {
                'name': request.POST['name'],
                'contact': request.POST['email'],
                'type': request.POST['category'],
                'subject': request.POST['subject'],
                'details': request.POST['message']}
            csForm = forms.supportForm(data)
            # validate the form:
            #  Not actually necessary, but is proper.
            if csForm.is_valid():
                print('Form is valid.')
                ticket = csForm.save(commit=False)

                # Grab Registered user data
                if request.user.is_authenticated:
                    ticket.accountID = request.user
                    print('User is authenticated: ' + request.user.username)

                # Grab General User Data
                ipAddr = request.META['REMOTE_ADDR']
                print('IP Address: ' + str(ipAddr))
                try:  # Grabbing specific users may fail
                    print('Trying to fill General User...')
                    userQuery = models.generalUser.objects.get(ip=ipAddr)
                    print('Query Success...')
                    userInfo = userQuery.first()
                    print('Using general user: ' + userInfo)
                except:  # If we cannot find the general user, make one.
                    print('Exception Caught - Query Error')
                    userInfo = models.generalUser(ip=ipAddr)
                    userInfo.save()
                    print('Using new General User: ' + userInfo.ip)
                else:
                    print("General User found")
                finally:
                    ticket.general = userInfo
                    # Grab Support Staff Data
                    try:  # No Support Staff will throw an exception
                        print('Trying to fill support staff...')
                        staffQuery = models.Supportstaff.objects.all()
                        print('Query Success...')
                        staffInfo = staffQuery.first()
                        print('Using Staff: ' + staffInfo.staff_email + '\n')
                        status = 'Success'
                        ticket.staff = staffInfo
                    except:
                        print("No staff to send support request to")
                        status = 'No Staff'
                    finally:
                        ticket.save()
                        print(ticket)
                        # If we did find staff, attempt the email
                        if status == 'Success':
                            email_subject = 'PlayDate Support #' + \
                                str(ticket.request_id) + ': ' + ticket.name
                            email_content = email_subject + '\n'
                            email_content += 'User: '
                            if request.user.is_authenticated:
                                email_content += request.user.get_username()
                            else:
                                email_content += ipAddr
                            email_content += '\nEmail: ' + ticket.accountID.email + '\n'
                            email_content += 'Category: ' + ticket.get_type_display() + '\n'
                            email_content += 'Details: \n\t' + ticket.details + '\n\n'
                            email_from = 'support@playdate.com'
                            email_to = staffInfo.staff_email
                            print('Email Description: ')
                            print("Subject: " + email_subject)
                            print("Content: " + email_content)
                            print("From: " + email_from)
                            print("To: " + email_to)
                            # Note: this function will not work until SMTP server set up.
                            # For now, fail silently.
                            send_mail(
                                email_subject,
                                email_content,
                                email_from,
                                [email_to],
                                fail_silently=True
                            )
                        # Return the user to the contact support page with a status to be displayed.
                        retVals = {
                            'name': data["name"],
                            'email': data["contact"],
                            'category': data["type"],
                            'subject': data["subject"],
                            'message': data["details"],
                            'modalTitle': "Success!",
                            'modalText': "Your support request has been successfully raised.",
                            'modalBtnText': "Close",
                            'modalImmediate': True}
                        return render(request, 'helpPage.html', retVals)
        return render(request, 'helpPage.html')


# This function allows the user to submit a support ticket where they can establish an email discussion with support staff to solve their issue.
def contactSupport(request):
    csForm = forms.supportForm()
    print('*******************************')
    print('Support Contact form Submitted by ' + request.user.get_username())
    if request.method == 'POST':
        print(request.POST)
        csForm = forms.supportForm(request.POST)
        # validate the form:
        #  Not actually necessary, but is proper.
        if csForm.is_valid():
            print('Form is valid.')
            ticket = csForm.save(commit=False)

            # Grab Registered user data
            if request.user.is_authenticated:
                ticket.accountID = request.user
                print('User is authenticated: ' + request.user.username)

            # Grab General User Data
            ipAddr = request.META['REMOTE_ADDR']
            print('IP Address: ' + str(ipAddr))
            try:  # Grabbing specific users may fail
                print('Trying to fill General User...')
                userQuery = models.generalUser.objects.get(ip=ipAddr)
                print('Query Success...')
                userInfo = userQuery.first()
                print('Using general user: ' + userInfo)
            except:  # If we cannot find the general user, make one.
                print('Exception Caught - Query Error')
                userInfo = models.generalUser(ip=ipAddr)
                userInfo.save()
                print('Using new General User: ' + userInfo.ip)
            else:
                print("General User found")
            finally:
                ticket.general = userInfo
                # Grab Support Staff Data
                try:  # No Support Staff will throw an exception
                    print('Trying to fill support staff...')
                    staffQuery = models.Supportstaff.objects.all()
                    print('Query Success...')
                    staffInfo = staffQuery.first()
                    print('Using Staff: ' + staffInfo.staff_email + '\n')
                    status = 'Success'
                    ticket.staff = staffInfo
                except:
                    print("No staff to send support request to")
                    status = 'No Staff'
                finally:
                    ticket.save()
                    print(ticket)
                    # If we did find staff, attempt the email
                    if status == 'Success':
                        email_subject = 'PlayDate Support #' + \
                            str(ticket.request_id) + ': ' + ticket.name
                        email_content = email_subject + '\n'
                        email_content += 'User: '
                        if request.user.is_authenticated:
                            email_content += request.user.get_username()
                        else:
                            email_content += ipAddr
                        email_content += '\nEmail: ' + ticket.accountID.email + '\n'
                        email_content += 'Category: ' + ticket.get_type_display() + '\n'
                        email_content += 'Details: \n\t' + ticket.details + '\n\n'
                        email_from = 'support@playdate.com'
                        email_to = staffInfo.staff_email
                        print('Email Description: ')
                        print("Subject: " + email_subject)
                        print("Content: " + email_content)
                        print("From: " + email_from)
                        print("To: " + email_to)

                        #Finally send the email
                        send_mail(
                            email_subject,
                            email_content,
                            email_from,
                            [email_to],
                            fail_silently=True
                        )
                    # Return the user to the contact support page with a status to be displayed.
                    return render(request, 'contactSupport.html', {'csForm': csForm, 'status': status})
    return render(request, 'contactSupport.html', {'csForm': csForm})
