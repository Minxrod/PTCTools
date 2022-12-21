ptctools - Essentially a terminal version of PTCUtilities

# Description

This tool intends to be a cross-platform replacement for PTCUtilities's PTC file and QR code conversion capabilities.
This program will not contain an editor - the intended use case is to create files in "normal" formats and convert them as necessary.

This program is a WIP. 
If there is a feature missing you would like to see, please create an issue.
If something breaks, please create an issue. Please provide the command and any relevant files that failed.

# Features:
## encode
* Convert text to PRG, MEM
* Convert image to GRP, CHR, COL, 
* Embed data into GRP, CHR, COL, SCR 
* Set internal name, file name of output PTC
* Format detection based on image size
* Specify palette to encode with

## decode
* Convert PRG, MEM to text
* Convert GRP, CHR, COL to image
* Specify palette to decode with

## qr
* Convert any .PTC to QR code(s)
* Auto-merge QR codes into one image

# Setup
This program is created entirely in Python 3 and relies on the `Pillow` and `qrcode` Python libraries. A basic setup would be:
```
python3 -m pip install Pillow qrcode[PIL]
git clone https://github.com/Minxrod/PTCTools.git
chmod +x ptctools
```

You will need the default color palettes. These can be copied by executed the following PTC commands and then saving to the SD card.
```
SAVE "COL0:COL0"
SAVE "COL2:COL2"
```
Alternatively, you can use the files extracted via the setup of https://github.com/Minxrod/PTC-EmkII. These would be located in the resources/graphics/ subdirectory.

Once you've done so, you can set up the graphics like this:
```shell
./ptctools decode COL0.ptc --output col_bgsp.png
./ptctools decode COL2.ptc --output col_grp.png
```

# Example usage
For more information on each options, see `./ptctools --help`.

## file -> PTC
```
./ptctools encode program.txt
```
Converts program.txt to a PTC file with internal name PROGRAM and filename PROGRAM.PTC
```
./ptctools encode program.txt --name TEST --output myCoolPTCFile
```
Converts program.txt to a PTC file with internal name TEST and filename myCoolPTCFile.PTC

## PTC -> file
```
./ptctools decode PROGRAM.PTC --output myCoolProgram
```
Converts PROGRAM.PTC back into a text file, called myCoolProgram.txt.

## PTC -> QRs
```
mkdir qrs
./ptctools qr PROGRAM.PTC --output qrs/ --merge
```
Converts PROGRAM.PTC into qr codes stored in the qrs/ directory, and then merges them into one image called PROGRAM#merged.png
```
./ptctools encode bgf0.png --name FONT
./ptctools qr FONT.PTC
```
Converts bgf0.png into a PTC file with internal name FONT, and then creates qr codes for it (in the current directory).

# Notes

Encoding and decoding are based on characters that are close to their PTC equivalents in UTF-8.
Some characters are not mapped or do not map correctly (like \x00), so decoded files can be missing some data or look different.

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
	
	There may be some weirdness with line endings. Make sure input files are using "\r" line ending for best results.

## decode
Converts from a PTC file to a common format.

Notes:
For PRG files, line endings will be "\r".

## qr
Converts a PTC file into a QR code or QR codes. Default behavior is to save to the current directory.

# References
* PTCUtilities - https://micutil.com/ptcutilities/top_e.html
* File format information - https://petitcomputer.fandom.com/wiki/PTC_File_Formats
* QR code information - https://gist.github.com/ajc2/25258be3296847bc55cec9e27d13f053
