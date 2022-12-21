from ptc_file import PTCFile, to_bytes, md5
from ptc_file import PRG_TYPE, MEM_TYPE, CHR_TYPE, SCR_TYPE, COL_TYPE, GRP_TYPE, PTC_TYPES
from common import CHARS, MEM_CHARS, palettize, load_palette

import PIL
from PIL import Image, ImageDraw, ImageFont

def force_bytes_size(b, size):
	# pad zeros for small file
	b += (b"\0"*(size-len(b)))
	# TODO: maybe should throw warning or error?
	return b[:size]

def byte(n):
	return n.to_bytes(1, byteorder="little")

def create_internal_name(name):
	return name.replace("\\","/").split("/")[-1].split(".")[0].upper()[:8].encode()

def encode_ucs2(data):
	byte_str = b""
	for c in data:
		cc = ord(c)
		if c in MEM_CHARS:
			byte_str += c.encode("utf-16le")
#			byte_str += byte(MEM_CHARS.index(c)) + b'\0'
		elif c in CHARS:
			byte_str += byte(CHARS.index(c)) + b'\0'
		else:
			print(c, c.encode())
			raise Exception("Unknown character!")

	return byte_str

def encode_text(filename, type_str, internal_name):
	with open(filename, "r", encoding="utf-8", newline="") as f:
		data = list(f.read())
	
#	i = 0
#	while i < len(data):
		# find line ending if not set
#		if data[i] == '\n':
#			data[i] = '\r'
#		i += 1
	
	if type_str == PRG_TYPE:
		try:
			byte_data = bytes([CHARS.index(c) if c in CHARS else MEM_CHARS.index(c) for c in data])
		except ValueError as e:
			print("Error: File contains characters not known in PTC character set")
			raise e
	elif type_str == MEM_TYPE:
		# pad string and 
		byte_data = encode_ucs2(data)
		force_bytes_size(byte_data, 512)
		byte_data += to_bytes(len(data))
	
	return PTCFile(data=byte_data, type=type_str, name=internal_name)

def encode_chr(image, internal_name, palette):
	# prepare palette info
	pal = palettize(palette)
	pal = [[(pal[i][0],pal[i][1],pal[i][2],0)]+pal[i+1:i+16] for i in range(0,256,16)] #split into 16 palettes, first color is transparent
	print(pal)
	pal_maps = [{x:ix for ix, x in enumerate(sub)} | {x[:3]:ix for ix, x in enumerate(sub)} for sub in pal]
	# doubled map because (0,0,0) and (0,0,0,X) both may be checked due to differing image transparency
	# convert data to PTC format
	data = ""
	for cy in range(0,8):
		for cx in range(0,32):
			# determine palette of a single tile
			tile_cols = set()
			for py in range(0,8):
				for px in range(0,8):
					tile_cols.add(image.getpixel((px+8*cx, py+8*cy)))
			
			# find closest matching palette
			sub_map = pal_maps[0]
#			print(tile_cols)
			for sub in pal_maps:
				if tile_cols.issubset(sub): # if sub will work 100% as palette
					sub_map = sub
					break
				elif len(tile_cols.intersection(sub)) > len(tile_cols.intersection(sub_map)): # if sub works partially and better than previous palette
					sub_map = sub
					# don't break because there might be a better match
			
			# convert single CHR to data
			for py in range(0,8):
				for px in range(0,8,2):
					ph = image.getpixel((px+8*cx, py+8*cy))
					pl = image.getpixel((px+8*cx+1, py+8*cy))
					
					#map all unknown colors to transparent
					data += hex(sub_map[pl] if pl in sub_map else 0)[2] # remove 0x from hex output
					data += hex(sub_map[ph] if ph in sub_map else 0)[2] # remove 0x from hex output
	data = bytearray.fromhex(data)
	
	return PTCFile(data=data, type=CHR_TYPE, name=internal_name)

# see https://petitcomputer.fandom.com/wiki/GRP_File_Format_(External)
# for why there's a staircase of for loops
def encode_grp(image, internal_name, palette):
	pal = palettize(palette)
	pal_map = {x:ix for ix, x in enumerate(pal) if ix == pal.index(x)}
	pal_map = pal_map | {x[:3]:ix for ix, x in enumerate(pal)} # to fix stupid transparency errors
#	print(pal_map)
	#behold, the staircase
	data = []
	for by in range(0,3):
		for bx in range(0,4):
			for cy in range(0,8):
				for cx in range(0,8):
					for py in range(0,8):
						for px in range(0,8):
							p = image.getpixel((px+8*cx+64*bx, py+8*cy+64*by))
							# unknown colors become transparent
							data.append(pal_map[p] if p in pal_map else 0)
	
	return PTCFile(data=bytes(data), type=GRP_TYPE, name=internal_name)

def encode_col(image, internal_name):
	pal = palettize(image)
	data = b""
	for c in pal:
		# GGGRRRRR GBBBBBGG
		r = round(c[0] // 8)
		g = round(c[1] // 4)
		b = round(c[2] // 8)
		
		data += (r | ((g & 0b001110) << 4)).to_bytes(1, byteorder="little")
		data += (((g & 0b110000) >> 4) | (b << 2) | ((g & 0b000001) << 7)).to_bytes(1, byteorder="little")
	
	return PTCFile(data=data, type=COL_TYPE, name=internal_name)

def encode_scr(image, internal_name):
	# TODO:
	# how should tileset be passed?
	# how should palettes be implemented?
	raise NotImplementedError("SCR not yet supported")

def encode_image(image, type_str, internal_name, palette=None):
	SIZE_TO_TYPE = {
		(256,64):CHR_TYPE,
		(256,192):GRP_TYPE,
		(512,512):SCR_TYPE,
		(16,16):COL_TYPE,
		(256,1):COL_TYPE,
		(1,256):COL_TYPE,
	}
	if type_str is None:
		type_str = SIZE_TO_TYPE[(image.width, image.height)]
	
	palette = load_palette(palette, type_str)
	
	#TODO do encoding here for type
	if type_str == CHR_TYPE:
		return encode_chr(image, internal_name, palette)
	elif type_str == GRP_TYPE:
		return encode_grp(image, internal_name, palette)
	elif type_str == COL_TYPE:
		return encode_col(image, internal_name)
	elif type_str == SCR_TYPE:
		return encode_scr(image, internal_name)

def encode_graphic(filename, type_str, internal_name, palette=None):
	try:
		img = Image.open(filename)
		return encode_image(img, type_str, internal_name, palette)
	except PIL.UnidentifiedImageError as e:
		# not an image format: insert raw data instead
		if type_str is None:
			raise Exception("Image format not recognized and output type unspecified")
		with open(filename, "rb") as f:
			data = f.read()
		TYPE_TO_SIZE = {
			CHR_TYPE:8192,
			GRP_TYPE:49152,
			COL_TYPE:512,
			SCR_TYPE:8192
		}
		
		# pad zeros for small file, trim for large file
		data = force_bytes_size(data, TYPE_TO_SIZE[type_str])
		
		return PTCFile(data=data, type=type_str, name=internal_name)
		

def encode(filename, force_type=None, internal_name=None, palette=None):
	# allow short type names
	if force_type:
		for t in PTC_TYPES:
			if t[-3:] == force_type.encode():
				force_type = t
				break
	
	extension = filename.split(".")[-1]
	internal_name = create_internal_name(filename) if not internal_name else create_internal_name(internal_name)
	
	if force_type:
		if force_type == PRG_TYPE or force_type == MEM_TYPE:
			return encode_text(filename, force_type, internal_name, palette)
		else:
			return encode_graphic(filename, force_type, internal_name, palette)
	elif extension in ["txt"]:
		return encode_text(filename, PRG_TYPE, internal_name, palette)
	elif extension in ["png", "bmp", "gif"]:
		return encode_graphic(filename, force_type, internal_name, palette)
	else:
		raise Exception("Format type not specified and cannot be guessed")

