"""
Project: Project - SS (Smart Security)
Description: A security system for modern problems.
Notes:

Liscense:
Copyright (c) 2019, Trenton D Scott || TrentApps || Other Related Branding for Trenton D Scott
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
		* Redistributions of source code must retain the above copyright
		  notice, this list of conditions and the following disclaimer.
		* Redistributions in binary form must reproduce the above copyright
		  notice, this list of conditions and the following disclaimer in the
		  documentation and/or other materials provided with the distribution.
		* Neither the name of the FandRec Dev Team nor the
		  names of its contributors may be used to endorse or promote products
		  derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL FandRec Dev Team BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
#==============================Imports=======================================
import sys, ujson, numpy as np, base64
from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource

from autobahn.twisted.websocket import WebSocketClientFactory, \
		 WebSocketServerFactory, WebSocketClientProtocol, \
		 WebSocketServerProtocol, connectWS, listenWS

from flask import Flask, render_template, request as flask_request, make_response, redirect, url_for

app = Flask(__name__)
app.config["CACHE_TYPE"] = "null"

#~~~~~~~~~~~~ Database Import ~~~~~~~~~~~~#

from database import DBHelper
DBHelper = DBHelper.DBHelper

#==========================Global Variables==================================

ip_address = "0.0.0.0"
port_nums = [8090, 8091, 8073]

app = Flask(__name__)


#==========================Web Server========================================

class WebComms():
		def __init__(self, url):
				#STEP-1: Start up the camera listener
				self.cam_factory = CameraFactory(url + str(port_nums[1]), self)

				#STEP-2: Start up webpage
				self.web_factory = WebFactory(url + "8092", self)

				listenWS(self.web_factory)
				listenWS(self.cam_factory)

				#self.compes_factory = None

				self.user = None
				self.camera = None


class WebsiteServerProtocol(WebSocketServerProtocol):
		def __init__(self):
				WebSocketServerProtocol.__init__(self)
				self.connected = False

		def onConnect(self, request):
				#self.cameraName = self.factory.bridge.camera
				self.connected = True

				self.factory.connect("client1", self)

				print("WebSocket connection request: {}".format(request.peer))

		def onOpen(self):
				print("Connection to client opened!")

		def onMessage(self, data, isBinary):
				data = ujson.loads(data.decode("UTF8"))
				#self..clientName = data.decode("UTF8")
				self.factory.connect(self.clientName, self)


		def onClose(self, wasClean, code, reason):
				self.connected = False
				self.factory.disconnect("client1")
				print("Connection to client was closed!")

class WebFactory(WebSocketServerFactory):
		protocol = WebsiteServerProtocol
		def __init__(self, url, bridge):
				WebSocketServerFactory.__init__(self, url)
				self.frame = None
				self.connections = {}
				self.bridge = bridge

		def connect(self, clientName, connection):
				#if (clientName not in self.connections):
				self.connections[clientName] = connection

		def disconnect(self, clientName):
				if ("client1" in self.connections):
						del self.connections["client1"]
				else:
						print("Nothing to delete matching client name. ")

		def post(self, clientName, message):
				try:
						self.connections["client1"].sendMessage(message)
				except:
						pass


#==========================Camera Server=====================================
class CameraServerProtocol(WebSocketServerProtocol):
		def onConnect(self, request):
				self.clientName = request.headers['camera_id']
				self.factory.connect(self.clientName, self)
				print("WebSocket connection request: {}".format(request.peer))

		def onOpen(self):
				print("Connection to camera_client opened.")

		def onMessage(self, data, isBinary):
				frame = ujson.loads(data.decode("utf8"))
				frame = np.asarray(frame, np.uint8)
				frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

				frame = cv2.UMat(frame)
				frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 20])[1]
				frame = base64.b64encode(frame)
				print("Processing frame...")
				#send to web factory
				self.factory.bridge.web_factory.post(self.factory.bridge.user, frame)

		def onClose(self, wasClean, code, reason):
				self.factory.disconnect(self.clientName)
				print("Connection to client was closed!")

class CameraFactory(WebSocketServerFactory):
		protocol = CameraServerProtocol
		def __init__(self, url, bridge):
				WebSocketServerFactory.__init__(self, url)
				self.frame = None
				self.connections = {}
				self.bridge = bridge
		def connect(self, clientName, connection):
				if (clientName not in self.connections):
						self.connections[clientName] = connection
				else:
						print("Failed to register connection. ")

		def disconnect(self, clientName):
				if (clientName in self.connections):
						del self.connections[clientName]
				else:
						print("Nothing to delete matching client name. ")

		def post(self, clientName, message):
				self.connections[clientName].sendMessage(message.encode("UTF8"))
#=======================================================================================

@app.route("/", methods = ["GET"])
def index():
	return render_template("index.html")

@app.route("/active", methods = ["GET"])
def active():
	return render_template('active.html')

@app.route("/reg_complete", methods = ["GET"])
def reg_complete():
		resp = make_response(render_template('active.html', user=comms.user))
		return resp

@app.route("/connect", methods = ["POST"])
def connect():
		#process users credentials here.
		db = DBHelper(True) #close the connection in this function.

		username = flask_request.form['username_field']
		password = flask_request.form['password_field']

		authSuccess = True #db.authenticate([username, password])

		if (authSuccess):
			return redirect(url_for('active'))
		else:
			return render_template('index.html', message="Failed to authenticate. Please try again. ")

		db.disconnect()

@app.route("/register", methods = ["POST", "GET"])
def register():
		if flask_request.method == 'POST':
				username = flask_request.form['username_field']
				password = flask_request.form['password_field']

				db = DBHelper()
				dbSuccess = db.createUser([username, password])

				if (dbSuccess):
						global comms
						comms.registerUser(username, password)
						#comms.cam_factory.rec.is_registering = True
						resp = make_response(render_template('profile.html', user = username))
						return resp
				else:
						#display message on webpage and have the user try again.
						return "failed register"
		else:
				return render_template("register.html")


@app.route("/camera_page", methods = ["GET"])
def camera_page():
		return render_template("cameras.html")

@app.route("/error_page", methods = ["GET"])
def error_page():
	return render_template("error.html")

#==========================Main========================================
def main():
		"""
		Description: Starts all of the factories and protocols needed to start the server and all of its functions.
		Notes:
				1.
				2.
		"""
		log.startLogging(sys.stdout)
		#initRecognizer()
		global comms
		comms = WebComms("ws://localhost:")
		wsResourse = WSGIResource(reactor, reactor.getThreadPool(), app)


		#STEP-5: Setup the reactor
		reactor.listenTCP(port_nums[0], Site(wsResourse))

		#STEP-6: run
		reactor.run()

if(__name__ == "__main__"):
		main()
