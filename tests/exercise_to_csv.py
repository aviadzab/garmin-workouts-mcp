import json
import requests

# Opening JSON file from the provided link
file_link = "https://connect.garmin.com/web-data/exercises/Exercises.json"
response = requests.get(file_link)
if response.status_code != 200:
    raise Exception(f"Failed to fetch JSON from {file_link}, status code: {response.status_code}")

data = response.json()

# Derive the name from the link (e.g., 'Exercises' from 'Exercises.json')
base_name = file_link.split('/')[-1].split('.')[0]

# Create output CSV file
csv_filename = f"{base_name}.csv"
mf = open(csv_filename, "a")

# write headers row
mf.write("NAME_GARMIN"+";"+"CATEGORY_GARMIN"+";"+"Name"+";"+"Detailed"+";"+"Body parts"+";"+"Difficulty"+";"+"Equipment"+";"+"Focus"+";"+"Description"+";"+"Image1"+";"+"Image2"+";"+"URL"+";"+"\n")

# Iterating through the json list 
for category in data['categories']:
    for exercise in data['categories'][category]['exercises']:
        # set default values (when there is no detail for exercise)
        NAME_GARMIN = exercise
        CATEGORY_GARMIN = category
        Name = exercise.replace('_',' ').title()
        Detailed = "0"
        Body_parts = ""
        Difficulty = ""
        Equipment = ""
        Focus = ""
        Description = ""
        Image1 = ""
        Image2 = ""
        URL = ""

        # URL based on known path and exercise name
        URLjson = 'https://connect.garmin.com/web-data/exercises/en-US/' + category+"/"+exercise + '.json'
        page = requests.get(URLjson)

        # if page exists (200), then there are details for the exercise
        if page.status_code == 200:
            exdata = json.loads(page.text)
            Detailed = "1"
            Body_parts = exdata.get('bodyParts', "")
            Difficulty = exdata.get('difficulty', "")
            Equipment = exdata.get('equipment', "")
            Focus = exdata.get('focuses', "")
            Description = exdata.get('description', "")
            # try if there are images available (I try just 2, but when there are, there are usually more)
            try:
                Image1 = exdata['videos'][0]['thumbnail']
            except:
                Image1 = ""
            try:
                Image2 = exdata['videos'][1]['thumbnail']
            except:
                Image2 = ""
            URL = "https://connect.garmin.com/modern/exercises/"+category+"/"+exercise

        # print the name of exercise (to see what's happening while the script is running)
        print(exercise)

        # write the row data with exercise
        mf.write(NAME_GARMIN+";"+CATEGORY_GARMIN+";"+Name+";"+Detailed+";"+str(Body_parts)+";"+str(Difficulty)+";"+str(Equipment)+";"+str(Focus)+";"+str(Description)+";"+str(Image1)+";"+str(Image2)+";"+str(URL)+";"+"\n")

# close output file
mf.close()