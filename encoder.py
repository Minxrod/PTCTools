import qrcode
import zlib
from math import ceil
import PIL
from PIL import Image, ImageDraw, ImageFont

from ptc_file import PTCFile, to_bytes, md5
from ptc_file import PRG_TYPE, MEM_TYPE, CHR_TYPE, SCR_TYPE, COL_TYPE, GRP_TYPE

CHARS =  "\0🅐🅑����☺☻⇥★🖛🅻\r��♪♫🆁��🭽🭶🭾🅧🅨⭗�⭢⭠⭡⭣"
CHARS += "".join([chr(c) for c in range(32,128)])
CHARS += "◇▘▝▀▖▌▞▛▗▚▐▜▄▙▟█┻┳┣╋┫━┃█┏┓┗┛◢◣◥◤"
CHARS += "～。「」、・ヲァィゥェォャュョッーアイウエオカキクケコサシスセソ"
CHARS += "タチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン゛゜"
CHARS += "■●▲▼□○△▽��������♠♥♦♣🯅���▔▏▕▁╱╲╳▒"


def create_internal_name(name):
	return name.replace("\\","/").split("/")[-1].split(".")[0].upper()[:8].encode()

def encode_text(filename, type_str, internal_name):
	with open(filename, "r", encoding="utf-8") as f:
		data = list(f.read())
	
	i = 0
	while i < len(data):
		# find line ending if not set
		if data[i] == '\n':
			data[i] = '\r'
		i += 1
	
	try:
		byte_data = bytes([CHARS.index(c) for c in data])
	except ValueError as e:
		print("Error: File contains characters not known in PTC character set")
		raise e
	
	return PTCFile(data=byte_data, type=type_str, name=internal_name)

def palettize(image):
	pal_array = []
	for y in range(0,image.height):
		for x in range(0,image.width):
			pal_array.append(image.getpixel((x,y)))
	return pal_array

def encode_chr(image, internal_name, palette):
	# prepare palette info
	pal = palettize(palette)
	pal = [pal[i:i+16] for i in range(0,256,16)] #split into 16 palettes
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
	print(pal_map)
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

# https://petitcomputer.fandom.com/wiki/COLSET_(Command)
# not checking this [yet], assuming it's accurate
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

def encode_image(image, type_str, internal_name, palette=None):
	SIZE_TO_TYPE = {
		(256,64):CHR_TYPE,
		(256,192):GRP_TYPE,
		(512,512):SCR_TYPE,
		(16,16):COL_TYPE,
	}
	if type_str is None:
		type_str = SIZE_TO_TYPE[(image.width, image.height)]
	
	if palette is None and (type_str == CHR_TYPE or type_str == SCR_TYPE):
		# open default CHR palette and use that
		palette = "col_bgsp.png"
	elif palette is None and type_str == GRP_TYPE:
		# open default GRP palette
		palette = "col_grp.png"
	# open provided palette
	if palette:
		palette = Image.open(palette)
	
	#TODO do encoding here for type
	if type_str == CHR_TYPE:
		return encode_chr(image, internal_name, palette)
	elif type_str == GRP_TYPE:
		return encode_grp(image, internal_name, palette)
	elif type_str == COL_TYPE:
		return encode_col(image, internal_name)


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
		return PTCFile(data=data, type=type_str, name=internal_name)
		

def encode(filename, force_type=None, internal_name=None):
	extension = filename.split(".")[-1]
	internal_name = create_internal_name(filename) if not internal_name else create_internal_name(internal_name)
	
	if extension in ["txt"]:
		return encode_text(filename, PRG_TYPE, internal_name)
	elif extension in ["png", "bmp", "gif"]:
		return encode_graphic(filename, force_type, internal_name)
	elif force_type:
		if force_type == PRG_TYPE or force_type == MEM_TYPE:
			return encode_text(filename, force_type, internal_name)
		else:
			return encode_graphic(filename, force_type, internal_name)
	else:
		raise Exception("Format type not specified and cannot be guessed")

def decode_text(data):
	unicode_str = ""
	for c in data:
		if c > 0 and c < 256:
			unicode_str += CHARS[c]
		elif c >= 256:
			unicode_str += c
	return unicode_str

def decode(filename, output):
	"""
	Newlines are converted to LF.
	"""
	ptc = PTCFile(file=filename)
	if ptc.type_str == PRG_TYPE or ptc.type_str == MEM_TYPE:
		with open(output+".txt", "w") as f:
			if ptc.type_str == PRG_TYPE:
				s = decode_text(ptc.data)
				f.write(s)
			elif ptc.type_str == MEM_TYPE:
				s = decode_text(ptc.data.decode("usc2"))
				f.write(s)
		
	
# shoutouts to this document here for all of the information
# https://gist.github.com/ajc2/25258be3296847bc55cec9e27d13f053
def create_qr(ptc_file, output, merge):
	ptc = PTCFile(file=ptc_file)
	
	qrs = qrcode.QRCode(
		version=20,
		error_correction=qrcode.constants.ERROR_CORRECT_M,
		border=10,
		box_size=2,
	)

	compressed = zlib.compress(ptc.get_internal_file())

	data = ptc.filename
	data += ptc.type_str[8:]
	data += to_bytes(len(compressed))
	data += to_bytes(ptc.size)
	data += compressed

	#https://www.qrcode.com/en/about/version.html#versionPage11_20
	#TODO: variable size qrs?
	chunk_size = 666 #997
	segment_size = chunk_size - 36

	chunks = []
	max_qrs = ceil(len(data)/segment_size)
#	print(max_qrs)
	for i in range(1,max_qrs+1):
		chunk = b"PT"
		chunk += to_bytes(i)[0:1]
		chunk += to_bytes(max_qrs)[0:1] # max qrs
		segment = data[(i-1)*segment_size:i*segment_size]
		chunk += md5(segment)
		chunk += md5(data)
		chunk += segment
		chunks.append(chunk)
		
		qrs.clear()
		qrs.add_data(chunk, optimize=0)
		qrs.make(fit=False)
		
		img = qrs.make_image()
		img.save(output+"#qr"+format(i, "03d")+".png")
#		print(i, img)
#		img.show()
#		print(chunk)
	
	if merge:
		wcount = min(5,max_qrs)
		hcount = ceil(max_qrs/5)
		
		img = Image.open(output+"#qr001.png")
		
		# this img is from the last QR code above.
		# (It doesn't matter which one is used, they're all the same size)
		
		mergewidth = img.width * wcount
		mergeheight = img.height * hcount
		
		mergeimg = Image.new("RGBA", (mergewidth, mergeheight), (255,255,255,255))
		mergedraw = ImageDraw.Draw(mergeimg)
		font = ImageFont.load_default().font
		
		for i in range(1,max_qrs+1):
			img = Image.open(output+"#qr"+format(i, "03d")+".png")
			x = ((i-1) % 5) * img.width
			y = ((i-1) // 5) * img.height
			mergeimg.paste(img, (x, y))
			mergedraw.text((x + img.width / 2, y + img.height - 15), str(i)+"/"+str(max_qrs), font=font, fill=(0,0,0,255))
#			print("Merging " + str(i))
			img.close()
		mergeimg.save(output+"#merged.png")
		

