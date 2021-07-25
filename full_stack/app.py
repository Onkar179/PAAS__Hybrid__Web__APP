from argparse import ArgumentParser
from flask import Flask, render_template, Response , request , jsonify , send_file
import os
import math
import random
import smtplib
import sys
from werkzeug import secure_filename
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError


AUDIO_FORMATS = {"ogg_vorbis": "audio/ogg",
                 "mp3": "audio/mpeg",
                 "pcm": "audio/wave; codecs=1"}

session = Session(profile_name="default")
polly = session.client("polly")

app = Flask("dockerapp")

UPLOAD_FOLDER = '/var/www/cgi-bin'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

op = []

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route("/", methods= [ 'GET' ])
def wlcm():
    return render_template('login.html')

@app.route("/send" , methods= [ 'GET' ])
def send():
    email = request.args.get("email")
    digits="0123456789"
    OTP=""
    for i in range(6):
        OTP+=digits[math.floor(random.random()*10)]
    passwd = OTP
    otp = OTP + " is your OTP"
    msg = otp
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("sender_email", "sender_passwd")
    s.sendmail("sender_email",email,msg)
    s.quit()
    op.append(passwd)
    if len(op) is not None:
        return render_template('success.html')

@app.route("/validate", methods=[ 'GET' ])
def home():
    OTP = op.pop()
    ios = request.args.get("otp")
    print(OTP)
    if ios == OTP:
        return render_template('main.html')        
    else:
        return render_template('error.html')


@app.route("/file" , methods=[ 'GET', 'POST' ])
def save():
    if request.method == 'POST':
      f = request.files['filename']
      fb = secure_filename(f.filename)
      f.save(os.path.join(app.config['UPLOAD_FOLDER'] , fb))
      return render_template("upload.html")


@app.route('/polly', methods=['GET'])
def index():
    return render_template('polly.html')


@app.route('/audio', methods=['GET'])
def read():
    # Get the parameters from the query string
    try:
        outputFormat = request.args.get('outputFormat')
        text = request.args.get('text')
        voiceId = request.args.get('voiceId')
    except TypeError:
        raise InvalidUsage("Wrong parameters", status_code=400)

    # Validate the parameters, set error flag in case of unexpected
    # values
    if len(text) == 0 or len(voiceId) == 0 or \
            outputFormat not in AUDIO_FORMATS:
        raise InvalidUsage("Wrong parameters", status_code=400)
    else:
        try:
            # Request speech synthesis
            response = polly.synthesize_speech(Text=text,
                                               VoiceId=voiceId,
                                               OutputFormat=outputFormat)
        except (BotoCoreError, ClientError) as err:
            # The service returned an error
            raise InvalidUsage(str(err), status_code=500)

        return send_file(response.get("AudioStream"),
                         AUDIO_FORMATS[outputFormat])


@app.route('/voices', methods=['GET'])
def voices():
    """Handles routing for listing available voices"""
    params = {}
    voices = []

    try:
        # Request list of available voices, if a continuation token
        # was returned by the previous call then use it to continue
        # listing
        response = polly.describe_voices(**params)
    except (BotoCoreError, ClientError) as err:
        # The service returned an error
        raise InvalidUsage(str(err), status_code=500)

    # Collect all the voices
    voices.extend(response.get("Voices", []))

    return jsonify(voices)




app.run(port=1111, host='0.0.0.0')
