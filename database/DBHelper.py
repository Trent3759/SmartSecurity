"""
	Created by Trenton Scott
	Created on 02/23/2018
	Purpose: The purpose of this class is to assist with database interaction 
	on the FandRec client. 
"""

import sqlite3, random, hashlib

class DBHelper:
	global conn
	global curr 
	global keepConnOpen
	
	def __init__(self, active = False):
		"""
			
			Created by Trenton D Scott
			Output: N/A
			Description: Initializes DBHelper
			Usage: DBHelper(active)
				active	--	if True the database connection will stay open until
							closed. If false, the database connection will close 
							after 1 transaction. 
		
		"""
		
		self.db_connect()
		try:
			conn.execute("SELECT * FROM Users")
		except:
			#if the above throws an error, the table does not exist and will be created. 
			#this should only occurs during initial setup. 
			conn.execute("CREATE TABLE Users ( ID INTEGER PRIMARY KEY, Username varchar(20) UNIQUE, Password varchar(20),"
			"Salt varchar(16))")
				
		global keepConnOpen
		keepConnOpen = active;
		
		
	def db_connect(self):
		"""
			Created by Trenton D Scott
			Output: N/A
			Description: Connected to database
			Usage: This function should only be called by 
		"""
		#connect to the database. 
		try:
			global conn
			conn = sqlite3.connect('database/database.db')
		except:
			print("An error was encountered while trying to connect to the database. ")
		global curr
		curr = conn.cursor()	

	def createUser(self, credentials):
		"""
			Created by Trenton D Scott
			Output: Boolean
			Description: Stores new user in the database. 
			Usage: DBHelper.createUser([username, password])
		
		"""
		CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
		salt= ""
		for i in range(16):
			salt += random.choice(CHARS)
		
		encodedPass = (credentials[1] + salt).encode()
		sec_pass = hashlib.sha256(encodedPass)
		
		try:
			conn.execute("INSERT INTO Users (Username, Password, Salt) VALUES (?,?,?)", (credentials[0], str(sec_pass.hexdigest()), salt))
			conn.commit()
			return True
		except sqlite3.IntegrityError:
			return False

		if not keepConnOpen: self.disconnect()

	def authenticate(self, credentials):
		"""
			Created by Trenton D Scott
			Output: Boolean
			Description: Returns true on successful authentication 
			Usage: DBHelper.getUsernames()
		
		"""
		username = credentials[0]
		password = credentials[1]

		
		try: 
			try:
				curr.execute("SELECT Salt FROM Users WHERE Username=?", (username,))
				salt = curr.fetchone()[0]
				encodedPass = (password + salt).encode()
				testHash = hashlib.sha256(encodedPass).hexdigest()

				curr.execute("SELECT Password FROM Users WHERE Username=?", (username,))

				storedHash = curr.fetchone()[0]
			except:
				return False

			if (testHash == storedHash):
				return True
			else:
				return False

		except:
			print("Could not execute query on database. The database could be closed. ")
		if not keepConnOpen: self.disconnect()

		
		
	def getUsernames(self):
		"""
			Created by Trenton D Scott
			Output: List [String, ...]
			Description: Returns username from database based on ID. 
			Usage: DBHelper.getUsernames()
		
		"""
		curr.execute("SELECT Username from Users");
		userList = []
		usernames = curr.fetchall()
		if not keepConnOpen: self.disconnect()
		for x in usernames:
			userList.append(x[0])
		return userList

	def getUsernameById(self, ID):
		"""
			Created by Trenton D Scott
			Output: String
			Description: Returns username from database based on ID. 
			Usage: DBHelper.getUserNameById(Integer)
		
		"""
		curr.execute("SELECT Username FROM Users WHERE ID=?", (ID,))
		try:
			return curr.fetchone()[0]
		except: 
			return "NoUserExists"
		if not keepConnOpen: self.disconnect()
		
	def getIDByUsername(self, username):
		"""
			Created by Trenton D Scott
			Output: String
			Description: Returns ID from database based on username. 
			Usage: DBHelper.getIdByUsername(String)
		
		"""
		curr.execute("SELECT ID FROM Users WHERE Username=?", (username,))
		try: 
			return curr.fetchone()[0]
		except:
			return "NoUserExists"
		if not keepConnOpen: self.disconnect()
		
	def disconnect(self):
		conn.close()
