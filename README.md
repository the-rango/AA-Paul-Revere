# Paul Revere
Lets you know when the British are coming. Just kidding. Notifies you when classes or waitlists open with email (SendGrid), text (AWS SNS), and push notification (Firebase). Paul works with AntAlmanac for UCI.

There are actually two programs here, that do separate jobs but work together to make Paul Revere work. We used a MongoDB datastore for the watchlist.

## Bookkeeper
The bookkeeper is a Flask API that accepts requests to add courses to watchlist. Even though it is mostly called by AntAlmanac programmatically, users may view it when using the add-back link that comes with notifications. For these landing pages, we used amazing UCI landscape photography taken by students.

It also includes an endpoint to send test push notifications to verify that the user is on a compatible device.

#### Usage
GET request to /{type}/{code}/{name}/{address}, where type is 'email', 'sms', or 'push', code is the 5 digit section code, name is the name of the course, and address is the email address, phone number of push token to be added to the database.

## Dispatcher
The dispatcher checks if the courses on the watchlist have opened, and if any has, it sends out the appropriate notifications.

This is done concurrently with Paul and his doggo, one checks the watchlist and sends notifications, while the other one fetches course statuses. Paul and doggo communicate via pickling. We preferred this over a database because it was one fewer thing to set up (and break) and because pickling is surprisingly efficient.

We parse [UCI Registrar's Schedule of Classes (SOC)](https://www.reg.uci.edu/perl/WebSoc) with BeautifulSoup which uses lxml under the hood.

Overall, it takes generally less than 15 seconds to receive a push notification from the moment when a course is dropped, anecdotally.

#### Usage
Run both paul.py and doggo.py as separate processes.
