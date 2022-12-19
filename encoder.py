from ptc_file import PTCFile, PRG_TYPE, to_bytes, md5
import qrcode
import zlib
from math import ceil

def create_internal_name(name):
	return name.replace("\\","/").split("/")[-1].split(".")[0].upper()[:8].encode()

def encode_text(filename, internal_name=None):
	with open(filename,"rb") as f:
		data = f.read()
	
	if not internal_name:
		internal_name = create_internal_name(filename)
	
	return PTCFile(data=data, type=PRG_TYPE, name=internal_name)

def encode(filename, output, force_type=None):
	extension = filename.split(".")[-1]
	if extension in ["txt"]:
		return encode_text(filename, output)
	elif extension in ["png", "bmp"]:
		return encode_image(filename, output)
	elif force_type:
		return encode_text(filename, output)
	else:
		raise Exception("Format type not specified and cannot be guessed")
	
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

