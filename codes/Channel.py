# SimPy model for an unreliable communication channel.
#
#	A packet sent over this channel:
#		
#		- can get lost, with probability Pl
#		- reaches the other end after a "propagation_delay" amount of time, if it is not lost.
#
# Author: Devyani Remulkar


import simpy
import random
from Packet import Packet
import copy

class UnreliableChannel(object):

    def __init__(self, env, name, propagation_delay, transmission_rate):
        # Initialize variables
        self.env = env 
        self.name = name

        self.propagation_delay = propagation_delay
        self.transmission_rate = transmission_rate
        self.receiver = None

        # Variables to maintain stats
        self.bandwidth = 100  # in bytes per second
        self.Pl = 0
        self.bandwidth_util = {}  # Buffer to store bandwidth util values 
        self.cwnd_values = {}  # Buffer to store cwnd values
        self.sender_rate = 0
    def udt_send(self, packt_to_be_sent, cwnd, RTT):
        # This function is called by the sending-side 
        # to send a new packet over the channel.
        self.sender_rate = cwnd / RTT
		
        self.bandwidth_util[self.env.now] = self.sender_rate / self.bandwidth
        self.cwnd_values[self.env.now] = cwnd
        packt = copy.copy(packt_to_be_sent)  # !!! BEWARE: Python uses pass-by-reference by default. Thus a copy() is necessary
        print("TIME:", self.env.now, self.name, ": udt_send called for", packt)
        # Start a process to deliver this packet across the channel.
        self.env.process(self.deliver_packet_over_channel(self.propagation_delay, packt, self.sender_rate))
		
    def deliver_packet_over_channel(self, propagation_delay, packt_to_be_delivered, sender_rate):
        packt = copy.copy(packt_to_be_delivered)
        
        if sender_rate > self.bandwidth:
            self.Pl = 1
        elif sender_rate < 0:
            self.Pl = 0
        else:
            self.Pl = 0.1

        if random.random() < self.Pl:
            print("TIME:", self.env.now, self.name, ":", packt, "was lost!")
        else:
            # If the packet isn't lost, it should reach the destination.
            # Now wait for "propagation_delay" amount of time
            yield self.env.timeout(propagation_delay)
            # Deliver the packet by calling the rdt_rcv()
            # function on the receiver side.
            self.receiver.rdt_rcv(packt)
