# This is a Python class for a Packet.
#
# A packet has the following members:
#
#	payload: the data contained in the packet,
#	packet_length: length of the entire packet (in bits)
#	seq_num: the packet sequence number,
#	
#	
#
# Author: Devyani Remulkar


class Packet(object):
	
	def __init__(self,payload,packet_length,seq_num):
		self.payload=payload
		self.packet_length=packet_length
		self.seq_num = seq_num
		#self.corrupted=False
	
	# this function can be called
	# to mark a packet as "corrupted".
	

	# this function can be used to print a packet
	def __str__(self):
		return "Packet(seq_num=%d, payload=%s, packet_length=%d bytes)"% (self.seq_num, self.payload, self.packet_length)

