#!/usr/bin/env python3
import argparse

import encoder

parser = argparse.ArgumentParser(prog="ptctools", description="PTC file conversion tools.")
parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1 (c) 2022")

parser.add_argument("action", choices=["decode","encode","qr"], help="Encode to PTC, decode from PTC, or create QR code from PTC")
parser.add_argument("source_file", help="Source file for action.")

parser.add_argument("-f", "--format", dest="dest_format", help="Set PTC file output format.")
parser.add_argument("-l", "--line-ending", dest="line_ending", choices=["CR","LF","CRLF"], help="Sets the line endings of non-PTC files.")
parser.add_argument("-n", "--name", dest="internal_name", help="Sets the internal PTC filename.")
parser.add_argument("-o", "--output", dest="output_name", help="Sets the output filename.")
parser.add_argument("-p", "--palette", dest="palette_file", help="Set the palette file to use when encoding from an image.")

args = parser.parse_args()
print(args)

if args.action == "encode":
	# file -> PTC
	# --output takes priority over --name takes priority over default originalname.PTC format
	if args.output_name:
		output = args.output_name
	elif args.internal_name:
		output = args.internal_name + ".PTC"
	else:
		output = encoder.create_internal_name(args.source_file).decode() + ".PTC"
	
	result = encoder.encode(args.source_file, args.internal_name, args.line_ending, force_type=args.dest_format)
	result.write_file(output)
	
	print(result)
elif args.action == "decode":
	# PTC -> file
	if args.output_name:
		output = args.output_name
	elif args.internal_name:
		output = args.internal_name
	else:
		output = encoder.create_internal_name(args.source_file).decode()
	
	encoder.decode(args.source_file, output)
	
elif args.action == "qr":
	# file -> QRs
	encoder.create_qr(args.source_file)
