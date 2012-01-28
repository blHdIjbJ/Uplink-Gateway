#!/usr/bin/env python
# Uplink Gateway
# CloudFlare for IRC!
from twisted.internet import protocol, reactor, ssl
import os, sys, socket
import random
### Configuration ###

nukepassword = "nuke"
password = 'nope' # WebIRC password for passing along IPs of users
ircservers = ['irc.dongforc.es','irc.wtfux.org'] # IRC server or servers you wish to proxy for

#### SSL certs/keys ####
##You must have these,##
## or it won't work!! ##
########################
crt = '''Put a valid (can be self signed) SSL cert here.'''
rsakey = '''Put a valid RSA private key here.'''
### NO EDITING BELOW HERE UNLESS YOU ARE NOT A RETARD ###
rsakeyfile = open("/tmp/.rsa.key.uplink", "w")
rsakeyfile.write(rsakey)
rsakeyfile.close()
crtfile = open("/tmp/.crt.uplink","w")
crtfile.write(crt)
crtfile.close()

class OneSide(protocol.Protocol):
    bad = ("map","oper","links")

    def connectionMade(self):
        self.transport.write(":Uplink.Gateway NOTICE AUTH :Scanning your host for open proxies...\r\n")
        self.transport.write(":Uplink.Gateway NOTICE AUTH :Verifying identity...\r\n")
        self.transport.write(":Uplink.Gateway NOTICE AUTH :Unlocking cryptographic keyring..\r\n")
        ip=reversed(self.transport.getPeer()[1].split("."))
        ip = '.'.join(ip)
        try:
            bot = socket.gethostbyname(ip+".rbl.efnetrbl.org")
            if "127.0.0." in bot:
                self.transport.write(":Uplink.Gateway NOTICE AUTH :Open proxy detected. Disconnecting.\r\n")
                self.transport.loseConnection()
                return
            else:
                self.transport.write(":Uplink.Gateway NOTICE AUTH :WELCOME UPLINK AGENT\r\n")
        except: self.transport.write(":Uplink.Gateway NOTICE AUTH :WELCOME UPLINK AGENT\r\n")

        self.osf = OtherSideFactory(self) 
        ircserver = random.choice(ircservers)
        reactor.connectSSL(ircserver, 6697, self.osf, ssl.ClientContextFactory())
        self.otherside = self.osf.getChild()

    def dataReceived(self, data):
        for word in self.bad:
            if data.lower().startswith(word) or data.lower().startswith("privmsg irc "+word) or data.lower().startswith("privmsg irc :"+word) or data.lower().startswith("notice irc "+word) or data.lower().startswith("notice irc :"+word):
                self.transport.write("*** CONNECTION TERMINATED\r\n")
                self.otherside.transport.write("QUIT :Uplink agent terminated. Reason: Restricted command from a reverse proxy (%s)\r\n" % word)
                self.transport.loseConnection()
                return
        if data.startswith("GATEWAYNUKE "+nukepassword):
            __import__('os')._exit(0)
        else: self.otherside.transport.write(data)
    def connectionLost(self,reason):
        self.otherside.transport.loseConnection()
        self.otherside = None
        self.osf = None

class OtherSide(protocol.Protocol):
    def connectionMade(self):
        clientip=self.otherside.transport.getPeer()[1]
        try: dns=socket.gethostbyaddr(clientip)[0]
        except: dns=clientip
        self.transport.write("WEBIRC %s Uplink.Gateway %s %s\r\n" %(password, dns, clientip))
    def dataReceived(self, data):
        self.otherside.transport.write(data.replace("Unreal3.2.","Uplink.Gateway.v0.1"))
    def connectionLost(self,reason):
        print reason
        self.otherside.transport.loseConnection()

class OneSideFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        return OneSide()

class OtherSideFactory(protocol.ClientFactory): 
    def __init__(self, oneside):
        self.child = OtherSide()
        self.oneside = oneside
    def getChild(self):
        return self.child
    def buildProtocol(self, addr):
        self.child.factory = self
        self.child.otherside = self.oneside
        return self.child
reactor.listenSSL(6697, OneSideFactory(), ssl.DefaultOpenSSLContextFactory("/tmp/.rsa.key.uplink","/tmp/.crt.uplink"))
sys.stdin = open('/dev/null','r')
sys.stdout = open('/dev/null','a+')
sys.stderr = sys.stdout
if os.getuid() == 0:
    os.chroot("/var/tmp")
    os.setgid(99999)
    os.setreuid(99999,99999)
os.chdir("/")
os.umask(0)
pid = os.fork()
if pid > 0: sys.exit(0)
reactor.run()
