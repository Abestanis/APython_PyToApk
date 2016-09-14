# This tests the twisted module

from twisted.internet import reactor, protocol

# Server #

class Echo(protocol.Protocol):
    """This is just about the simplest possible protocol"""
    
    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        print('[Server] Received: "' + str(data) + '" from ' + str(self.transport.getPeer()))
        self.transport.write(data)

def setupServer():
    """This runs the protocol on port 8000"""
    factory = protocol.ServerFactory()
    factory.protocol = Echo
    reactor.listenTCP(8000,factory)

# Client #

class EchoClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""
    
    def connectionMade(self):
        print('[Client] Starting! My Ip-address: ' + str(self.transport.getHost()))
        print('[Client] Sending message to server...')
        self.transport.write("hello, world!")
    
    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        print('[Client] Server said: "' + str(data) + '"')
        print('[Client] Terminating connection...')
        self.transport.loseConnection()
    
    def connectionLost(self, reason):
        print('[Client] Connection closed.')

class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print('[Client] Connection failed!')
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        print('[Client] Connection lost.')
        reactor.stop()

def setupClient():
    f = EchoFactory()
    reactor.connectTCP("localhost", 8000, f)

# Main #

def run():
    setupServer()
    setupClient()
    reactor.run()
