# SimPy models for the Sending and Receiving Applications.
#
# The sending application:
#	- keeps creating new messages
#	- requests the lower-layer (rdt_sender)
#	  to deliver each message using the rdt_send() function
#
# The receiving application:
#	- receives the message delivered by the lower-layer to its
#	   deliver_data() method.
#	- does some basic validation. 

# Author: Devyani Remulkar



import simpy
import random
from Packet import Packet
import sys

class SendingApplication(object):

    def __init__(self, env, sending_interval):
        # Initialize variables
        self.env = env 
        self.rdt_sender = None
        self.total_messages_sent = 0
        self.sending_interval = sending_interval
        self.msg = 1
        # start behavior
        self.env.process(self.behavior())

    def behavior(self):
        
        while self.total_messages_sent < 1000:
            # wait for the 'sending_interval' amount of time
            assert(self.sending_interval > 0)
            yield self.env.timeout(self.sending_interval)
            
            # create a message (its just a number, for now.)
            # msg = self.total_messages_sent + 1
            
            print("TIME:", self.env.now, "SENDING APP: trying to send data", self.msg)
            # try to send it.
            while self.rdt_sender.rdt_send(self.msg):
                # success.
                self.msg += 1
                self.total_messages_sent += 1
                print("TIME:", self.env.now, "SENDING APP: trying to send data", self.msg)

class ReceivingApplication(object):

    def __init__(self, env):
        # Initialize variables
        self.env = env 
        self.total_messages_received = 0

    def deliver_data(self, data):
        # This function is called by the lower-layer (rdt_receiver)
        # to deliver data to the Receiving Application
        print("TIME:", self.env.now, "RECEIVING APP: received data", data)
        self.total_messages_received += 1
        
        # do some basic validation.
        if not (data == self.total_messages_received):
            print("ERROR!! RECEIVING APP: received wrong data:", data, ",expected:", self.total_messages_received)
            print("Halting simulation...")
            sys.exit(0)
