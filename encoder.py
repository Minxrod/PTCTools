from ptc_file import PTCFile, PRG_TYPE

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
