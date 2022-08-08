from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import History
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import auth_users, allowed_users
import json
import os
import platform
import pathlib
import time
from django.http import HttpResponse
from datetime import datetime,timezone,tzinfo
import pytz
import sys
import sqlite3
from django.views.decorators.csrf import csrf_exempt
import random
import string
import requests
import csv
from geopy.geocoders import Nominatim
import re
import math
# Create your views here.

#http://subzerocbd.info/#venues

headers = {
     'origin': 'https://resy.com',
     'accept-encoding': 'gzip, deflate, br',
     'x-origin': 'https://resy.com',
     'accept-language': 'en-US,en;q=0.9',
     'authorization': 'ResyAPI api_key="VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"',
     'content-type': 'application/x-www-form-urlencoded',
     'accept': 'application/json, text/plain, */*',
     'referer': 'https://resy.com/',
     'authority': 'api.resy.com',
     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
}

def login(username,password):
    data = {
      'email': username,
      'password': password
    }
    response = requests.post('https://api.resy.com/3/auth/password', headers=headers, data=data)
    res_data = response.json()
    try:
        auth_token = res_data['token']
    except KeyError:
        print("Incorrect username/password combination")
        return None, None
    payment_method_string = '{"id":' + str(res_data['payment_method_id']) + '}'
    return auth_token,payment_method_string

def find_table(res_date,party_size,table_time,auth_token,venue_id,file_to_use):
    #convert datetime to string
    day = res_date.strftime('%Y-%m-%d')
    params = (
     ('x-resy-auth-token',  auth_token),
     ('day', day),
     ('lat', '0'),
     ('long', '0'),
     ('party_size', str(party_size)),
     ('venue_id',str(venue_id)),
    )
    response = requests.get('https://api.resy.com/4/find', headers=headers, params=params)
    data = response.json()
    results = data['results']
    if len(results['venues']) > 0:
        open_slots = results['venues'][0]['slots']
        if len(open_slots) > 0:
            available_times = [(k['date']['start'],datetime.strptime(k['date']['start'],"%Y-%m-%d %H:%M:00").hour, datetime.strptime(k['date']['start'],"%Y-%m-%d %H:%M:00").minute) for k in open_slots]

            decimal_available_times = []
            for i in range (0, len(available_times)):
                decimal_available_times.append(available_times[i][1] + available_times[i][2]/60)

            absolute_difference_function = lambda list_value : abs(list_value - table_time)
            decimal_closest_time = min(decimal_available_times, key= absolute_difference_function)
            closest_time = available_times[decimal_available_times.index(decimal_closest_time)][0]

            #closest_time = min(available_times, key=lambda x:abs(x[1]-table_time))[0]
            best_table = [k for k in open_slots if k['date']['start'] == closest_time][0]
            return best_table

def make_reservation(auth_token, payment_method_string, config_id,res_date,party_size):
    #convert datetime to string
    day = res_date.strftime('%Y-%m-%d')
    party_size = str(party_size)
    params = (
         ('x-resy-auth-token', auth_token),
         ('config_id', str(config_id)),
         ('day', day),
         ('party_size', str(party_size)),
    )
    details_request = requests.get('https://api.resy.com/3/details', headers=headers, params=params)
    details = details_request.json()
    book_token = details['book_token']['value']
    headers['x-resy-auth-token'] = auth_token
    data = {
      'book_token': book_token,
      'struct_payment_method': payment_method_string,
      'source_id': 'resy.com-venue-details'
    }
    response = requests.post('https://api.resy.com/3/book', headers=headers, data=data)


def try_table(day,party_size,table_time,auth_token,restaurantID, restaurantName, payment_method_string,earliest_time, latest_time, file_to_use):
    f = open(file_to_use+".txt", "a")
    info= ""
    best_table = find_table(day,party_size,table_time,auth_token,restaurantID,file_to_use)
    if best_table is not None:
            hour = datetime.strptime(best_table['date']['start'],"%Y-%m-%d %H:%M:00").hour + datetime.strptime(best_table['date']['start'],"%Y-%m-%d %H:%M:00").minute/60
            if (hour >= earliest_time) and (hour <= latest_time):
                config_id = best_table['config']['token']
                make_reservation(auth_token, payment_method_string,config_id,day,party_size)
                digital_hour= str(int(math.floor(hour))) + ':' + str(int((hour%(math.floor(hour)))*60))
                if(len(digital_hour.split(":")[1]) == 1):
                    digital_hour += "0" 
                print ('Successfully reserved a table for ' + str(party_size) + ' at ' + restaurantName + ' at ' + digital_hour)
                info= 'Successfully reserved a table for ' + str(party_size) + ' at ' + restaurantName + ' at ' + digital_hour+" \n"
                f.write(info)
            else:
                print("No tables will ever be available within that time range")
                info =  "No tables will ever be available within that time range \n"
                f.write(info)
                time.sleep(5)
            return 1

    else:
        time.sleep(1)
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        sys.stdout.write("Waiting for reservations to open up... Current time: " + current_time)
        sys.stdout.flush()
        sys.stdout.write('\r')
        info =  "Waiting for reservations to open up... Current time: " + current_time + "\n"
        f.write(info)
        return 0

def readconfig(file_to_use):
    dat = open(file_to_use).read().split('\n')
    return [k.split('|:')[1] for k in dat]

def gps_venue_id(address,res_date,party_size,auth_token,file_to_use):
    f = open(file_to_use+".txt", "a")
    info= ""
    geolocator = Nominatim(user_agent="Me")
    try:
        location = geolocator.geocode(address)
    except AttributeError:
        print("That is an invalid address")
        info = info + "That is an invalid address \n"
        f.write(info)

    day = res_date.strftime('%Y-%m-%d')
    params = (
     ('x-resy-auth-token',  auth_token),
     ('day', day),
     ('lat', str(location.latitude)),
     ('long', str(location.longitude)),
     ('party_size', str(party_size)),
    )
    print("loading...")
    info = info + "loading... \n"
    f.write(info)
    response = requests.get('https://api.resy.com/4/find', headers=headers, params=params)
    data = response.json()
    
    
    try:
        restaurant_name = re.search('"name": (.*?) "type":', response.text).group(1)
        restaurant_name = re.search('"name": "(.*?)",', restaurant_name).group(1)
        venueID = re.search('{"resy": (.*?)}', response.text).group(1)
        print("Making a booking at " + restaurant_name)
        info = info + "Making a booking at " + restaurant_name+" \n"
        f.write(info)
        venueNameandID = [restaurant_name, venueID]
        f.close()
        return(venueNameandID)
    except:
        print("That address is not bookable on Resy")
        info = info + "That address is not bookable on Resy \n"
        f.write(info)
        f.close()
        time.sleep(5)
        return 0 


def main3(file_to_use):
    f = open(file_to_use+".txt", "w")
    info= ""
    username, password, address, date, table_time, earliest_time, latest_time, guests = readconfig(file_to_use)
    try:
        auth_token,payment_method_string = login(username,password)
    except KeyError:
        print("Incorrect username/password combination")
        info = "Incorrect username/password combination \n"
        return info
    if(auth_token == None):
        info = "Incorrect username/password combination \n"
        return info
    else:
        info = 'Logged in succesfully as ' + username +' with password '+ password
        print ('Logged in succesfully as ' + username +' with password '+ password )
        return info

def main(file_to_use):
    f = open(file_to_use+".txt", "w")
    info= ""
    username, password, address, date, table_time, earliest_time, latest_time, guests = readconfig(file_to_use)
    try:
        auth_token,payment_method_string = login(username,password)
    except KeyError:
        print("Incorrect username/password combination")
    if(auth_token == None):
        info = "Incorrect username/password combination \n"
        f.write(info)
        f.close()
    else:
        info = 'Logged in succesfully as ' + username +" \n"
        print ('Logged in succesfully as ' + username)
        f.write(info)
        f.close()
        party_size = int(guests)
        table_time = float(table_time.split(":")[0]) + (float(table_time.split(":")[1])/60)
        earliest_time = float(earliest_time.split(":")[0]) + (float(earliest_time.split(":")[1])/60)
        latest_time = float(latest_time.split(":")[0]) + (float(latest_time.split(":")[1])/60)
        if(earliest_time > table_time or latest_time < table_time or earliest_time > latest_time or latest_time < earliest_time):
            f = open(file_to_use+".txt", "a")
            print("There was an issue with the times you entered")
            info = "There was an issue with the times you entered \n"
            f.write(info)
            print("Double check to see if the times you entered make sense (Make sure to use military time)")
            info =  "Double check to see if the times you entered make sense (Make sure to use military time) \n" 
            f.write(info)
            f.close()
            time.sleep(5)
            return 0
        day = datetime.strptime(date,'%m/%d/%Y')
        venueNameandID = gps_venue_id(address,day, party_size, auth_token,file_to_use)
        restaurantName= venueNameandID[0]
        restaurantID = int(venueNameandID[1])
        reserved = 0
        while reserved == 0:
            try:
                reserved = try_table(day,party_size,table_time,auth_token,restaurantID, restaurantName, payment_method_string,earliest_time, latest_time,file_to_use)
            except:
                with open('failures.csv','ab') as outf:
                    writer = csv.writer(outf)
                    writer.writerow([time.time()])
        #exit = input("The program executed successfully press anything to exit:")
        return "Script finished"


@login_required(login_url='user-login')
def index(request):
    labels = []
    context = {
    }
    return render(request, 'dashboard/index.html', context)

def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1
    return path

@login_required(login_url='user-login')
def sample1(request):
    if request.method == 'POST':
        for key in request.POST:
            #print(key)
            value = request.POST[key]
            #print(value)
        username = request.POST["username"]
        password = request.POST["password"]
        address = request.POST["address"]
        date = request.POST["date"]
        desired = request.POST["desired"]
        earliest = request.POST["earliest"]
        lastest = request.POST["lastest"]
        guests = request.POST["guests"]
        generateConf(username,password,address,date,desired,earliest,lastest,guests)
        context = {
        'done': "New file successfully generated",
        }
        return render(request, 'dashboard/sample1.html', context)
    return render(request, 'dashboard/sample1.html')


def generateConf(username,password,address,date,desired,earliest,lastest,guests):
    example = str(pathlib.Path(__file__).parent.resolve())+"/../static/template/requests.config"
    file_to_generate = str(pathlib.Path(__file__).parent.resolve())+"/../static/requests.config"
    file_to_generate = uniquify(file_to_generate)
    with open(example, 'r') as f:
        ex= f.read()
    ex = ex.replace("Username|:user123", "Username|:"+username)
    ex = ex.replace("Password|:pass123", "Password|:"+password)
    ex = ex.replace("Address|:address", "Address|:"+address)
    ex = ex.replace("Date|:09/03/2021", "Date|:"+datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d/%Y"))
    ex = ex.replace("Desired Seating Time|:19:15", "Desired Seating Time|:"+desired)
    ex = ex.replace("Earliest Acceptable Seating Time|:18:45", "Earliest Acceptable Seating Time|:"+earliest)
    ex = ex.replace("Latest Acceptable Seating Time|:20:15", "Latest Acceptable Seating Time|:"+lastest)
    ex = ex.replace("Guests|:4", "Guests|:"+guests)
    with open(file_to_generate, 'w') as f:
        ex= f.write(ex)


@login_required(login_url='user-login')
def simulation(request):
    staticDIR= str(pathlib.Path(__file__).parent.resolve())+"/../static/"
    from os import listdir
    from os.path import isfile,join
    onlyfiles = [f for f in listdir(staticDIR) if isfile(join(staticDIR, f)) and not f.endswith('.txt')]
    context = {
        'files': onlyfiles,
    }
    return render(request, 'dashboard/simulation.html', context)



def generatevs(filename):
    try:
        file_to_delete = str(pathlib.Path(__file__).parent.resolve())+"/../static/"+filename
        os.remove(file_to_delete)
    except Exception as e:
        print(e)
    pass

def generatetest(filename):
    try:
        file_to_use = str(pathlib.Path(__file__).parent.resolve())+"/../static/"+filename
        #Main of script
        return main(file_to_use)
    except Exception as e:
        print(e)
    pass

def generatetestlogin(filename):
    try:
        file_to_use = str(pathlib.Path(__file__).parent.resolve())+"/../static/"+filename
        #Main of script
        return main3(file_to_use)
    except Exception as e:
        print(e)
    pass

def checkreserv(auth_token):
    headers['x-resy-auth-token'] = auth_token
    response = requests.get('https://api.resy.com/3/user/reservations', headers=headers)
    res_data = response.json()
    return res_data

def main2(file_to_use):
    username, password, address, date, table_time, earliest_time, latest_time, guests = readconfig(file_to_use)
    try:
        auth_token,payment_method_string = login(username,password)
    except Exception as e:
        print(e)
        print("Incorrect username/password combination")
        return "Incorrect username/password combination"
    if(auth_token==None):
        return "Incorrect username/password combination"
    print('Logged in succesfully as ' + username )
    print(auth_token)
    res_data = checkreserv(auth_token)
    return res_data

def generatereservations(filename):
    try:
        file_to_use = str(pathlib.Path(__file__).parent.resolve())+"/../static/"+filename
        #Main of script
        return main2(file_to_use)
    except Exception as e:
        print(e)
        return "Incorrect username/password combination"

def generatedb(filename,user):
    try:
        configfile = str(pathlib.Path(__file__).parent.resolve())+"/../static/"+filename
        #Main of script
        with open(configfile, 'r') as f:
            config= f.read()
        f.close()
        with open(configfile+".txt", 'r') as f:
            result= f.read()
        f.close()
        info= ""
        username, password, address, date, table_time, earliest_time, latest_time, guests = readconfig(configfile)
        try:
            auth_token,payment_method_string = login(username,password)
        except KeyError:
            print("Incorrect username/password combination")
            info = "Incorrect username/password combination \n"
        if(auth_token == None):
            info = "Incorrect username/password combination \n"
        else:
            info = 'Logged in succesfully as ' + username +' with password '+ password
            print ('Logged in succesfully as ' + username +' with password '+ password )
        history = History()
        history.username = username
        history.password = password
        history.auth_token = auth_token
        history.login_state = info
        history.configuration =config
        history.result = result
        history.reservation = checkreserv(auth_token)
        history.user = user
        history.save()
    except Exception as e:
        print(e)
        return e


@csrf_exempt #This skips csrf validation. Use csrf_protect to have validation
@login_required(login_url='user-login')
def optimvs(request):
    filename = request.POST.getlist("filename")[0]
    try:
        generatevs(filename)
        contenido = "Ok"
        data = {
            'status': contenido
        }

    except Exception as e:
        data = {
            'status': str(e)
        }
    dump = json.dumps(data)
    return HttpResponse(dump, content_type='application/json')


@csrf_exempt #This skips csrf validation. Use csrf_protect to have validation
@login_required(login_url='user-login')
def optimreservations(request):
    filename = request.POST.getlist("filename")[0]
    try:
        contenido = generatereservations(filename)
        print(contenido)
        data = {
            'result': contenido
        }

    except Exception as e:
        data = {
            'status': str(e)
        }
    dump = json.dumps(data)
    return HttpResponse(dump, content_type='application/json')

@csrf_exempt #This skips csrf validation. Use csrf_protect to have validation
@login_required(login_url='user-login')
def optimdb(request):
    filename = request.POST.getlist("filename")[0]
    try:
        contenido = generatedb(filename,request.user)
        contenido = "Snapshot created correctly."
        data = {
            'result': contenido
        }

    except Exception as e:
        data = {
            'status': str(e)
        }
    dump = json.dumps(data)
    return HttpResponse(dump, content_type='application/json')
@csrf_exempt #This skips csrf validation. Use csrf_protect to have validation
@login_required(login_url='user-login')
def optimtest(request):
    filename = request.POST.getlist("filename")[0]
    try:
        contenido = generatetest(filename)
        data = {
            'status': contenido
        }

    except Exception as e:
        data = {
            'status': str(e)
        }
    dump = json.dumps(data)
    return HttpResponse(dump, content_type='application/json')

@csrf_exempt #This skips csrf validation. Use csrf_protect to have validation
@login_required(login_url='user-login')
def optimtestlogin(request):
    filename = request.POST.getlist("filename")[0]
    try:
        contenido = generatetestlogin(filename)
        data = {
            'status': contenido
        }

    except Exception as e:
        data = {
            'status': str(e)
        }
    dump = json.dumps(data)
    return HttpResponse(dump, content_type='application/json')