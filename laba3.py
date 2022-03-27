from inspect import Parameter
import struct, datetime, socket, time, sys



def get_fraction(number, precision):
		return int((number - int(number)) * 2 ** precision)

class NTPPacket:
	_FORMAT = "!B B b b 11I"

	def __init__(self, version_number=2, mode=3, transmit=0):
		
		#without correction
		self.leap_indicator = 0
		self.version_number = version_number 
		self.mode = mode
		self.stratum = 0
		self.pool = 0 
		self.precision = 0
		self.root_delay = 0
		self.root_dispersion = 0
		# Indicator of clocks (4 bytes)
		self.ref_id = 0
		# Last update time on server (8 bytes)
		self.reference = 0
		# Time of sending packet from local machine (8 bytes)
		self.originate = 0
		# Time of receipt on server (8 bytes)
		self.receive = 0
		# Time of sending answer from server (8 bytes)
		self.transmit = transmit
	 
	def __get_fraction(number, precision):
		return int((number - int(number)) * 2 ** precision)

	def pack(self):
		return struct.pack(NTPPacket._FORMAT,
                (self.leap_indicator << 6) + 
                    (self.version_number << 3) + self.mode,
                self.stratum,
                self.pool,
                self.precision,
                int(self.root_delay) + get_fraction(self.root_delay, 16),
                int(self.root_dispersion) + 
                    get_fraction(self.root_dispersion, 16),
                self.ref_id,
                int(self.reference),
                get_fraction(self.reference, 32),
                int(self.originate),
                get_fraction(self.originate, 32),
                int(self.receive),
                get_fraction(self.receive, 32),
                int(self.transmit),
                get_fraction(self.transmit, 32))
	
	def unpack(self, data: bytes):
		unpacked_data = struct.unpack(NTPPacket._FORMAT, data)

		self.leap_indicator = unpacked_data[0] >> 6  # 2 bits
		self.version_number = unpacked_data[0] >> 3 & 0b111  # 3 bits
		self.mode = unpacked_data[0] & 0b111  # 3 bits

		self.stratum = unpacked_data[1]  # 1 byte
		self.pool = unpacked_data[2]  # 1 byte
		self.precision = unpacked_data[3]  # 1 byte

		# 2 bytes | 2 bytes
		self.root_delay = (unpacked_data[4] >> 16) + \
			(unpacked_data[4] & 0xFFFF) / 2 ** 16
		# 2 bytes | 2 bytes
		self.root_dispersion = (unpacked_data[5] >> 16) + \
			(unpacked_data[5] & 0xFFFF) / 2 ** 16 

		# 4 bytes
		self.ref_id = str((unpacked_data[6] >> 24) & 0xFF) + " " + \
					  str((unpacked_data[6] >> 16) & 0xFF) + " " +  \
					  str((unpacked_data[6] >> 8) & 0xFF) + " " +  \
					  str(unpacked_data[6] & 0xFF)

		self.reference = unpacked_data[7] + unpacked_data[8] / 2 ** 32  # 8 bytes
		self.originate = unpacked_data[9] + unpacked_data[10] / 2 ** 32  # 8 bytes
		self.receive = unpacked_data[11] + unpacked_data[12] / 2 ** 32  # 8 bytes
		self.transmit = unpacked_data[13] + unpacked_data[14] / 2 ** 32  # 8 bytes

		return self


	def to_display(self):
		return "Leap indicator: {0.leap_indicator}\n" \
				"Version number: {0.version_number}\n" \
				"Mode: {0.mode}\n" \
				"Stratum: {0.stratum}\n" \
				"Pool: {0.pool}\n" \
				"Precision: {0.precision}\n" \
				"Root delay: {0.root_delay}\n" \
				"Root dispersion: {0.root_dispersion}\n" \
				"Ref id: {0.ref_id}\n" \
				"Reference: {0.reference}\n" \
				"Originate: {0.originate}\n" \
				"Receive: {0.receive}\n" \
				"Transmit: {0.transmit}"\
				.format(self)

	def get_time_different(self, arrive_time):
		return self.receive - self.originate - arrive_time + self.transmit

class NTPClient:
	server="pool.ntp.org"
	port=123


	def __init__(self):
		# Time difference between now and 1900, seconds
		self.FORMAT_DIFF = (datetime.date(1970, 1, 1) - datetime.date(1900, 1, 1)).days * 24 * 3600	
		self.packet = NTPPacket(version_number=2, mode=3, transmit=time.time() + self.FORMAT_DIFF)
		self.answer = NTPPacket()


	def get_time(self):    
		# Waiting time for recv (seconds)
		WAITING_TIME = 5
			
		
		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
			s.settimeout(WAITING_TIME)
			s.sendto(self.packet.pack(), (self.server, self.port))
			data = s.recv(48)
			arrive_time = time.time() + self.FORMAT_DIFF
			self.answer.unpack(data)

		time_different = self.answer.get_time_different(arrive_time)
		result = "Time difference: {}\nServer time: {}\n{}".format(
			time_different,
			datetime.datetime.fromtimestamp(time.time() + time_different).strftime("%c"),
			self.answer.to_display())
		return result


if __name__ == "__main__":

	userInput = ''
	client = NTPClient()
	
	while userInput != '--exit':
		userInput = input("Enter command: ")
		parameters_of_command = userInput.split()
		if (parameters_of_command.count == 3):
			client.server = parameters_of_command[1]
			client.port = int(parameters_of_command[2])
		if (parameters_of_command[0] == "get_time"):
			print(client.get_time())