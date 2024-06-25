
# Congestion control algorithms
#
# Author: Devyani Remulkar
# Date: 23 April 2024
import simpy
import random
import sys
from Packet import Packet  # Assuming Packet class is defined elsewhere


class TCP_Sender(object):
    
    def __init__(self, env):
        self.env = env 
        self.channel = None

        # Parameters
        self.MSS = 16  # Length of data in bytes (1 MSS)
        self.InitialSeqNumber = 0
        self.NextSeqNum = 0
        self.SendBase = self.InitialSeqNumber
        self.cwnd = self.MSS  # Initial congestion window size
        self.ssthresh = float('inf')  # Initialize slow start threshold to infinity
        self.dupACKcount = 0
        self.RTT = 4
        self.ack_num = 0
        self.a1 = 1
        self.b1 = 1
        self.a2 = 0
        self.b2 = 0.5
        self.cwnd_inc=0
        # States
        self.Slow_start_state = 0
        self.Congestion_Avoidance_state = 1
        self.Fast_recovery_state = 2
        self.state = self.Slow_start_state
        self.send = True
        self.Resend_SeqNum=0
        # Other variables to maintain sender-side statistics
        self.total_packets_sent = 0
        self.num_retransmissions = 0
        
        # Timer related variables
        self.timeout_value = 5  # Timeout value in seconds
        self.timer = {}  # Store timer for current packet
        self.timer_is_running = False

        # Packet buffer and timers
        self.pkt_buffer = {}
        #self.timers = {}

    def rdt_send(self, data):
        if self.NextSeqNum+16 - self.SendBase <= self.cwnd:
            
            
            return self.send_segment(data)
        else:
            print("Sequence number outside current window")
            if(self.Resend_SeqNum != self.NextSeqNum and (not self.send)):
                while self.Resend_SeqNum+16 - self.SendBase <= self.cwnd and self.Resend_SeqNum != self.NextSeqNum:
                    self.retransmit_segment(self.Resend_SeqNum)
                    self.Resend_SeqNum += 16
            else:
                self.send = True

            return False

    def send_segment(self, data):
        # Create a TCP segment
        if(self.Resend_SeqNum != self.NextSeqNum and (not self.send)):
                while self.Resend_SeqNum+16 - self.SendBase <= self.cwnd and self.Resend_SeqNum != self.NextSeqNum:
                    self.retransmit_segment(self.Resend_SeqNum)
                    self.Resend_SeqNum += 16
                self.send = True
        if self.send:
            segment = Packet(seq_num=self.NextSeqNum, payload=data, packet_length=self.MSS)
            # Pass segment to IP
            self.channel.udt_send(segment, self.cwnd, self.RTT)
            # Store segment in buffer
            self.total_packets_sent += 1
            self.pkt_buffer[self.NextSeqNum] = segment
            # Update sequence number
            self.NextSeqNum += 16
            if not self.timer:
                self.start_timer(0)
            return True
        else:
            return False
    
    def timer_behavior(self, seq_num):
        try:
            # Wait for timeout 
            self.timer_is_running = True
            yield self.env.timeout(self.timeout_value)
            self.timer_is_running = False
            # Take some actions 
            self.on_timeout(seq_num)
        except simpy.Interrupt:
            # Stop the timer
            self.timer_is_running = False
    
    def start_timer(self, seq_num):
        # Start the timer for the given sequence number
        if seq_num not in self.timer:
            self.timer[seq_num] = self.env.process(self.timer_behavior(seq_num))
            print("TIME:", self.env.now, "TIMER STARTED with a timeout of", self.timeout_value)
        else:
            print("TIME:", self.env.now, "TIMER ALREADY RUNNING ")
    
    def stop_timer(self, seq_num):
        # Stop the timer for the given sequence number
        if seq_num in self.timer:
            if not self.timer[seq_num].triggered:
                self.timer[seq_num].interrupt()
                print("TIME:", self.env.now, "TIMER STOPPED")
                del self.timer[seq_num]
            else:
                print("TIME:", self.env.now, "TIMER ALREADY TRIGGERED for current window")
        else:
            print("TIME:", self.env.now, "TIMER NOT FOUND")

    def on_timeout(self, seq_num):
        #self.ssthresh = self.cwnd / 2
        self.ssthresh = self.a2+self.b2*self.cwnd
        self.send = False
        self.cwnd = self.MSS
        self.dupACKcount = 0
        self.state = self.Slow_start_state
        del self.timer[seq_num]
        self.start_timer(0)
        print("Slow start starts")
        self.Resend_SeqNum = self.SendBase
        

    def rdt_rcv(self, packt):
        self.ack_num = packt.seq_num
        if self.ack_num > self.SendBase:
            self.stop_timer(0)
            while self.SendBase < self.ack_num:
                del self.pkt_buffer[self.SendBase]
                self.SendBase += 16
            
            if self.state == self.Slow_start_state:
                self.cwnd += self.MSS
                self.dupACKcount = 0
                if self.cwnd >= self.ssthresh:
                    self.state = self.Congestion_Avoidance_state
                    print("Congestion Avoidance starts")
                    self.cwnd_inc=0
            elif self.state == self.Congestion_Avoidance_state:
                #self.cwnd_inc += self.MSS * (self.MSS / self.cwnd)
                self.cwnd_inc += self.a1*self.MSS*(self.MSS/self.cwnd)
                if(self.cwnd_inc ==self.a1*self.MSS ):
                    #self.cwnd+=self.cwnd_inc
                    self.cwnd=self.cwnd_inc + self.b1*self.cwnd
                    self.cwnd_inc=0
                self.dupACKcount = 0
            if self.state==self.Fast_recovery_state:
                self.cwnd = self.ssthresh
                self.dupACKcount = 0
                self.state = self.Congestion_Avoidance_state
                print("Congestion Avoidance starts")
            if self.pkt_buffer:
                self.start_timer(0)
        else:
            self.handle_dup_ack(self.ack_num)

    def handle_dup_ack(self, ack_num):
        self.dupACKcount += 1
        if self.state == self.Fast_recovery_state:
            self.cwnd += self.MSS
        elif self.dupACKcount == 3 and self.state != self.Fast_recovery_state:
            self.ssthresh = self.cwnd / 2
            #self.ssthresh = self.a2+self.b2*self.cwnd
            self.cwnd = self.ssthresh + 3 * self.MSS
            print(self.cwnd)
            self.stop_timer(0)
            self.start_timer(0)
            self.state = self.Fast_recovery_state
            print("Fast recovery starts")
            self.retransmit_segment(self.ack_num)
            
    def retransmit_segment(self, seq_num):
        self.num_retransmissions += 1
        self.total_packets_sent += 1
        if seq_num in self.pkt_buffer:
            self.channel.udt_send(self.pkt_buffer[seq_num], self.cwnd, self.RTT)
            print("packet resent")
        
    def print_status(self):
        print("TIME:", self.env.now, "Current window:", self.cwnd/self.MSS,"MSS base =", self.SendBase, "nextseqnum =", self.NextSeqNum)
        print("---------------------")

class TCP_Receiver(object):
    
    def __init__(self, env):
        
        # Initialize variables
        self.env = env 
        self.receiving_app = None
        self.channel = None

        # Some default parameter values
        self.ack_packet_length = 16  # bytes
        #self.K = 16  # Range of sequence numbers expected

        # Initialize state variables
        self.expectedseqnum = 0
        self.packet_number = 0
        #self.receiving_window = 16  # Receiver's Window size
        
        self.sndpkt = Packet(seq_num=0, payload="ACK", packet_length=self.ack_packet_length)
        self.total_packets_sent = 0
        
        self.received_packets = {}  # Buffer to store received packets 

    def rdt_rcv(self, packt):
        # This function is called by the lower-layer when a packet arrives at the receiver
        # Store the received packet in the buffer
        self.received_packets[self.expectedseqnum] = packt
        
        if(packt.seq_num == self.expectedseqnum):
            # Move the window ahead if the first packet in the window is received
            while self.expectedseqnum in self.received_packets:
                self.receiving_app.deliver_data(self.received_packets[self.expectedseqnum].payload)
                del self.received_packets[self.expectedseqnum]
                self.packet_number -= 1
                self.expectedseqnum  += 16
        else:
            self.packet_number += 1
            
        print("TIME:", self.env.now, "RDT_RECEIVER: got packet", packt.seq_num, ". Sent ACK", self.expectedseqnum)
        # Send acknowledgment for the received packet
        self.sndpkt = Packet(seq_num=self.expectedseqnum, payload="ACK", packet_length=self.ack_packet_length)
        self.channel.udt_send(self.sndpkt, -1, 1)
        self.total_packets_sent += 1
