from ptc_file import PTCFile, to_bytes, md5
from ptc_file import PRG_TYPE, MEM_TYPE
import qrcode
import zlib
from math import ceil

CR=ord('\r')

CHARS =  "\0🅐🅑����☺☻⇥★🖛🅻\r��♪♫🆁��🭽🭶🭾🅧🅨⭗�⭢⭠⭡⭣"
CHARS += "".join([chr(c) for c in range(32,128)])
CHARS += "◇▘▝▀▖▌▞▛▗▚▐▜▄▙▟█┻┳┣╋┫━┃█┏┓┗┛◢◣◥◤"
CHARS += "～。「」、・ヲァィゥェォャュョッーアイウエオカキクケコサシスセソ"
CHARS += "タチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン゛゜"
CHARS += "■●▲▼□○△▽��������♠♥♦♣🯅���▔▏▕▁╱╲╳▒"


def create_internal_name(name):
	return name.replace("\\","/").split("/")[-1].split(".")[0].upper()[:8].encode()

def encode_text(filename, line_end=None, internal_name=None):
	with open(filename, "r", encoding="utf-8") as f:
		data = list(f.read())
	
	if not internal_name:
		internal_name = create_internal_name(filename)
	
	# line ending conversion
	if not line_end:
		i = 0
		while i < len(data):
			# find line ending if not set
			if data[i] == '\n':
				data[i] = '\r'
			i += 1
		# line_end may be None if this is a MEM type being converted with no newlines, for example
	
	try:
		byte_data = bytes([CHARS.index(c) for c in data])
	except ValueError as e:
		print("Error: File contains characters not known in PTC character set")
		raise e
	
	return PTCFile(data=byte_data, type=PRG_TYPE, name=internal_name)

def encode(filename, output, line_ending, force_type=None):
	extension = filename.split(".")[-1]
	if extension in ["txt"]:
		return encode_text(filename, line_ending, output)
	elif extension in ["png", "bmp"]:
		return encode_image(filename, output)
	elif force_type:
		return encode_text(filename, output)
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
		with open(output, "w") as f:
			if ptc.type_str == PRG_TYPE:
				s = decode_text(ptc.data)
				f.write(s)
			elif ptc.type_str == MEM_TYPE:
				s = decode_text(ptc.data.decode("usc2"))
				f.write(s)
		
	
# shoutouts to this document here for all of the information
# https://gist.github.com/ajc2/25258be3296847bc55cec9e27d13f053
def create_qr(ptc_file):
	ptc = PTCFile(file=ptc_file)
	
	qrs = qrcode.QRCode(
		version=20,
		error_correction=qrcode.constants.ERROR_CORRECT_M,
		border=4,
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
	print(max_qrs)
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
		img.save("qr"+format(i, "03d")+".png")
#		print(i, img)
#		img.show()
#		print(chunk)

