# Simulation Testbench
#
# Author: Devyani Remulkar
# Date: 23 April 2024

import simpy
from Applications import SendingApplication,ReceivingApplication
from Channel import UnreliableChannel
from Protocol_TCP import TCP_Sender, TCP_Receiver
import matplotlib.pyplot as plt

# Create a simulation environment
env=simpy.Environment()


# Populate the simulation environment with objects:
sending_app	  = SendingApplication(env,sending_interval=1)
receiving_app = ReceivingApplication(env)
rdt_sender	  = TCP_Sender(env=env)
rdt_receiver  = TCP_Receiver(env=env)
# create the DATA and ACK channels and set channel parameters
channel_for_data  = UnreliableChannel(env=env,name="DATA_CHANNEL", propagation_delay=2, transmission_rate=1000)
channel_for_ack	  = UnreliableChannel(env=env,name="ACK_CHANNEL", propagation_delay=2, transmission_rate=1000)


# Set some parameters for the Go-Back-N Protocol

rdt_sender.timeout_value=5	# Timeout value for the sender
rdt_sender.data_packet_length=16 # length of the DATA packet in bytes
rdt_receiver.ack_packet_length=16 # length of the ACK packet in bytes


# connect the objects together
# .....forward path...
sending_app.rdt_sender = rdt_sender
rdt_sender.channel = channel_for_data
channel_for_data.receiver = rdt_receiver
rdt_receiver.receiving_app = receiving_app
# ....backward path...for acks
rdt_receiver.channel = channel_for_ack
channel_for_ack.receiver = rdt_sender


# Run simulation, and print status information every now and then.
# Run the simulation until TOTAL_SIMULATION_TIME elapses OR the receiver receives a certain 
# number of messages in total, whichever occurs earlier.
TOTAL_SIMULATION_TIME = 300 # <==== Total simulation time. Increase it as you like.
t = 0
while t < TOTAL_SIMULATION_TIME:
    if env.peek() > t:
        rdt_sender.print_status()
    env.step()
    t = int(env.now)
    # We may wish to halt the simulation if some condition occurs.
    # For example, if the receiving application receives 100 messages.
    num_msg = receiving_app.total_messages_received
    if num_msg >= 1000:  # <=== Halt simulation when receiving application receives these many messages.
        print("\n\nReceiving application received", num_msg, "messages. Halting simulation.")
        break
    if t == TOTAL_SIMULATION_TIME:
        print("\n\nTotal simulation time has elapsed. Halting simulation.")


# print some statistics at the end of simulation:
print("===============================================")
print(" SIMULATION RESULTS:")
print("===============================================")

print("Total number of messages sent by the Sending App= %d"%sending_app.total_messages_sent)
print("Total number of messages received by the Receiving App=%d"%receiving_app.total_messages_received)

print("Total number of DATA packets sent by rdt_Sender=%d"%rdt_sender.total_packets_sent)
print("Total number of re-transmitted DATA packets=%d (%0.2f%% of total packets sent)"%(rdt_sender.num_retransmissions,(rdt_sender.num_retransmissions/rdt_sender.total_packets_sent*100.0)))

print("Total number of ACK packets sent by rdt_Receiver=%d"%rdt_receiver.total_packets_sent)

keys=channel_for_data.bandwidth_util.keys()
values=channel_for_data.bandwidth_util.values()

keys1=channel_for_data.cwnd_values.keys()
values1=channel_for_data.cwnd_values.values()

plt.figure()
plt.plot(keys, values)
plt.xlabel('Time')
plt.ylabel('Bandwidth Utilization')
plt.show()

# Plot for keys1 and values1
plt.figure()
plt.plot(keys1, values1)
plt.xlabel('Time')
plt.ylabel('CWND')
plt.show()
#print("Total number of re-transmitted ACK packets=%d (%0.2f%% of total packets sent)"%(rdt_receiver.num_retransmissions,(rdt_receiver.num_retransmissions/rdt_receiver.total_packets_sent*100.0)))

#print("Bandwidth Utilization for the DATA channel=%0.2f%%"%(channel_for_data.channel_utilization_time/t*100.0))
#print("Utilization for the  ACK channel=%0.2f%%"%(channel_for_ack.channel_utilization_time/t*100.0))



