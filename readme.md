ptctools - Essentially a terminal version of PTCUtilities

# Description

This tool intends to be a cross-platform replacement for PTCUtilities's PTC file and QR code conversion capabilities.
This program will not contain an editor - the intended use case is to create files in "normal" formats and convert them as necessary.

This program is a WIP. If something breaks, please create an issue. Please provide the command and any relevant files that failed.

# Setup

```shell
git clone https://github.com/Minxrod/ptctools.git
chmod +x ptctools
```

# Example usage
```
./ptctools encode program.txt
```
Converts program.txt to a PTC file with internal name PROGRAM and filename PROGRAM.PTC
```
./ptctools encode program.txt --name TEST --output myCoolPTCFile
```
Converts program.txt to a PTC file with internal name TEST and filename myCoolPTCFile.PTC
```
mkdir qrs
./ptctools qr PROGRAM.PTC --output qrs/ --merge
```
Converts PROGRAM.PTC into qr codes stored in the qrs/ directory, and then merges them into one image called PROGRAM#merged.png
```
./ptctools decode PROGRAM.PTC --output myCoolProgram
```
Converts PROGRAM.PTC back into a text file, called myCoolProgram.txt.
```
./ptctools encode bgf0.png --name FONT
./ptctools qr FONT.PTC
```
Converts bgf0.png into a PTC file with internal name FONT, and then creates qr codes for it (in the current directory).

# Notes

Encoding and decoding are based on characters that are close to their PTC equivalents in UTF-8.
Some characters are not mapped, so decoded files can be missing some data.

# Operations

## encode
Converts from a common format to a PTC SD formatted file. The output format is guessed based on the input file.
*	.txt	->	PRG
*	.png (256x64)	->	CHR
*	.png (256x64)	->	GRP
*	.png (512x512)	->	SCR
*	.png (16x16)	->	COL
	
	To specify the MEM type or to specify the type explicity, use the --format option. If a non-image input file is provided
	and the output format is forced to be a graphical type, the binary data will be inserted into the PTC file with no conversion.
	
	Notes:
	PRG files:
	Line endings are determined by OS/Python default, and converted to CR automatically.

## decode
	Converts from a PTC file to a common format.
	
	Notes:
	PRG files:
	Line endings will be CR only.

## qr
	Converts a PTC file into a QR code or QR codes. Default behavior is to save to 

# Options

--format PTC_FORMAT
-f PTC_FORMAT
	Specify encoding output format directly. For non-image types being mapped to graphical formats, the binary data is inserted.
	MEM,PRG: Read input file as utf-8 text. 
	CHR,GRP,SCR,COL: Read input file as image if possible; otherwise insert binary data into file.

--palette FILE
-p FILE
	Specify the color palette to use for image conversions, instead of the default palette. Only applies if encoding or decoding an image.
