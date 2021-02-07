import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

API_KEY = "taOdLay8TiXO"
PROJECT_TOKEN = "tFCnXzZpA6fo"
RUN_TOKEN = "tTTz56HSi1ck"


class Data:
	def __init__(self, api_key, project_token):
		self.api_key = api_key
		self.project_token = project_token
		self.params = {
			"api_key": self.api_key
		}
		self.data = self.get_data()

	def get_data(self):  #calls the request from api and returns the data.
		response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
		data = json.loads(response.text)  #converts json string into python dict(of the data)
		return data

	def get_total_cases(self):  #we get a dict of data, in that the total has the value that has list of all total cases overall.
		data = self.data['total']

		for content in data:
			if content['name'] == "Coronavirus Cases:":  #return value of corona cases if the value of name key is this.
				return content['value']

	def get_total_deaths(self):  #overall deaths
		data = self.data['total']

		for content in data:
			if content['name'] == "Deaths:":
				return content['value']

		return "0"  #if we ask for nothing

	def get_country_data(self, country):   #all data of a country
		data = self.data["country"]

		for content in data:
			if content['name'].lower() == country.lower():
				return content

		return "0" 

	def get_list_of_countries(self):  #if user uses 'countries' in his words, it,s gonna return the list of countries.
		countries = []
		for country in self.data['country']:
			countries.append(country['name'].lower())

		return countries

	def update_data(self):  #suppose we run this after sometime, we need it to auto update so that the most recent data is given.
		response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params) #post for update, initializes a new run from parse.

		def poll():
			time.sleep(0.1)  #when a thread is working to get updated data, it will not interfere with the thread that hears the voice, so no time is wasted
			old_data = self.data
			while True:
				new_data = self.get_data()
				if new_data != old_data:   #if updated data is different
					self.data = new_data
					print("Data updated")
					break
				time.sleep(5)  #every 5 secs i'll ping the request link(get_data), after 5 seconds it will update again.


		t = threading.Thread(target=poll) #if we didnt use thread, it would take a minute to give us the updated response.
		t.start()


def speak(text):  #takes some text
	engine = pyttsx3.init()  #initialize the engine
	engine.say(text)  #we say and it recognizes
	engine.runAndWait()  #runs


def get_audio():
	r = sr.Recognizer()  #speech recognize
	with sr.Microphone() as source:
		audio = r.listen(source)  #listen for audio
		said = ""  #store audio here

		try:
			said = r.recognize_google(audio)  #assistant type
		except Exception as e:
			print("Exception:", str(e))  #return exception if nothing said

	return said.lower()  #returns the audio said in text


def main():
	print("Started Program")  #when the program starts
	data = Data(API_KEY, PROJECT_TOKEN)
	END_PHRASE = "stop"    #if it hears stop, it stops listening
	country_list = data.get_list_of_countries()

	TOTAL_PATTERNS = {     #setting search patterns
					re.compile("[\w\s]+ total [\w\s]+ cases"):data.get_total_cases,  #calls the function when we say for ex. total no. of cases.
					re.compile("[\w\s]+ total cases"): data.get_total_cases,  #[\w\s] = something said
                    re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
                    re.compile("[\w\s]+ total deaths"): data.get_total_deaths   #keyword total is used for overall only, not country specific
					}

	COUNTRY_PATTERNS = {   #detects country name pattern
					re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
                    re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths'],
					}

	UPDATE_COMMAND = "update"  #when we say 'update', it will update

	while True:
		print("Listening...")
		text = get_audio()  #gets audio
		print(text)
		result = None

		for pattern, func in COUNTRY_PATTERNS.items():  #looping through the patterns to search for country
			if pattern.match(text):
				words = set(text.split(" "))  #for finding the country name in the spoken words
				for country in country_list:
					if country in words:  #if country name recognised
						result = func(country)
						break

		for pattern, func in TOTAL_PATTERNS.items():   #looping through the patterns to search for country
			if pattern.match(text):
				result = func()
				break

		if text == UPDATE_COMMAND:
			result = "Data is being updated. This may take a moment!"
			data.update_data()

		if result:  #if result is found, speak it out
			speak(result)

		if text.find(END_PHRASE) != -1:  # stop loop
			print("Exit")
			break

main()
