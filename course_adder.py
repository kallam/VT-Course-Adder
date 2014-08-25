#!/usr/bin/python

import mechanize, base64
from bs4 import BeautifulSoup
from time import sleep

def login(username, password, addBrowser, timetableBrowser):
	try:
		login_to_hokiespa(username, password, addBrowser, timetableBrowser)

		navigate_to_timetable(timetableBrowser)
		navigate_to_dropadd(addBrowser)
		print "Successfully logged in. Beginning timetable watching."
	except:
		print "Error logging in, attempting again..."
		login(username, password, addBrowser, timetableBrowser)

def login_to_hokiespa(username, password, addBrowser, timetableBrowser):
	addBrowser.open("https://banweb.banner.vt.edu/ssb/prod/twbkwbis.P_WWWLogin")
	timetableBrowser.open("https://banweb.banner.vt.edu/ssb/prod/twbkwbis.P_WWWLogin")

	addBrowser.follow_link(text="Login to HokieSpa >>>")
	timetableBrowser.follow_link(text="Login to HokieSpa >>>")

	addBrowser.select_form(nr = 0)
	timetableBrowser.select_form(nr = 0)

	addBrowser["username"] = username
	timetableBrowser["username"] = username

	addBrowser["password"] = password
	timetableBrowser["password"] = password

	addBrowser.submit()
	timetableBrowser.submit()

def navigate_to_timetable(timetableBrowser):
	timetableBrowser.follow_link(text="Timetable of Classes")

def navigate_to_dropadd(addBrowser):
	addBrowser.follow_link(text="Hokie Spa")
	addBrowser.follow_link(text="Registration and Schedule")
	addBrowser.follow_link(text="Drop/Add", nr=0)

def is_course_open(timetableBrowser, crn):
	timetableBrowser.select_form(nr = 0)
	crnControl = timetableBrowser.find_control(name = "crn")
	crnControl.readonly = False
	crnControl._value = crn
	response = timetableBrowser.submit()
	responseText = response.get_data()
	if "Full" in responseText:
		return False
	else:
		return True

def add_course(addBrowser, crn):
	addBrowser.select_form(nr = 1)
	crnControl = addBrowser.find_control(id = "crn_id1")
	crnControl.readonly = False
	crnControl._value = crn
	response = addBrowser.submit()
	responseText = response.get_data()

	if "Registration Errors" in responseText:
		# Unsuccessfully added.
		print "CRN:", crn, "unsuccessfully added. Trying again in 30 seconds."
		return False
	else:
		# Successfully added.
		print "CRN:", crn, "successfully added. Removing from the list."
		return True

def is_valid_class(crn, timetableBrowser):
	timetableBrowser.select_form(nr = 0)
	crnControl = timetableBrowser.find_control(name = "crn")
	crnControl.readonly = False
	crnControl._value = crn
	response = timetableBrowser.submit()
	responseText = response.get_data()
	if "NO SECTIONS FOUND FOR THIS INQUIRY." in responseText:
		return False
	else:
		return True

def filter_invalid_crns(classes, timetableBrowser):
	# Removes any elements from the list if the length is not 5.
	classes[:] = [crn for crn in classes if len(str(crn)) == 5 and is_valid_class(crn, timetableBrowser)]

def main():
	# Browser for course adding
	addBrowser = mechanize.Browser()
	addBrowser.set_handle_robots(False)
	# Browser for checking the timetable for empty seat
	timetableBrowser = mechanize.Browser()
	timetableBrowser.set_handle_robots(False)

	username = raw_input("Enter your username: ")
	password = raw_input("Enter your password: ")
	
	classesToAdd = raw_input("Enter CRN's that you wish to add separated by spaces: ")
	classesToAdd = map(int, classesToAdd.split())

	login(username, password, addBrowser, timetableBrowser)

	# Eliminates CRN's not of length 5 and that are do not have a class
	# associated with them.
	filter_invalid_crns(classesToAdd, timetableBrowser)

	# Runs the script until all classes are successfully added.
	while len(classesToAdd) > 0:
		openClasses = [crn for crn in classesToAdd if is_course_open(timetableBrowser, crn)]

		for crn in openClasses:
			if add_course(addBrowser, crn):
				classesToAdd.remove(crn)

		sleep(30)

	print "All courses added."

if __name__ == "__main__": main()