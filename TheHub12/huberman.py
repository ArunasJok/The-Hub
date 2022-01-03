#importing libraries required for the app
from typing import Text
from flask import Flask, request, render_template, jsonify
from datetime import date,datetime
import time
import threading
from sense_hat import SenseHat
import subprocess
from werkzeug.utils import redirect
import vlc
from localStoragePy import localStoragePy
import smtplib

#setting up Flask local server
app = Flask(__name__)

running = False # to control loop in thread
value = 0   
#storing data localy
localStorage = localStoragePy('TheHub', Text)

#Function to set the alarm and start the light/sound when trigered 
def startAlarm(alarm_time, alarm_date):
    sense = SenseHat()
    while True:
                today=date.today().strftime("%Y-%m-%d")
                current_time = datetime.now().strftime("%H:%M")
                time.sleep(1)                
                print("Current Date is:",today)
                print("Current Time is:", current_time)
                print("Alarm set to: ", alarm_time, alarm_date)
                if alarm_time == current_time:
                    if alarm_date == today:
                        print("Time to Wake up")
                        subprocess.run(['sh', './light.sh', 'on'])                        
                        media_player = vlc.MediaPlayer()
                        media = vlc.Media("distress.wav")
                        media_player.set_media(media)
                        media_player.play()                        
                        time.sleep(10)
                        media_player.stop()                                                                                 
                        break 

#Default route to load initial page
@app.route('/', methods=['GET','POST']) 
def index():
    return render_template('index.html')

#Route to control light on/off
@app.route('/<device>/<action>')
def light(device=None, action=None):
    global running
    global value    

    if device:
        if action == 'on':
            if not running:                                
                print('start')
                running = True
                subprocess.run(['sh', 'light.sh', 'on'])                
            else:
                print('already running')
        elif action == 'off':
            if running:                            
                print('stop')
                subprocess.run(['sh', 'light.sh', 'off'])
                0
                running = False  # it should stop thread
            else:
                print('not running')        
    return render_template('index.html')
    
#Route to display and update the readings
@app.route('/update', methods=['GET','POST'])
def update():
    global celcius, humidity, pressure, date
    
    sense = SenseHat()
    celcius = round(sense.get_temperature()-10, 1)
    humidity = round(sense.get_humidity(), 1)
    pressure = round(sense.get_pressure(), 1)
    today=date.today()
    dateToday=today.strftime("%Y-%m-%d")            
        
    return  jsonify({        
        'time': datetime.now().strftime("%H:%M:%S"),
        'celcius': celcius,
        'humidity': humidity,
        'pressure': pressure,
        'dateToday':dateToday,
       
    })

#Route to take in new alarm request and email a reminder to the user
@app.route('/alarm', methods=['GET','POST'])
def alarm():   
      
    if request.method=="POST":
            alarm_date=request.form["alarm_date"]
            alarm_time=request.form["alarm_time"]
            print("Alarm set to", alarm_date, alarm_time)

            gmail_user = 'fluxcapacitorpi@gmail.com'
            gmail_password = '20053946'

            sent_from = gmail_user
            to = ['jokubynas@gmail.com']
            subject = 'Alarm set!'
            body = 'Alarm is set to '+str(alarm_time)+' on the '+str(alarm_date)+'. Please go to bed at least 6h before!'

            email_text = """\
            From: %s
            To: %s
            Subject: %s

            %s
            """ % (sent_from, ", ".join(to), subject, body)

            try:
                smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                smtp_server.ehlo()
                smtp_server.login(gmail_user, gmail_password)
                smtp_server.sendmail(sent_from, to, email_text)
                smtp_server.close()
                print ("Email sent successfully!")
            except Exception as ex:
                print ("Something went wrong….",ex)            
            threading.Thread(target=startAlarm, args=(alarm_time, alarm_date,)).start()            
          
    return render_template('index.html', alarm_date=alarm_date, alarm_time=alarm_time)                

#Route to take in user next travel destination for alarm calculations(NOT FINISHED)
@app.route('/travel', methods=['GET','POST'])
def travel():    
    today=datetime.today()    
    if request.method=="POST":
            travel_date=request.form["travel_date"]
            travel_destination=request.form["travel_destination"]                     
            time_zone=request.form["time_zone"] 
            obj_travel_date = datetime.strptime(travel_date, "%Y-%m-%d")            
            delta=(obj_travel_date - today).days
            print("Traveling to", travel_destination, time_zone, travel_date, today, delta)
            
             
    return render_template('index.html', travel_date=travel_date, travel_destination=travel_destination, delta=delta)                             
    
app.run() 
