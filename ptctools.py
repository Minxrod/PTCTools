#!/usr/bin/env python3
import argparse

import encoder
import decoder
import qr

parser = argparse.ArgumentParser(prog="ptctools", description="PTC file conversion tools.")
parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.6 (c) 2022")

parser.add_argument("action", choices=["decode","encode","qr"], help="Encode to PTC, decode from PTC, or create QR code from PTC")
parser.add_argument("source_file", help="Source file for action.")

parser.add_argument("-a", "--arrangement", dest="arrangement", action="store", choices=["1x1","1x2","1x4","2x1","2x2","2x4","4x1","4x2","4x4","4x8","8x4","8x8"], help="Sets the arrangement of characters in a CHR image.")
parser.add_argument("-f", "--format", dest="force_type", help="Set PTC file output format.")
parser.add_argument("-m", "--merge", dest="merge", action="store_true", help="Merge generated QRs into one image.")
parser.add_argument("-n", "--name", dest="internal_name", help="Sets the internal PTC filename.")
parser.add_argument("-o", "--output", dest="output", help="Sets the output filename.")
parser.add_argument("-p", "--palette", dest="palette", help="Set the palette file to use when encoding from an image.")
parser.add_argument("-t", "--tileset", dest="tileset", help="Set the tileset file to use when encoding/decoding SCR.")

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
