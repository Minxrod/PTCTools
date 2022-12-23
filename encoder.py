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

def encode_text(args):
	filename, type_str, internal_name = args.source_file, args.force_type, args.internal_name
	
	with open(filename, "r", encoding="utf-8", newline="") as f:
		data = list(f.read())
	
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

def determine_palette(image, pal, pal_maps):
	# determine palette of a single tile
	tile_cols = set()
	for py in range(0,8):
		for px in range(0,8):
			tile_cols.add(image.getpixel((px, py)))
	
	# find closest matching palette
#	print(tile_cols)
	min_diff = 99999999
	sub_map = pal_maps[0]
	sub_i = -1
	sub_pal = pal[0]
	for i, sub in enumerate(pal_maps):
		if tile_cols.issubset(sub): # if sub will work 100% as palette
			sub_map = sub
			sub_pal = pal[i]
			sub_i = i
			break
		else:
			d = 0
			for c in tile_cols:
				close, diff = match_close_color(c, pal[i])
				d += diff
			if d < min_diff:
				min_diff = d
				sub_map = sub # colors on average were closer
				sub_pal = pal[i]
				sub_i = i
	print(sub_i)
	
	return sub_map, sub_pal, sub_i

def encode_single_chr(image, sub_map, sub_pal):
	sub_map = dict(sub_map) # to allow temp modifications for CHR
	# convert single CHR to data
	data = ""
	for py in range(0,8):
		for px in range(0,8,2):
			ph = image.getpixel((px, py))
			pl = image.getpixel((px+1, py))
			
			if pl in sub_map:
				data += hex(sub_map[pl])[2] # remove 0x from hex output
			else:
				close, d = match_close_color(pl, sub_pal)
				sub_map[pl] = close
				data += hex(sub_map[pl])[2]
			if ph in sub_map:
				data += hex(sub_map[ph])[2] # remove 0x from hex output
			else:
				close, d = match_close_color(ph, sub_pal)
				sub_map[ph] = close
				data += hex(sub_map[ph])[2]
	return data


def encode_chr(image, internal_name, palette, arrangement=None):
	arrangement = (1,1) if arrangement is None else tuple(int(x) for x in arrangement.split('x'))
	# prepare palette info
	pal = palettize(palette)
	pal = [[(pal[i][0],pal[i][1],pal[i][2],0)]+pal[i+1:i+16] for i in range(0,256,16)] #split into 16 palettes, first color is transparent
	print(pal)
	pal_maps = [{x:ix for ix, x in enumerate(sub)} | {x[:3]:ix for ix, x in enumerate(sub)} for sub in pal]
	# doubled map because (0,0,0) and (0,0,0,X) both may be checked due to differing image transparency
	# convert data to PTC format
	data = ""
	for cy in range(0,8,arrangement[1]):
		for cx in range(0,32,arrangement[0]):
			for sy in range(0,arrangement[1]):
				for sx in range(0,arrangement[0]):
					sub_image = image.crop((8*(cx+sx),8*(cy+sy),8*(cx+sx+1),8*(cy+sy+1)))
					sub_map, sub_pal, _ = determine_palette(sub_image, pal, pal_maps)
					data += encode_single_chr(sub_image, sub_map, sub_pal)
					
	data = bytearray.fromhex(data)
	
	return PTCFile(data=data, type=CHR_TYPE, name=internal_name)

def match_close_color(p, pal):
	#if p[3] == 0: print(0); return 0, 0 # transparency check
	diff = lambda c, p: (abs(c[0]-p[0])**2+abs(c[1]-p[1])**2+abs(c[2]-p[2])**2)
	
	min_diff = diff(p, pal[0])
	min_diff_i = 0
	for i,c in enumerate(pal):
		c_diff = diff(c, p)
		if c_diff < min_diff:
			min_diff = c_diff
			min_diff_i = i
#	print(p)
#	print(min_diff_i, min_diff, pal[min_diff_i])
	return min_diff_i, min_diff

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
							if p in pal_map:
								data.append(pal_map[p])
							else:
								close, d = match_close_color(p, pal)
#								print(d, end="")
								pal_map[p] = close # save closeness result
								data.append(close)
	
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

def encode_scr(image, internal_name, palette, tileset):
	pal = palettize(palette)
	pal = [[(pal[i][0],pal[i][1],pal[i][2],0)]+pal[i+1:i+16] for i in range(0,256,16)] #split into 16 palettes, first color is transparent
#	print(pal)
	pal_maps = [{x:ix for ix, x in enumerate(sub)} | {x[:3]:ix for ix, x in enumerate(sub)} for sub in pal]
	
	tiles = Image.open(tileset)
	
	chr_data = b""
	for i in range(0,tiles.height,64):
		chr_part_img = tiles.crop((0,i,256,i+64))
		chr_data += encode_chr(chr_part_img, b"SCR_TILE", palette).data
	# contains entire tileset
	
	scr_data = b""
	for y in range(0,image.height,256):
		for x in range(0,image.width,256):
			for cy in range(0,256,64):
				scr_part_img = image.crop((x,y+cy,x+256,y+cy+64))
				scr_data += encode_chr(scr_part_img, b"SCR_DATA", palette).data
	# scr_data contains SCR if it was converted to CHR
	
	data = b""
	chr_size = 32
	for i in range(0,len(scr_data),chr_size):
		scr_chr = scr_data[i:i+chr_size]
		loc = -1
		rot = 0
		chr_flip = 0x0
		while loc == -1:
			if rot == 0:
				scr_chunk = scr_chr
			elif rot == 1:
				# H flip
				chr_flip = 0x4
				dat = scr_chr.hex()
				newdat = ""
				for j in range(0,64,8):
					newdat += (dat[j:j+8])[::-1]
				scr_chunk = bytes.fromhex(newdat)
			elif rot == 2:
				# V flip
				chr_flip = 0x8
				scr_chunk = bytes.fromhex(scr_chr.hex()[::-1])
				dat = scr_chunk.hex()
				newdat = ""
				for j in range(0,64,8):
					newdat += (dat[j:j+8])[::-1]
				scr_chunk = bytes.fromhex(newdat)
			elif rot == 3:
				#HV flip
				chr_flip = 0xc
				scr_chunk = bytes.fromhex(scr_chr.hex()[::-1])
			else:
				raise Exception("Tile unidentified!")
			
			#TODO: Rotations?
			try:
				while loc & 0x001f:
					loc = chr_data.index(scr_chunk, loc+1)
			except ValueError as e:
				rot += 1
				print(scr_chunk.hex(), loc)
			
		chr_id = loc // 32
		
		j = i // 32
		by = j // 2048
		bx = j // 1024 % 2
		ty = j // 32 % 32
		tx = j % 32
		# find closest matching palette
		_, _, chr_pal = determine_palette(image.crop((8*tx+256*bx, 8*ty+256*by, 8*tx+256*bx+8, 8*ty+256*by+8)), pal, pal_maps)
		
		data += byte(chr_id & 0x00ff)
		data += byte((chr_pal << 4) | chr_flip | (chr_id >> 8))
	
	return PTCFile(data=data, type=SCR_TYPE, name=internal_name)
	# TODO:
	# how should tileset be passed?
	# how should palettes be implemented?
	

def encode_image(image, args):
	SIZE_TO_TYPE = {
		(256,64):CHR_TYPE,
		(256,192):GRP_TYPE,
		(512,512):SCR_TYPE,
		(16,16):COL_TYPE,
		(256,1):COL_TYPE,
		(1,256):COL_TYPE,
	}
	type_str = args.force_type if args.force_type else SIZE_TO_TYPE[(image.width, image.height)]
	palette = load_palette(args.palette, type_str)
	
	#TODO do encoding here for type
	if type_str == CHR_TYPE:
		return encode_chr(image, args.internal_name, palette, args.arrangement)
	elif type_str == GRP_TYPE:
		return encode_grp(image, args.internal_name, palette)
	elif type_str == COL_TYPE:
		return encode_col(image, args.internal_name)
	elif type_str == SCR_TYPE:
		return encode_scr(image, args.internal_name, palette, args.tileset)

def encode_graphic(args):
	try:
		img = Image.open(args.source_file)
		return encode_image(img, args)
	except PIL.UnidentifiedImageError as e:
		# not an image format: insert raw data instead
		if args.force_type is None:
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
		data = force_bytes_size(data, TYPE_TO_SIZE[args.force_type])
		
		return PTCFile(data=data, type=args.force_type, name=args.internal_name)

def encode(args):
	extension = args.source_file.split(".")[-1]
	
	# allow short type names
	if args.force_type:
		for t in PTC_TYPES:
			if t[-3:] == args.force_type.encode():
				args.force_type = t
				break
	# prepare internal name
	args.internal_name = create_internal_name(args.source_file) if not args.internal_name else create_internal_name(args.internal_name)
	
	if args.force_type:
		if args.force_type == PRG_TYPE or args.force_type == MEM_TYPE:
			return encode_text(args)
		else:
			return encode_graphic(args)
	elif extension in ["txt"]:
		args.force_type = PRG_TYPE
		return encode_text(args)
	elif extension in ["png", "bmp", "gif"]:
		return encode_graphic(args)
	else:
		raise Exception("Format type not specified and cannot be guessed")

