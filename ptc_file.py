import hashlib
from math import ceil

PTC_PX01 = 0x0
PTC_SIZE_AFTER_MD5 = 0x4
PTC_TYPE = 0x8
PTC_FILENAME = 0xc
PTC_MD5 = 0x14
PTC_TYPE_STR = 0x24
PTC_DATA = 0x30
PTC_HEADER_SIZE = 0x30

PTC_PRG_PACKAGE_HIGH = 0x30
PTC_PRG_PACKAGE = 0x34
PTC_PRG_SIZE = 0x38
PTC_PRG_DATA = 0x3c
PTC_PRG_HEADER_SIZE = 0x0c

PX01 = b"PX01"
MD5_PREFIX = b"PETITCOM"

PRG_TYPE = b"PETC0300RPRG"
MEM_TYPE = b"PETC0200RMEM"
GRP_TYPE = b"PETC0100RGRP"
CHR_TYPE = b"PETC0100RCHR"
SCR_TYPE = b"PETC0100RSCR"
COL_TYPE = b"PETC0100RCOL"

# index = type id
PTC_TYPES = [PRG_TYPE, MEM_TYPE, GRP_TYPE, CHR_TYPE, SCR_TYPE, COL_TYPE]

def to_number(bin_str):
	return int.from_bytes(bin_str, byteorder="little")

def to_bytes(number):
	return number.to_bytes(4, byteorder="little")

def md5(data):
	return hashlib.md5(data).digest()

class PTCFile:
	def _from_sd_file(self, filename):
		with open(filename,"rb") as f:
			self._sd_data = f.read()
			
		size = to_number(self._sd_data[PTC_SIZE_AFTER_MD5:PTC_SIZE_AFTER_MD5+4])
		self.size = 4*ceil(size/4) # pad to nearest 4
		self.type_id = to_number(self._sd_data[PTC_TYPE:PTC_TYPE+4])
		self.filename = self._sd_data[PTC_FILENAME:PTC_FILENAME+8]
		self.md5 = self._sd_data[PTC_MD5:PTC_MD5+16]
		self.type_str = self._sd_data[PTC_TYPE_STR:PTC_TYPE_STR+12]
		if (self.type_id): # Other resources
			self.data = self._sd_data[PTC_DATA:]
		else: # PRG type
			self.package = self._sd_data[PTC_PRG_PACKAGE_HIGH:PTC_PRG_PACKAGE_HIGH+8]
			self.prg_size = to_number(self._sd_data[PTC_PRG_SIZE:PTC_PRG_SIZE+4])
			self.prg_data = self._sd_data[PTC_PRG_DATA:PTC_PRG_DATA+self.prg_size]
			self.data = self._sd_data[PTC_PRG_DATA:]
	
	def _from_data(self, data, ptc_type, name):
		self.data = data # keep copy of old data
		while len(self.data) % 4:
			self.data += b"\0" # pad zeros until multiple of 4
		
		# NOTE: size depends on file size and therefore includes padding
		# prg_size is just based on program size and does not include padding
		self.size = len(self.data) + len(ptc_type)
		if ptc_type == PRG_TYPE:
			self.size += PTC_PRG_HEADER_SIZE
		self.type_str = ptc_type
		self.type_id = PTC_TYPES.index(ptc_type)
		self.filename = (name+b"\0"*8)[:8]
		if ptc_type == PRG_TYPE:
			self.package = b"\0"*8
			self.prg_data = self.data
			self.prg_size = len(data)
		self.md5 = md5(MD5_PREFIX + self.get_internal_file())
	
	def __init__(self, *, file=None, data=None, type=None, name=None):
		""" 
		Note: Expects SD file name or raw bytes.
		"""
		if data is not None:
			self._from_data(data, type, name)
		elif file:
			self._from_sd_file(file)
		else:
			raise Exception("Invalid constructor" + str([file,data,type,name]))
	
	def write_file(self, output):
		with open(output+".PTC", "wb") as f:
			f.write(PX01)
			f.write(to_bytes(self.size))
			f.write(to_bytes(self.type_id))
			f.write(self.filename)
			f.write(self.md5)
			f.write(self.type_str)
			if self.type_str == PRG_TYPE:
				f.write(self.package)
				f.write(to_bytes(self.prg_size))
			f.write(self.data)
	
	def __str__(self):
		s = (self.filename.replace(b"\0",b"").decode() + 
			"\nType: " + self.type_str[-3:].decode() + 
			"\nSize: " + str(self.size) + 
			"\nMD5: " + self.md5.hex()
		)
		return s
	
	def set_package_str(self, package_bits):
		if package_bits >= 0x200000000000:
			raise Exception("Invalid package string!")
		self.package = to_bytes((package_bits & 0x00001fff00000000) >> 32) + to_bytes(package_bits & 0x00000000ffffffff)
	
	def get_internal_file(self):
		if self.type_str == PRG_TYPE:
			return self.type_str + self.package + to_bytes(self.prg_size) + self.data
		else:
			return self.type_str + self.data
		
	def get_internal_name(self):
		return self.filename
	
	def get_internal_type_id(self):
		return to_bytes(self.type_id)
