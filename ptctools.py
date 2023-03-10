#!/usr/bin/env python3
import argparse

import encoder
import decoder
import qr
import package

parser = argparse.ArgumentParser(prog="ptctools", description="PTC file conversion tools.")
parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.8 (c) 2022")

parser.add_argument("action", choices=["decode","encode","qr", "merge", "pack", "unpack"], help="Encode to or decode from PTC, or create QR code from PTC, or pack/unpack PTC files.")
parser.add_argument("source_file", help="Source file for action.")

parser.add_argument("-a", "--arrangement", dest="arrangement", action="store", choices=["1x1","1x2","1x4","2x1","2x2","2x4","4x1","4x2","4x4","4x8","8x4","8x8"], help="Sets the arrangement of characters in a CHR image.")
parser.add_argument("-f", "--format", dest="force_type", help="Set PTC file output format.")
parser.add_argument("-m", "--merge", dest="merge", action="store_true", help="Merge generated QRs into one image.")
parser.add_argument("-n", "--name", dest="internal_name", help="Sets the internal PTC filename.")
parser.add_argument("-o", "--output", dest="output", help="Sets the output filename.")
parser.add_argument("-p", "--palette", dest="palette", help="Set the palette file to use when encoding from an image.")
parser.add_argument("-t", "--tileset", dest="tileset", help="Set the tileset file to use when encoding/decoding SCR.")
parser.add_argument("-s", "--package-str", dest="package_str", help="PTC package string to specify files to pack")
parser.add_argument("-d", "--data-files", dest="data_names", nargs="*", help="Specify the file names to pack or unpack.")
parser.add_argument("-c", "--color", dest="color_offset", help="Specify the palette color when decoding CHR resources.")
parser.add_argument("-b", "--palette-block", dest="block_size", help="Treat each palette as being separated into multiple smaller units.")
parser.add_argument("-i", "--no-index", dest="no_index", action="store_true", help="Should QR codes be numbered when merged? (Default yes - specify this to disable)")

args = parser.parse_args()
print(args)

# get output file name
if args.output:
	output = args.output
elif args.internal_name:
	output = args.internal_name
else:
	output = encoder.create_internal_name(args.source_file).decode()
args.output = output

if args.action == "encode":
	# file -> PTC
	# --output takes priority over --name takes priority over default originalname.PTC format
	
	result = encoder.encode(args)
	result.write_file(args.output)
	
	print("Wrote result to PTC file:")
	print(result)
elif args.action == "decode":
	# PTC -> file
	
	decoder.decode(args)
	print("Decoded "+args.source_file+" to file "+args.output)
	
elif args.action == "qr":
	# file -> QRs
	qr.create_qr(args)
	print("QRs created and saved to "+args.output)
elif args.action == "merge":
	# many QRs -> one image
	qr.merge(args.source_file, args.data_names, not args.no_index)
	print("Merged QRs into "+args.source_file)
elif args.action == "pack":
	# PTCs -> PTC
	package.pack(args)
	print("Packed to file "+args.output)
elif args.action == "unpack":
	# PTC -> PTCs
	package.unpack(args)
	print("Unpacked file")
