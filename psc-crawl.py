import requests
import string
import time
import os
import json
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch, helpers

POST_URL = 'https://directory.psc.gov/hhsdir/eeQ.asp'
POST_URL_BASE = 'https://directory.psc.gov/hhsdir/'
INDEX_NAME = 'hhs-employees'

agency_list = ['ACF', 'ACL', 'AHRQ', 'AOA', 'ATSDR', 'CDC', 'CMS', 'FDA', 'HRSA', 'IHS', 'NIH', 'OIG', 'OS', 'PSC', 'SAMHSA' ]

class Person:
    def __init__(self, last_name, middle_name, first_name, organization, job_title, agency, room=None, duty_station=None, mail_stop=None, phone=None, email=None):
        self.last_name = last_name
        self.middle_name = middle_name
        self.first_name = first_name
        self.organization = organization
        self.job_title = job_title
        self.agency = agency
        self.room = room
        self.duty_station = duty_station
        self.mail_stop = mail_stop
        self.phone = phone
        self.email = email

def get_employee_details(employee_key, person:Person):
    REQUEST_GET_URL = POST_URL_BASE + employee_key
    try:
        response = requests.get(REQUEST_GET_URL)
        if(response.status_code == 200):
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Some employee details page are not found when clicking from search result
            result_exists = soup.findAll(text='Last name')
            if len(result_exists) > 0:
                
                try:
                    room_row = soup.findChildren('td', text='Room')[0].parent
                    room = room_row.findChildren('td')[1].text
                    person.room = room
                except IndexError:
                    pass

                try:
                    duty_station_row = soup.findChildren('td', text='Duty station')[0].parent
                    duty_station = duty_station_row.findChildren('td')[1].text
                    person.duty_station = duty_station
                except IndexError:
                    pass

                try:
                    mail_stop_row = soup.findChildren('td', text='Mail stop')[0].parent
                    mail_stop = mail_stop_row.findChildren('td')[1].text
                    person.mail_stop = mail_stop
                except IndexError:
                    pass

                try:
                    phone_row = soup.findChildren('td', text='Phone')[0].parent
                    phone = phone_row.findChildren('td')[1].text
                    person.phone = phone
                except IndexError:
                    pass

                try:
                    email_row = soup.findChildren('td', text='Internet e-mail')[0].parent
                    email = email_row.findChildren('td')[1].text
                    person.email = email
                except IndexError:
                    pass

            return person

    except Exception:
        print(person)
        print(Exception)
        return person

 
def write_to_elasticsearch(person_list):
    es = Elasticsearch(cloud_id=os.environ['CLOUD_ID'],api_key=os.environ['CLOUD_API_KEY'])
    result = es.ping()
    print(result)
    if result:
        print("Connected to Elasticsearch")
        try:
            resp = helpers.bulk(es, person_list, index=INDEX_NAME)
            print ("helpers.bulk() RESPONSE:", resp)
            print ("helpers.bulk() RESPONSE:", json.dumps(resp, indent=4))
        except helpers.BulkIndexError as bulkIndexError:
            print("Indexing error: {0}".format(bulkIndexError))
    else:
        print("Not connected")


def scrape_search_result(POST_URL, form_data, Person, person_list, agency):
    response = requests.post(POST_URL, data=form_data)

    if(response.status_code == 200):
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.findChildren('table', {'cellpadding':'4'})
        if len(tables) > 0:
            result_table = tables[0]

            # Check if max result limit reached
            max_limit_reached = soup.find_all(text="maximum")
            max_bool = len(max_limit_reached)
            print("Max limit reached: " + str(max_bool))

            if max_bool > 0:
                # Iterate over first names
                for letter in alphabet:
                    form_data['FirstNameOp']='begins with'
                    form_data['FirstName']=letter
                    print('First name iteration: ' + letter)
                    scrape_search_result(POST_URL, form_data, Person, person_list, agency)
                pass

            else:
                rows = result_table.findChildren(['tr'])

                for row in rows:
                    cells = row.findChildren('td')

                    last_name = cells[0].text
                    first_name = cells[1].text
                    middle_name = cells[2].text
                    organization = cells[3].text
                    job_title = cells[4].text

                    person = Person(last_name, middle_name, first_name, organization, job_title, agency)

                    # Get Employee Details
                    link = cells[0].find('a')
                    employee_key = link['href']
                    updated_person = get_employee_details(employee_key, person)

                    person_list.append(updated_person.__dict__)

        else:
            print('Response code: ' + str(response.status_code))

    return person_list

# Iterate by letter of Last Name for each Agency
alphabet = list(string.ascii_lowercase)

def get_employee_by_agency(agency):
    person_list = []

    for letter in alphabet:
        print(letter)
        current_count = len(person_list)
        form_data = {'LastNameOp': 'begins with', 'LastName': letter, 'AgencyOp':'equal to', 'Agency': agency, 'maxRows': 500}
        person_list = scrape_search_result(POST_URL, form_data, Person, person_list, agency)
        updated_count = len(person_list)
        delta = updated_count - current_count
        print('Person count to add: ' + str(delta))

    write_to_elasticsearch(person_list)

    return person_list
    
person_list = get_employee_by_agency(agency_list[12])        
print('Final total: ' + str(len(person_list)))


