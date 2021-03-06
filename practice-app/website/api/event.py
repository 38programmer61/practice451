from flask import Blueprint, json, request,  url_for, jsonify, make_response, abort, flash
from sqlalchemy.sql.elements import Null
from ..models import Event, DiscussionPost, Sport, User
from re import template

from .. import db
import json
import sqlite3
import requests
import re
from ..views import get_sport_names
from flasgger.utils import swag_from
from sqlalchemy import exc
from sqlalchemy.sql.elements import Null
import re
from ..settings import *

events = Blueprint('events', __name__)

def get_weather(latitude, longitude):
    """
    Get weather description using OpenWeather API.

    parameters:
        latitude : "latitude of the location"
        longitude : "longitude 
    return:
        The weather description and the weather icon id
    """
   
    # GET request to the uri using API_KEY2
    parameters = {'lat': latitude, 'lon' : longitude, 'appid': API_KEY2 }
    uri = 'https://api.openweathermap.org/data/2.5/weather'
    r = requests.get(uri, params=parameters)
    r = r.json()
    # return the weather description and the weather icon id
    return r["weather"][0]["description"], r["weather"][0]["icon"]

"""
    Get coordinates using Google Maps API

    parameters:
        address: "address of the location" 
    return:
        True if valid False otherwise
"""
def get_coordinates(address):


    # Make GET request to the uri using API_KEY
    parameters = {'key': API_KEY , 'address': address}
    uri = 'https://maps.googleapis.com/maps/api/geocode/json'

    r = requests.get(uri, params=parameters)

    result = r.json()

    # If there is no error return information from response.
    if r.status_code == 200:
        if result['status'] == "OK":
            formatted_address = result['results'][0]['formatted_address']
            longitude = result['results'][0]['geometry']['location']['lng']
            latitude = result['results'][0]['geometry']['location']['lat']
            return formatted_address, longitude, latitude, "OK"

    
    # Address not valid, error messages from API docs
    if result['status'] == "ZERO_RESULTS" or result['status'] == "INVALID_REQUEST": 
        return "",0,0,"Address Not Valid"
    # Cannot make a request
    elif result['status'] == "OVER_DAILY_LIMIT" or result['status'] == "OVER_QUERY_LIMIT" or result['status'] == "REQUEST_DENIED" or result['status'] == "UNKNOWN_ERROR": 
        return "",0,0,"Try Later"
    # Remaining Errors
    else:
        return "",0,0,"Try Later"

def check_event_id(new_event):
    """
    Check if the given event id is valid
    parameters:
        new_event: Event 
    return:
        True if valid false otherwise
    """
    event = new_event.serialize()
    id = event["id"]
    if(id <= 0):
        return False
    return True

def check_weather_icon(weather_icon_id):
    """
    Check the validity of a given weather icon id
    parameters:
        weather_icon_id: String 
    return:
        True if valid false otherwise
    """
    # create the corresponding regex
    weather_icon_id_regex = "[0-9][0-9][dn]"
    if not re.match(weather_icon_id_regex, weather_icon_id):
        return False
    return True

#helper method for querying
def query_handler_events(name, sport, date_from, date_to):
    query = 'SELECT * FROM Event WHERE'
    filters = []
    # adds filter for name
    if name:
        filters.append(' name LIKE \'%' + name + '%\' AND')
    # adds filter for sport name
    if sport:
        filters.append(' sport = ' + str(sport) + ' AND')
    # adds filter for initial date
    if date_from:
        filters.append(' date >= \'' + date_from + '\' AND')
    # adds filter for final date
    if date_to:
        filters.append(' date <= \'' + date_to + '\' AND')

    # checks if there is any filter added
    if filters:
        for filt in filters:
            query += filt
        query = query[:-4] + ';'
    else:
        query = query[:-6] + ';'
    return query

"""
    Check the validity of the sport field of event
    parameters:
        new_event: Event 
    return:
        True if valid False otherwise
"""
def check_event_sport(new_event):
    try:
        # sport Ids between 102-120
        if int(new_event.sport) < 102 or int(new_event.sport) > 120:
            return False
        return True
    except:
        # sport string cannot be changed to integer
        return False

"""
    Check the format of the date field of event
    Format should match YYYY-MM-DDTHH:MM
    parameters:
        new_event: Event 
    return:
        True if valid False otherwise
"""
def check_event_date(new_event):
    # Date format YYYY-MM-DDTHH:MM
    date_regex = "^(20[0-9][0-9])-(0[1-9]|1[0-2])-(0[1-9]|1[0-9]|2[0-9]|3[0-1])T(0[0-9]|1[0-9]|2[0-3]):(0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])$"
    if not re.match(date_regex, new_event.date):
        return False
    return True


@events.route('/', methods=['GET', 'POST'])
@swag_from('doc/events_POST.yml', methods=['POST'])
@swag_from('doc/events_GET.yml', methods=['GET'])
def event():

    # handles get request
    if request.method == 'GET':
        # fethes body parameters
        query_parameters = request.args
        name = query_parameters.get('name')
        sport = query_parameters.get('sport')
        date_from = query_parameters.get('date_from')
        date_to = query_parameters.get('date_to')

        # sets up querys
        query = query_handler_events(name, sport, date_from, date_to)

        # executes query and converts to json format
        eventList = db.engine.execute(query)
        eventList = json.dumps([dict(event_item) for event_item in eventList])

        # temporary parameter for adding additional info into result
        temp = json.loads(eventList)

        # external api for assigning random names for event creators
        multi = requests.get('https://randomuser.me/api/?inc=name&results=' + str(len(temp))).json()['results']
        
        # adds external info into the result
        for index, item in enumerate(temp):
            name = multi[index]['name']
            item['creator_name'] = name['first'] + ' ' + name['last']
        
        # returns the result in json format
        return jsonify(temp)
        

    if request.method == 'POST':

        """
            Used to create a new event.
            Endpoint description:
                ./api/v.10/events
                'POST':
                    JSON Request Body Format : {
                                                name = "Name of the event, title." required,
                                                creator_user = "Id of the user creating the event. Id must be registered to a user." required,
                                                location = "Address of the event, given using basic English." required,
                                                sport = "Id of the sport. Between 102-120." required,
                                                date ="Date of the event. Format is "YYYY-MM-DDTHH:MM" required
                                            }
                    Response Example : {
                                            "creator_user": 1,
                                            "date": "10.12.2021",
                                            "entered_address": "Trabzon",
                                            "formatted_address": "Trabzon, Ortahisar/Trabzon, Turkey",
                                            "id": 2,
                                            "latitude": 41.0026969,
                                            "longitude": 39.7167633,
                                            "name": "abc",
                                            "sport": 103
                                        }
                    Status Codes:
                        201: "Event created and added to database."
                        400: "Body parameters are not correct."
                        503:  "There is an error, try later."


        """

        # All parameters must be present.
        if not request.json or not 'name' in request.json or not 'creator_user'  in request.json or not 'location' in request.json or not 'sport' in request.json or not 'date' in request.json:
            return jsonify({"error":"Parameters not correct"}), 400

        # Get coordinates using Google Maps API.
        formatted_address, longitude, latitude, error = get_coordinates(request.json['location'])

        # Return error if fetch was not correct.
        if error != "OK":
            if error != "Try Later":
                return jsonify({"error": error}), 400
            else:
                return jsonify({"error": "Service Unavailable"}), 503

        # Create database model
        new_event = Event(
            name = request.json['name'],
            date = request.json['date'],
            formatted_address = formatted_address,
            entered_address = request.json['location'],
            longitude = longitude,
            latitude = latitude,
            creator_user = request.json['creator_user'],
            sport = request.json['sport']
        )

        # Check if creator_user is valid and there is a user registered with that id.
        user = User.query.get(request.json['creator_user'])
        if not user:
            return jsonify({"error":"User Not Registered"}), 400

        # Check sport id.
        if not check_event_sport(new_event):
            return jsonify({"error":"Sport Id Is Not Correct"}), 400

        # Check date format.
        if not check_event_date(new_event):
            return jsonify({"error":"Date Format Not Correct"}), 400


        try:
            # Add Event to database.
            db.session.add(new_event)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            # In case of error, return error message
            db.session.rollback()

            return jsonify({"error": "Service Unavailable"}), 503
        
        # No error, return new event information
        return jsonify(new_event.serialize()), 201

        
@events.route('/<event_id>/', methods = ['GET'])
@swag_from('doc/event_GET.yml', methods=['GET'])
def get_event_by_id(event_id):
    """
            Used to get the event with the corresponding ID
            event_id is a path parameter and it is required
            Endpoint description:
                ./api/v1.0/events/<event_id>
                'GET':                 
                    Response Example : {
                                            "event_id": 24,
                                            "id": 24,
                                            "name": "Basketball Match at 9",
                                            "date": "2021-06-16",
                                            "formatted_address": "Artvin, Merkez/Artvin, Turkey",   
                                            "entered_address": "Artvin",
                                            "longitude": 41.87645,                                      
                                            "latitude": 43.54367,
                                            "creator_user" : 5748
                                            "sport": "Basketball"                                     
                                            "hour" : "09:00"
                                            "weather" : "scattered clouds"
                                            "weatcher_icon" : "03d"
                                        }
                    Status Codes:
                        200: "Event has been fetched."
                        400: "Event ID is not correct."                       

        """

    if request.method == 'GET':
        event = Event.query.get(event_id)  
       
        # if there exists no such event return error.
        if(event is None):         
            return jsonify({"error":"Event ID is not correct"}), 400
        # if event id is not valid return error
        elif(not check_event_id(event)):
            return jsonify({"error":"Event ID is not correct"}), 400          
        
        else:    
            event_with_weather = event.serialize()
            event_with_weather['event_id'] = event_id
            # Split the hour and the date.
            event_with_weather["hour"] =  event_with_weather["date"][11:]
            event_with_weather["date"] = event_with_weather["date"][:10]     
            #get the weather and the weather_icon, sending request to OpenWeather API
            weather, weather_icon = get_weather(event_with_weather["latitude"], event_with_weather["longitude"])
            event_with_weather["weather"] = weather
            #check if weather_icon is valid.
            if(check_weather_icon(weather_icon)):
                event_with_weather["weather_icon"] = weather_icon
            sport_names = get_sport_names()    
            # Change the sport id to the corresponding sport name
            event_with_weather["sport"] = sport_names[event_with_weather["sport"]]                
            return jsonify(event_with_weather), 200


# checks whether an entered comment has text
def check_comment_has_text(message):
    if len(message) < 1:
        return False
    else:
        return True

      
"""
This method handles all requests for adding a discussion post and getting all
discussion posts in order to show those in the event's discussion page.
"""
# When the id of the event given, corresponding discussion is returned by adding the definition of the sport type in the json format
# Corresponding event must exist and have a sport type in db.
@events.route('<event_id>/discussions', methods=['GET', 'POST'])
@swag_from('doc/discussionForEvent_GET.yml', methods=['GET'])
@swag_from('doc/discussionForEvent_POST.yml', methods=['POST'])
def discussionForEvent(event_id):

    if request.method == 'GET':

        if int(event_id) <=-1:
            return "Wrong path parameters", 401
        try:
            eventList = Event.query.all()
        except exc.NoReferenceError as e:
            return "Database error", 400
        eventList = Event.query.all()


        sportName = ''

        # Finds the event with the given id and its sport type
        for i in range(len(eventList)):
            if eventList[i].serialize()["id"] == int(event_id):
                sportName = eventList[i].serialize()["sport"]


        # ############# New

        sportList = Sport.query.all()

        for i in range(len(sportList)):
            if sportList[i].serialize()["id"] == int(sportName):
                sportName = sportList[i].serialize()["sport"]
                break

  
        ############# New

        description = 'No definition found for ' + sportName

        # Find the corresponding definition for the sport type
        response = requests.get(
            'https://sports.api.decathlon.com/sports/' + sportName.lower())  # API to use
        if response.status_code >= 200 and response.status_code < 300:
            json_data = json.loads(response.text)
            description = json_data['data']['attributes']['description']
            if description == None:
                description = 'No definition found for ' + sportName

        try:
            discussionPostList = DiscussionPost.query.all()
        except exc.NoReferenceError as e:
            return "Database error", 400

        discussionPostList = DiscussionPost.query.all()
        # Get the discussion from the database for the given event
        text = 'No discussion found'

        for i in range(len(discussionPostList)):
            if discussionPostList[i].serialize()["id"] == int(event_id):
                text = discussionPostList[i].serialize()["text"]

        result = {"id": event_id, "description": description, "text": text}
        return jsonify(result), 201
        

    elif request.method == 'POST': # if the user wants to post a comment to a discussion

        # event_id is wrong        
        if int(event_id) < 0:
            return jsonify({"error":"Wrong Parameters"}), 400

        # users shall not be able to enter a comment to a nonexistent event
        event = Event.query.get(int(event_id))
        if not event:
            return jsonify({"error":"Event Does Not Exist"}), 400
        
        # get a random name 
        response = requests.get(
                'https://api.namefake.com/english-united-states/random/')

        # if the GET request sent is successful, use the name returned        
        if response.status_code >= 200 and response.status_code < 300:
            data = json.loads(response.content)
            name_shown = data['name']

        else: # if cannot get the name for some reason, show the user's name as "No Name"
            name_shown = "No Name"


        message = request.json['text']
        test = check_comment_has_text(message)
        
        # if the text field is empty, this request is erroneous        
        if not test: 
            return jsonify({"error":"Text Field Cannot Be Empty"}), 400

        message = name_shown + ': ' + message # combine the comment with the name

        discussionPostList = DiscussionPost.query.all()

        doesExist = False
        for i in range(len(discussionPostList)):
            if discussionPostList[i].serialize()["id"] == int(event_id):
                # check if there exists a discussion page for that event_id
                doesExist = True
                break

        # if there is not a discussion page for this event, create one                
        if not doesExist:
            newPost = DiscussionPost(id=event_id, text=message)
            try:
                db.session.add(newPost)
                db.session.commit()
                return jsonify(newPost.serialize()), 201
            except exc.SQLAlchemyError as e:
                 db.session.rollback()
                 return jsonify({"error":"Service Unavailable"}), 503

        # if there is already a discussion page for this event, update it            
        else:
            try:
                currentRow = DiscussionPost.query.filter_by(id=event_id).first()
                # different comments under the same discussion page are separated by sharp as we agreed on                
                currentRow.text += '#' + message
                db.session.commit()
                return jsonify(currentRow.serialize()), 201
            except exc.SQLAlchemyError as e:
                db.session.rollback()
                return jsonify({"error":"Service Unavailable"}), 503
