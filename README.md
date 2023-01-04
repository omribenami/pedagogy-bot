Please ⭐ this repo if you find it useful

# Pedagogy-bot
Pedagogy-bot is a python based bot that scraps the Pedagogy (EDU) web site and alerts me when the kids has homeworks to complete. this bot is based on Ofek-bot (https://github.com/t0mer/ofek-bot) made by the Amzazing Tomer Klein (https://github.com/t0mer)

## Features
 - Monitor kids homework status
 - Monitor kids events(goodwork, late, etc...) status
 - Schedule when to run.
 - Creates a JSON file which is being monitored as an Home Assistant sensors


## Components and Frameworks used in pedagogy
* [Loguru](https://pypi.org/project/loguru/) For logging.
* [Schedule](https://pypi.org/project/schedule/) For alerts schedule.
* [Selenium](https://selenium-python.readthedocs.io/) For data scrapping.

## Installation
Pedagogy is a docker based application that can be installed using docker compose:
```
version: "3.6"
services:
  pedagogy-bot:
    image: omribenami/pedagogy-bot
    container_name: pedagogy-bot
    restart: always
    environment:
      - SCHEDULES=
    volumes:
      - path/to/config:/app/config
```

### Environment
* SCHEDULES - Set checks schedules times splited with "," (14:00,15:30) - default is set to 16:00.

### Volumes
pedagogy-bot is using the kids login credentials to the pedagogy website.
In the config folder there is a config.yaml files for saving the credentials.
in order to find the school value please navigate to https://pedagogy.co.il/parent.html#!/login -> click right mouse button on the school field 
and choose "inspect" -> open the drop down  triangle and find the required value (e.g ```<option value="sc_tops_hi6"> חט"ב ועליונה - פדגוגי</option>``` ). 
Make sure to create the config file in the following structure:

```
kids:
  - name: JohnDoe
    username:  "XXXX"
    password:  "XXXX"
    school: "sc_axxxx"

  - name: JoanDoe
    username:  "XXXX"
    password:  "XXXX"
    school: "sc_axxxx"


```


#### create Home Assistant Sensors ###
```
 - platform: command_line
   name: homeworks
   command: "cat config/homework.json"
   value_template: >- 
     {% for i in  state_attr('sensor.homeworks', 'homeworks' ) %}
      {{ i}}
     {% endfor %}
   json_attributes: 
     - homeworks
   scan_interval: 5

 - platform: command_line
   name: events
   command: "cat config/homework.json"
   value_template: >-
    {% for i in  state_attr('sensor.events', 'events' ) %}
      {{ i}}
     {% endfor %}
   json_attributes: 
     - events
   scan_interval: 5
   
```


####  create Home Assistant on/off Sensor ###

```
sensor:
 - platform: template
     sensors:
       homework_switch:
          friendly_name: Homework_switch
          value_template: >
            {% if states("sensor.homework") == '' %}
              off 
            {% else %} 
              on 
            {% endif -%}


sensor:
 - platform: template
     sensors:
       events_switch:
          friendly_name: events_switch
          value_template: >
            {% if states("sensor.events") == '' %}
              off 
            {% else %} 
              on 
            {% endif -%}
```
