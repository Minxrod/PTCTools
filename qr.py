import zlib
from math import ceil

import qrcode

from ptc_file import PTCFile, to_bytes, md5
from PIL import Image, ImageDraw, ImageFont


# shoutouts to this document here for all of the information
# https://gist.github.com/ajc2/25258be3296847bc55cec9e27d13f053
def create_qr(args):
	ptc_file = args.source_file
	output = args.output
	
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
	
	if args.merge:
		merge(output+"#merged.png", [output+"#qr"+format(i, "03d")+".png" for i in range(1,max_qrs+1)], not args.no_index)

def merge(output, names, indexed):
	wcount = min(5,len(names))
	hcount = ceil(len(names)/5)
	
	img = Image.open(names[0])
	
	# this img is from the last QR code above.
	# (It doesn't matter which one is used, they're all the same size)
	
	mergewidth = img.width * wcount
	mergeheight = img.height * hcount
	
	mergeimg = Image.new("RGBA", (mergewidth, mergeheight), (255,255,255,255))
	mergedraw = ImageDraw.Draw(mergeimg)
	font = ImageFont.load_default().font
	
	for i in range(1,len(names)+1):
		img = Image.open(names[i-1])
		x = ((i-1) % 5) * img.width
		y = ((i-1) // 5) * img.height
		mergeimg.paste(img, (x, y))
		if indexed:
			mergedraw.text((x + img.width / 2, y + img.height - 15), str(i)+"/"+str(len(names)), font=font, fill=(0,0,0,255))
#			print("Merging " + str(i))
		img.close()
	mergeimg.save(output)

