# Web Scraping Example - ASP Form
This is an example of scraping a website that contains a form. In this case, it is an employee directory for Health and Human Services (https://directory.psc.gov/employee.htm).

<img width="568" alt="image" src="https://user-images.githubusercontent.com/100947826/210420521-928ac844-6409-45c5-a2f7-8d2a6f65ff46.png">

## Approach
Since we need to interact with a form to retrieve the desired data, we can't crawl this like a typical website using something like the [Elastic web crawler](https://www.elastic.co/training/app-search-web-crawler-quick-start?utm_campaign=web-crawler-sitelink&utm_content=&utm_source=adwords-s&utm_medium=paid&device=c&utm_term=elastic%20web%20crawler&gclid=CjwKCAiAwc-dBhA7EiwAxPRylIV5uDbrzYgBeFIN_vof85iPj1NxalQg0fHGOsa6FECT5a3yOdVkWxoCxSQQAvD_BwE). So what we'll do is tackle this with some Python scripting to plug in different form values and then a library called BeautifulSoup which can parse the HTML page results.

### Initial Algorithm
You'll notice that this search has a limit of 500 results per page, so in the first iteration of the algorithm I looped through all the last names from A-Z for each different Agency.

```
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
```
From the search results returned, the scraper makes a separate request to retrieve details for the employee.

<img width="680" alt="image" src="https://user-images.githubusercontent.com/100947826/210425760-acf5f171-9574-450d-b549-eceef4663e41.png">

<img width="500" alt="image" src="https://user-images.githubusercontent.com/100947826/210425817-273a2ad5-e1c1-4e41-8442-a76ebb056c19.png">

Turns out that some of these agencies have more than 500 results returned when using the Last Name and Agency as a critiera. So an update was needed for this approach to make sure we didn't miss out on records.

### Updated Algorithm
To get around that, I added a check for when the max result limit is read for a particular Last Name, it would then iterate the search criteria across the First Name field from A-Z. Fortunately, that was enough to ensure that the results stayed below 500 so we could get all the records. 

```
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
```
# How to Run
1 - Create an Elastic deployment. I used Elastic Cloud to get going quickly (https://www.elastic.co/cloud/).
2 - Get the [Elastic Cloud ID](https://www.elastic.co/guide/en/cloud/current/ec-cloud-id.html)
3 - [Create an API Key](https://www.elastic.co/guide/en/kibana/master/api-keys.html)
4 - Create a Python virtual environment
```
$ python3 -m venv env
```
5 - Install the Python libraries in *requirements.txt* within the virtual environment
```
$ pip install -r requirements.txt
```
6 - Set environment variables in terminal so the script can get the Cloud ID and API Key
```
export CLOUD_ID=<CLOUD_ID>
export CLOUD_API_KEY=<CLOUD_API_KEY>
```

# Suggestions/Improvements
Feel free to make suggestions or improvements, always love to learn better ways and surely there is room for optimization.

