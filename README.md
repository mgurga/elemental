# elemental
- python 3
- uses sockets
- no dependencies
- multithreaded
- all data stored as JSON
- lots of command line options

*PS. The python 3 server is called a provider to make it less confusing*
<br/>

## Provider
This is what is going to be running 24/7 to provide servers for the users

### How it works
The provider works a lot like a Rest API where every request will have a response.
Every request should include a ```call```, an example of this is the login request:
```
{
  "call":"login",
  "usernm":"hello",
  "passwd":"world"
}
```
if the credentials are correct then the server will respond with
```
{
  "resp":true
}
```
if the credentials are incorrect the server will respond with
```
{
  "resp":false,
  "reason":"username does not exist"
}
```
the ```reason``` value will be different for each reason but gives insite on the problem

### Currntly supported provider calls
Wiki will go in depth on required values and responses
- ```login```
- ```register```
- ```createserver```
- ```joinserver```
- ```createchannel```
- ```deleteserver```
- ```leaveserver```
- ```message```
- ```getjoinedservers```
- ```getmessages```
- ```gettotalmessages```
- ```getprovidername```
- ```getserverchannels```
- ```deletechannel```

## Client (client.py)
A very simple client meant to be used as an example
- requires [blessed](https://pypi.org/project/blessed/)
- command line client
- uses all provider calls
- very simple code

### Client Commands
- ```/createserver```
- ```/deleteserver```
- ```/listservers```
- ```/listchannels```
- ```/joinserver```
- ```/gotoserver```
- ```/gotochannel```
- ```/createchannel```
- ```/deletechannel```

