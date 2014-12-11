#!/usr/bin/python

import mechanize, base64, getpass, sys, getopt
from bs4 import BeautifulSoup
from time import sleep

# Change this value for future sessions.
termYear = "201501"

# This value must be modified to match the number of the Drop/Add 
# link you wish to follow (0-indexed). For example, if you wish to 
# open the first drop-add link, you should set the value to 0, second
# to 1, etc.
numberOfDropAddLinkToFollow = 2

def login(username, password, addBrowser, timetableBrowser):
    try:
        login_to_hokiespa(username, password, addBrowser)
        login_to_hokiespa(username, password, timetableBrowser)

        navigate_to_timetable(timetableBrowser)
        navigate_to_dropadd(addBrowser)
        print "Successfully logged in. Beginning timetable watching."
    except mechanize._mechanize.LinkNotFoundError:
        sys.exit("Link not found. Please change the termYear and \
numberOfDropAddLinkToFollow variables to valid values.")
    except:
        print "Error logging in, attempting again..."
        sleep(5)
        login(username, password, addBrowser, timetableBrowser)

def login_to_hokiespa(username, password, browser):
    browser.open("https://banweb.banner.vt.edu/ssb/prod/twbkwbis.P_WWWLogin")

    browser.follow_link(text="Login to HokieSpa >>>")

    browser.select_form(nr = 0)

    browser["username"] = username

    browser["password"] = password

    browser.submit()

def navigate_to_timetable(timetableBrowser):
    timetableBrowser.follow_link(text="Timetable of Classes")

def navigate_to_dropadd(addBrowser):
    addBrowser.follow_link(text="Hokie Spa")
    addBrowser.follow_link(text="Registration and Schedule")

    # IMPORTANT: Depending on whether Drop/Add is open/not open for Winter/Summer sessions,
    # the "nr" paramter below must be modified accordingly.
    addBrowser.follow_link(text="Drop/Add", nr=numberOfDropAddLinkToFollow)

def is_course_open(timetableBrowser, crn):

    timetableBrowser.select_form(nr = 0)

    termYearControl = timetableBrowser.find_control(name = "TERMYEAR")
    termYearControl.readonly = False
    termYearControl.value = [termYear]

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
        # print responseText
        return False
    else:
        # Successfully added.
        print "CRN:", crn, "successfully added. Removing from the list."
        return True

def is_valid_class(crn, timetableBrowser):
    timetableBrowser.select_form(nr = 0)

    termYearControl = timetableBrowser.find_control(name = "TERMYEAR")
    termYearControl.readonly = False
    termYearControl.value = [termYear]

    crnControl = timetableBrowser.find_control(name = "crn")
    crnControl.readonly = False
    crnControl._value = crn
    response = timetableBrowser.submit()
    responseText = response.get_data()
    if "NO SECTIONS FOUND FOR THIS INQUIRY." in responseText:
        print 'CRN:', crn, 'is invalid. Removing.'
        return False
    else:
        return True

def filter_invalid_crns(classes, timetableBrowser):
    # Removes any elements from the list if the length is not 5.
    # classes[:] = [crn for crn in classes if len(str(crn)) == 5 and is_valid_class(crn, timetableBrowser)]
    for crngroup in classes:
        for crn in crngroup:
            if len(str(crn)) != 5 or not is_valid_class(crn, timetableBrowser):
                print "crn", crn, "is invalid so it has been removed"
                crngroup.remove(crn)

def main():
    # Browser for course adding
    addBrowser = mechanize.Browser()
    addBrowser.set_handle_robots(False)
    addBrowser.set_handle_refresh(False)
    # Browser for checking the timetable for empty seat
    timetableBrowser = mechanize.Browser()
    timetableBrowser.set_handle_robots(False)
    timetableBrowser.set_handle_refresh(False)

    fname = None
    try:                                
        opts, args = getopt.getopt(sys.argv[1:], "f:")
        if len(opts) > 0:
            temp, fname = opts[0]
    except getopt.GetoptError:
        print "Use -f to specify a file to use for crns"
        sys.exit(2)


    username = raw_input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    f = None
    classesToAdd = []
    if fname is not None:
        try:
            f = open(fname)
            sections = f.readline()
            while sections != '':
                crns = sections.split(" ")
                for index, crn in enumerate(crns):
                    if crn == "#":
                        crns = crns[:index]
                if crns != []:
                    classesToAdd.append(map(int, crns))

                sections = f.readline()
            print "Using CRNs from {0}: {1}".format(fname, classesToAdd)
            f.close()
        except Exception, e:
            print "Error reading input file"
            sys.exit(2)

    else:
        crns = raw_input("Enter CRN's that you wish to add separated by spaces: ").split(" ")
        for crn in crns:
            classesToAdd.append([int(crn)])


    login(username, password, addBrowser, timetableBrowser)

    # Eliminates CRN's not of length 5 and that are do not have a class
    # associated with them.
    filter_invalid_crns(classesToAdd, timetableBrowser)

    # Runs the script until all classes are successfully added.
    while len(classesToAdd[0]) > 0:
        openClasses = []
        for crngroup in classesToAdd:
            for crn in crngroup:
                if is_course_open(timetableBrowser, crn):
                    openClasses.append(crn)
        # Create a set of all currently open classes from the classesToAdd list.
        # openClasses = set([crn for crn in classesToAdd if is_course_open(timetableBrowser, crn)])

        # List comprehension to filter any successfully added CRNs from classesToAdd.
        # print openClasses
        for crn in openClasses:
            if crn in crngroup and add_course(addBrowser, crn):
                classesToAdd.remove(crngroup)

        # Sleeps for 30 seconds before attempting to add courses again.
        sleep(30)

    print "All courses added."

if __name__ == "__main__": main()