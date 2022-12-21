from ptc_file import PTCFile
from ptc_file import PRG_TYPE, MEM_TYPE, CHR_TYPE, SCR_TYPE, COL_TYPE, GRP_TYPE, PTC_TYPES

from common import CHARS, MEM_CHARS, load_palette, palettize

import PIL
from PIL import Image
from encoder import load_palette, palettize, CHARS, MEM_CHARS

def decode_text(data):
	"""
	Expects list of ints in [0,255] or bytes object
	"""
	unicode_str = ""
	for c in data:
		unicode_str += CHARS[c] if CHARS[c] != "�" else MEM_CHARS[c]
	return unicode_str

def decode_grp(ptc, output, pal):
	grp_img = Image.new("RGBA",(256,192))
	for i, p in enumerate(ptc.data):
		by = i // 16384
		bx = i // 4096 % 4
		cy = i // 512 % 8
		cx = i // 64 % 8
		py = i // 8 % 8
		px = i % 8
		grp_img.putpixel((px+8*cx+64*bx, py+8*cy+64*by), pal[p])
	grp_img.save(output+".png")

def decode_chr(ptc, output, pal):
	chr_img = Image.new("RGBA",(256,64))
	for i, p in enumerate(ptc.data):
		cy = i // 1024
		cx = i // 32 % 32
		py = i // 4 % 8
		px = i % 4
		chr_img.putpixel((2*px+8*cx, py+8*cy), pal[p & 0x0f])
		chr_img.putpixel((2*px+1+8*cx, py+8*cy), pal[(p & 0xf0) >> 4])
	chr_img.save(output+".png")

def decode_col(ptc, output):
	col_img = Image.new("RGBA",(16,16))
	for i in range(0,512,2):
		# gBBBBBGG GGGRRRRR
		y = i // 32
		x = i // 2 % 16
		p = ptc.data[i] + (ptc.data[i+1] << 8)
		r = (p & 0x001f) << 3
		g = ((p & 0x03e0) >> 2) + ((p & 0x8000) >> 13)
		b = (p & 0x7c00) >> 7
		# https://petitcomputer.fandom.com/wiki/COLSET_(Command)
		# is this right? not sure
		r = round(r * 255 / 248)
		g = round(g * 255 / 252)
		b = round(b * 255 / 248)
		col_img.putpixel((x, y), (r, g, b, 255 if i>0 else 0))
	col_img.save(output+".png")

def decode_scr(ptc, output, palette, tiles):
	# img -> data?
	pal=palettize(palette)
	tiles = Image.open(tiles)
	
	from encoder import encode_chr
	# maybe there's a better way to do this
	chr_data = b""
	for i in range(0,tiles.height,64):
		chr_part_img = tiles.crop((0,i,256,i+64))
		chr_data += encode_chr(chr_part_img, b"SCR_TILE", palette).data
	
	scr_img = Image.new("RGBA",(512,512))
	small_img = Image.new("RGBA", (8,8))
	for i in range(0,8192,2):
		# PPPPVHCC CCCCCCCC
		chr_id = ptc.data[i] + ((ptc.data[i+1] & 0x03) << 8)
		chr_h = (ptc.data[i+1] & 0x04) >> 2
		chr_v = (ptc.data[i+1] & 0x08) >> 3
		chr_pal = (ptc.data[i+1] & 0xf0) >> 4
		
		by = i // 4096
		bx = i // 2048 % 2
		ty = i // 64 % 32
		tx = i // 2 % 32
		
#		print(chr_id)
		chr_small_data = chr_data[chr_id*32:chr_id*32+32]
		for py in range(0,8):
			for px in range(0,8,2):
#				print(px,py)
				ph = (chr_small_data[px//2 + 4*py] & 0xf0) >> 4
				pl = chr_small_data[px//2 + 4*py] & 0x0f
				small_img.putpixel((px,py), pal[pl+16*chr_pal])
				small_img.putpixel((px+1,py), pal[ph+16*chr_pal])
		
		if chr_h:
			small_img = small_img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
		if chr_v:
			small_img = small_img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
		
		scr_img.paste(small_img, (8*tx+256*bx,8*ty+256*by))
	scr_img.save(output+".png")

def decode(args):
	"""
	Newlines are converted to LF by Python.
	"""
	ptc = PTCFile(file=args.source_file)
	palette = load_palette(args.palette, ptc.type_str)
	if palette:
		pal = palettize(palette)
	
	if ptc.type_str == PRG_TYPE or ptc.type_str == MEM_TYPE:
		with open(args.output+".txt", "wt", encoding="utf8", newline="") as f:
			if ptc.type_str == PRG_TYPE:
				s = decode_text(ptc.data)
				f.write(s)
			elif ptc.type_str == MEM_TYPE:
#				print(ptc.data)
				s = ptc.data[:512].decode("utf-16-le")
#				s = decode_text(s)
#				print([c for c in s])
#				print(s, len(s))
				f.write(s)
	elif ptc.type_str == GRP_TYPE:
		decode_grp(ptc, args.output, pal)
	elif ptc.type_str == CHR_TYPE:
		decode_chr(ptc, args.output, pal)
	elif ptc.type_str == COL_TYPE:
		decode_col(ptc, args.output)
	elif ptc.type_str == SCR_TYPE:
		decode_scr(ptc, args.output, palette, args.tileset)


