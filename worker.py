from urllib.parse import urlparse;
import os;
import socket;
from recvall import recvall;


# Handle the six required commands.
def takecommand(args, control, data):
  ftpurl = init(control, args)
  commtype = args.command
  if(args.location2 == None):
    if commtype in ["cp", "mv"]:
      print(commtype +" needs two args!")
      exit(-1)
  else:
    if commtype in ["mkdir", "rmdir", "ls", "rm"]:
      print(commtype + " needs one arg!")
      exit(-1)
  match commtype:
    case "mkdir":
      mkd(control, ftpurl.path)
      return
    case "rmdir":
      rmd(control, ftpurl.path)
      return
    case "ls":
      list(control, ftpurl.path, data)
      return
    case "rm":
      dele(control, ftpurl.path)
      return
    case "mv":
      mv(control, data, args.location1, args.location2)
      return
    case "cp":
      cp(control, data, args.location1, args.location2)
      return
  print("Unknown command " + commtype)
  
# Error checks to see if the request is reasonable:
# - if there is one path argument, it must be a network path
# - if there are two, there must be one network and one local path
# Also readies the control socket!
def init(control, args):
  ftpurl = "aah"
  if(args.location2 != None): # Either argument might be a url
    arg1link = args.location1.startswith("ftp://")
    arg2link = args.location2.startswith("ftp://")
    if arg1link and arg2link:
      print("Both paths cannot be serverside!")
      exit(-1)
    elif arg1link: #valid ftp link
      ftpurl = urlparse(args.location1, "ftp")
    elif arg2link:
      ftpurl = urlparse(args.location2, "ftp")
    else:
      print("Both paths cannot be local!")
      exit(-1)
  else:
    if(not args.location1.startswith("ftp://")):
      print("Singular path my not be local!")
      exit(-1)
    ftpurl = urlparse(args.location1, "ftp")
  

  control.connect((ftpurl.hostname, 21))
  print(recvall(control).decode())

  if(ftpurl.username == None):
    ftpurl.username = "anonymous"
  usernreq = "USER " + ftpurl.username + "\r\n"
  if(ftpurl.password != None):
    passreq = "PASS " + ftpurl.password + "\r\n"
  
  control.send(usernreq.encode())
  print(recvall(control).decode())
  if(ftpurl.password != None):
    control.send(passreq.encode())
    print(recvall(control).decode())
  return ftpurl



# UTILITIES

# Sends a PASV request to the server, readying the data socket to recieve/send data.
# Also sets data type, mode and structure.
def pasv(control, data):
  typereq = "TYPE I\r\n"
  modereq = "MODE S\r\n"
  strureq = "STRU F\r\n"
  # TYPE request
  control.send(typereq.encode())
  print(recvall(control).decode())
  # MODE req
  control.send(modereq.encode())
  print(recvall(control).decode())
  # STRU req
  control.send(strureq.encode())
  print(recvall(control).decode())

  pasvreq = "PASV\r\n"
  control.send(pasvreq.encode())
  msg = recvall(control).decode()
  print(msg)
  if(msg[0] in ["4", "5", "6"]):
    print("Error in PASV request!")
    exit(-1)
  # Getting the IP + port from the returned info
  numlist = msg[27:(len(msg) - 4)].split(",")
  port = (int(numlist[4]) << 8) + int(numlist[5])
  ip = numlist[0] + '.' + numlist[1] + '.' + numlist[2] + '.' + numlist[3] # There's a smarter way to do this but i'm tired.
  data.connect((ip, port))


# Sends a file to the FTP client at the given FTP URL, serverdest, from the given file path localsource.
def store(control : socket.socket, data : socket.socket, localsource, serverdest):
  pasv(control, data) # open up a data channel!
  storereq = "STOR " + urlparse(serverdest, "ftp").path + "\r\n"
  control.send(storereq.encode())
  msg = recvall(control).decode()
  print(msg)
  if(msg[0] in ["4", "5", "6"]):
    print("Error in STOR request!")
    exit(-1)

 
  file = open(localsource, mode='rb')
  tosend = bytearray(file.read())
  data.send(tosend) #????
  data.close()
  msg = recvall(control).decode()
  print(msg)
  if(msg[0] in ["4", "5", "6"]):
    print("Error in STOR request!")
    exit(-1)
  pass
  

# Sends a request and downloads the given file from the given FTP location, serversource, to the given path, localdest.
def retrieve(control, data, serversource, localdest):
  pasv(control,data)
  retreq = "RETR " + urlparse(serversource, "ftp").path + "\r\n"
  control.send(retreq.encode())
  msg = recvall(control).decode()
  print(msg)
  if(msg[0] in ["4", "5", "6"]):
    print("Error in RETR request!")
    exit(-1)
  downdata = data.recv(1024)
  with open(localdest, "wb+") as binary_file:
    while downdata:
      binary_file.write(downdata)
      downdata = data.recv(1024)
  msg = recvall(control).decode()
  print(msg)
  if(msg[0] in ["4", "5", "6"]):
    print("Error in RETR request!")
    exit(-1)
  #no need to close the data socket?
  
# Helper for mv and cp. Sends a file from localhost to the serverdest.
def localToServer(control, data, localsource, serverdest, delete : bool):
  store(control, data, localsource, urlparse(serverdest).path)
  if delete:
    os.remove(localsource)

# Helper for mv and cp. Downloads a file from the serverdest to the localhost.
def serverToLocal(control, data, serversource, localdest, delete : bool):
  retrieve(control, data, urlparse(serversource).path, localdest)
  if delete:
    dele(control, urlparse(serversource).path)




# COMMANDS

# Moves a file from the source to the destination.
# One of source and dest must be an FTP URL, the other must be a local path.
# Works the same as cp, but deletes the file after sending/retrieving it.
def mv(control, data, source, dest):
  if(source.startswith("ftp://")): #serverside source
    serverToLocal(control, data, source, dest, True)
  else: #checking for two server URLs/two local paths is checked in init()
    localToServer(control, data, source, dest, True) 

# Copies a file from the source to the destination.
# One of source and dest must be an FTP URL, the other must be a local path.
def cp(control, data, source, dest):
  if(source.startswith("ftp://")): #serverside source
    serverToLocal(control, data, source, dest, False)
  else: #checking for two server URLs/two local paths is checked in init()
    localToServer(control, data, source, dest, False) 

# Makes a directory with the given name at the given path.
# If the directory cannot be created, exit the program with -1.
def mkd(control, path):
  makedirreq = "MKD " + path + "\r\n"
  control.send(makedirreq.encode())
  msg = recvall(control).decode()
  if(msg[0] in ["4", "5", "6"]):
    print("Error in PASV request!")
    exit(-1)
  
# Removes a directory with the given name at the given path.
# If the directory cannot be deleted, exit the program with -1.
def rmd(control, path):
  remdirreq = "RMD " + path + "\r\n"
  control.send(remdirreq.encode())
  msg = recvall(control).decode()
  if(msg[0] in ["4", "5", "6"]):
    print("Error in RMD request!")
    exit(-1)

def dele(control, path):
  delereq = "DELE " + path + "\r\n"
  control.send(delereq.encode())
  msg = recvall(control).decode()
  if(msg[0] in ["4", "5", "6"]):
    print("Error in DELE request!")
    exit(-1)

def list(control, path, data):
  pasv(control, data)
  listreq = "LIST " + path + "\r\n"
  control.send(listreq.encode())
  msg = recvall(control).decode()
  if(msg[0] in ["4", "5", "6"]):
    print("Error in LIST request!")
    exit(-1)
  #print(msg)
  info = recvall(data).decode()
  print(info)
