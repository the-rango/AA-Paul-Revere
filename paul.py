#############################################
# Paul does two things:
# 1. Gets the watchlist from db
# 2. Sends out notifications if needed
#
# In between the two, Paul sends his doggo
# to go check if the courses on the watchlist
# are open, during which time, Paul may
# check the db again and send notifications

import pymongo
import urllib.parse
import requests
import bs4 as bs
import sendgrid
import config
import urllib
from sendgrid.helpers.mail import *
import boto3
import json
from bson.regex import Regex
import time
import pickle
from collections import defaultdict

########## Change Term ##########
TERM = '2019-92'
WEBSOC = 'https://www.reg.uci.edu/perl/WebSoc?'
BATCH_SIZE = 8 # Any larger, the field gets cut off and doesn't search for the ones that are cut off

aws = boto3.client(
	"sns",
	aws_access_key_id=config.AWS_ACCESSKEYID,
	aws_secret_access_key=config.AWS_SECRECTKEY,
	region_name="us-east-1"
)
TINY_URL = "http://tinyurl.com/api-create.php"
sg = sendgrid.SendGridAPIClient(config.SENDGRID_API_KEY)
from_email = Email("AntAlmanac@gmail.com")
qa_email = Email(config.QA_EMAIL)
EMAIL_SUBJECT = "[AntAlmanac Notifications] Space Just Opened Up"

def shorten(long_url):
	'''Uses tinyurl to shorten long urls'''
	try:
		url = TINY_URL + "?" \
			+ urllib.parse.urlencode({"url": long_url})
		res = requests.get(url)
		# print("LONG URL:", long_url) # original url
		# print("SHORT URL:", res.text) # shortened version
		return res.text if len(res.text)<50 else long_url # return shorten url
	except Exception as e:
		return long_url # if unable to get shorten url, just return back the long one


def send_notifications(status_type, code, db):
	'''Sends push/text/email notifications for a specific course'''
	if status_type == "OPEN":
		course_url = shorten(WEBSOC + urllib.parse.urlencode([('YearTerm',TERM),('CourseCodes',code)])) 	# shorten the course_url
		msg = 'Space opened in {}. Code: {} ({}). '.format(names[code], code, course_url)					# text/email msg
		push_msg = '{} is open. Click to register.'.format(code)											# push msg
	elif status_type == "Waitl":
		course_url = shorten(WEBSOC + urllib.parse.urlencode([('YearTerm',TERM),('CourseCodes',code)]))
		msg = 'Waitlist opened for {}. Code: {} ({}). '.format(names[code], code, course_url)
		push_msg = '{} waitlist is open. Click to add to waitlist.'.format(code)
	elif status_type == "None":
		course_url = WEBSOC + urllib.parse.urlencode([('YearTerm',TERM),('CourseCodes',code),('CancelledCourses','Include')])
		msg = '{}. Code: {} ({}) has been cancelled'.format(names[code], code, shorten(course_url))
		push_msg = '{} has been cancelled.'.format(code)

	# send push notifications
	print('push')
	click_link = "https://login.uci.edu/ucinetid/webauth?return_url=https://webreg2.reg.uci.edu:443/cgi-bin/wramia?page=login?call=0011&info_text=Reg+Office+Home+Page&info_url=https://www.reg.uci.edu/"	# webreg link
	if status_type == "None":
		click_link = course_url		# websoc link for the cancelled course
	for token in tokens[code]:
		fcm = "https://fcm.googleapis.com/fcm/send"
		headers = {"Authorization": config.PUSH_AUTHKEY,
				   "Content-Type": "application/json"}
		body = {
			"notification": {
				"title": "AntAlmanac Notifications",
				"body": push_msg,
				"click_action": click_link,
				"icon": "https://www.ics.uci.edu/~rang1/AntAlmanac/img/LogoSquareWhite.png"
			},
			"to": token
		}
		r = requests.post(fcm, data=json.dumps(body), headers=headers)
		print(r.status_code, r.reason)

	# send sms notifications
	print('sms')
	if aws != None:
		for num in nums[code]:
			try:
				long_url = '{}/sms/{}/{}/{}'.format(config.BASE_URL, code, urllib.parse.quote(names[code]), num)
				sms_msg = 'AntAlmanac: ' + msg + 'To add back to watchlist: ' + shorten(long_url)
				aws.publish(
					PhoneNumber="+1"+num,
					Message=sms_msg
					)
				content = Content("text/html",sms_msg)
				mail = Mail(from_email, "[AntAlmanac Notifications] SMS CC", qa_email, content) #For quality assurance purposes
				response = sg.client.mail.send.post(request_body=mail.get()) #For quality assurance
				# print(code)
			except:
				content = Content("text/html",'SOMETHING WENT WRONG:   '+sms_msg)
				mail = Mail(from_email, "[AntAlmanac ERROR] SMS Hit the Fan", qa_email, content) #For quality assurance purposes
				response = sg.client.mail.send.post(request_body=mail.get()) #For quality assurance


	# send email notifications
	print('emails')
	for house in emails[code]:
		to_email = Email(house)
		content = Content("text/html",'<html><p>'+msg+'</p><p>Here\'s WebReg while we\'re at it: <a href="https://www.reg.uci.edu/registrar/soc/webreg.html" target="_blank">WebReg</a></p><p>You have been removed from this watchlist; to add yourself again, please visit <a href="https://antalmanac.com" target="_blank">AntAlmanac</a> or click on <a href="{}/email/{}/{}/{}" target="_blank">this link</a></p><p>Also, was this notification correct? Were you able to add yourself? Please do let us know asap if there is anything that isn\'t working as it should be!!! <a href="https://goo.gl/forms/U8CuPs05DlIbrSfz2" target="_blank">Give (anonymous) feedback!</a></p><p>Yours sincerely,</p><p>Poor Peter\'s AntAlmanac</p></html>'.format(config.BASE_URL, code, urllib.parse.quote(names[code]), house))
		mail = Mail(from_email, EMAIL_SUBJECT, to_email, content)
		response = sg.client.mail.send.post(request_body=mail.get())
		content = Content("text/html",'<html><p>'+msg+'</p><p>Add back: {}/email/{}/{}/{}</p></html>'.format(config.BASE_URL, code, urllib.parse.quote(names[code]), house))
		mail = Mail(from_email, EMAIL_SUBJECT, qa_email, content) #For quality assurance purposes
		response = sg.client.mail.send.post(request_body=mail.get()) #For quality assurance
		# print(code)

	# Delete course code from database and local variables
	db.queue.delete_one({"code": str(code)})
	emails.pop(code, None)
	nums.pop(code, None)
	names.pop(code, None)
	tokens.pop(code, None)



# initialize senders
emails, nums, names, tokens = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)

while True:
	print("run")
	old = time.time()											# to check code runtime
	db = pymongo.MongoClient(config.MONGODB_URI).get_database()

	courses = {}												# create a dict of courses for doggo to fetch data for
	# initialize/update variables...
	for course in db.queue.find():
		# print(course)
		code = course['code']
		if len(emails[code]) != len(course['emails']):			# checks if locally stored email dict is different from the database's
			emails[code] = course['emails']
		if len(nums[code]) != len(course['nums']):
			nums[code] = course['nums']
		if len(names[code]) != len(course['name']):
			names[code] = course['name']
		if len(tokens[code]) != len(course['push']):			### uncomment when all courses in db are updated with 'push' !
			tokens[code] = course['push']

		if code not in courses:
			courses[code] = None

	print(len(courses))

	# Dump courses so doggo knows what course info to fetch
	try:
		pickle.dump(courses, open('l.p', 'wb'))
		# print("dumping")
	except:
		print('Paul did not dump properly')
		continue
	# Load course statuses that doggo fetched
	try:
		statuses = pickle.load(open('s.p','rb'))
		# print("loading")
	except:
		print('Paul did not load properly')
		continue

	# For testing purposes
	#print(time.time()-old)
	#print(len(statuses))
	#print(statuses)

	# Extracting list of open / waitl / cancelled courses
	open_list, wait_list, cancelled_list = list(filter(lambda k: statuses[k] == "OPEN", statuses.keys())), list(filter(lambda k: statuses[k] == "Waitl", statuses.keys())), list(filter(lambda k: statuses[k] == None, statuses.keys()))
	# If all are empty, then no notifications to send
	if len(open_list) == 0 and len(wait_list) == 0 and len(cancelled_list) == 0:
		continue

	# Sends notifications in OPEN -> Waitl -> Cancelled priority
	for code in open_list:
		send_notifications("OPEN",code,db)
	for code in wait_list:
		send_notifications("Waitl",code,db)
	for code in cancelled_list:
		print('QUAN HELP ME! SOMETHING IS WRONG')
		#send_notifications("None",code,db)
