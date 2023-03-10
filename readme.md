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
Note that Pillow should be version >=9.1.0, as certain operations (SCR decoding) use features from relatively recent versions.

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
```
./ptctools encode grp.png --name MYGRP
```
Converts a 256x192 image into MYGRP.PTC with internal name MYGRP.
```
./ptctools encode sprites.png --name GAMESPR0 --arrangement 2x2
```
Converts a 256x64 image into GAMESPR0.PTC, with character data arranged for 16x16 pixel sprites.

## PTC -> file
```
./ptctools decode PROGRAM.PTC --output myCoolProgram
```
Converts PROGRAM.PTC back into a text file, called myCoolProgram.txt.
```
./ptctools decode SPU0.PTC --arrangement 2x2
```
Converts SPU0.PTC into an image file SPU0.png, treating the CHR data as containing size 2x2 sprites.

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

## Packaging
```
./ptctools pack MYPROG.PTC --package-str 0x100 --data-names MYFONT.PTC
```
Packs MYPROG.PTC and MYFONT.PTC together into MYPROG.PTC. Note that by default this will overwrite the original program! To specify a different output, use --name or --output.
```
./ptctools unpack MYPROGP.PTC  --name MYPROG --data-names MYFONT
```
Unpacks MYPROGP.PTC to MYPROG.PTC and MYFONT.PTC. Note the use of name - otherwise, MYPROGP would be overwritten with the unpacked version.


# Notes

Encoding and decoding are based on characters that are close to their PTC equivalents in UTF-8.
Some characters are not mapped or do not map correctly (like \x00), so decoded files can be missing some data or look different.

# Operations

## encode
Converts from a common format to a PTC SD formatted file. The output format is guessed based on the input file.
* .txt	->	PRG
* .png (256x64)	->	CHR
* .png (256x64)	->	GRP
* .png (512x512)	->	SCR
* .png (16x16)	->	COL

To specify the MEM type or to specify the type explicity, use the --format option. If a non-image input file is provided
and the output format is forced to be a graphical type, the binary data will be inserted into the PTC file with no conversion.

For PRG types, there may be some weirdness with line endings. Make sure input files are using "\r" line ending, otherwise you'll end up with stars instead of newlines and your program won't work.

### CHR encoding extras
There are some extra settings that are useful for encoding CHR images.

#### --arrangement [-a]
If your images are intended to be used for sprites, you can set the --arrangement option to the sprite size to handle the character arranging for you, instead of manually setting up the spritesheet. This is limited to the entire CHR image however, so if you need multiple sprite sizes in one sheet it will still take some manual effort.

#### --palette-block [-b]
For CHR files, when encoding you can limit the palette further with --palette-block. This splits each palette into smaller blocks, useful if you have duplicate colors and need a specific one to be used. Every division allows the transparent color to be used, in addition to the selected colors. Some divisions will also include the transparent color within the first palette.

Division should be specified as a string of hex digits, where each digit represents the number of colors in a segment. For example,
```
./ptctools encode chr.png -b 133333
```
would create a palette from each set of three colors (after skipping transparency).

## decode
Converts from a PTC file to a common format.

For decoding CHR files, you can specify the output color palette with --color.

Notes:
For PRG files, line endings will be "\r".

## qr
Converts a PTC file into a QR code or QR codes. Default behavior is to save to the current directory.

By specifying the --merge option, QR codes will be automatically combined into one image.

Specify --no-index to not add numbers to a merged QR image.

## merge
Merge several QR images into one. Expects the QR images to be all the same size, but should work 
anyways as long as the first QR is the largest.

Specify the QRs to be combined after --data-files.

Specify --no-index to not add numbers to a merged QR image.

# References
* PTCUtilities - https://micutil.com/ptcutilities/top_e.html
* File format information - https://petitcomputer.fandom.com/wiki/PTC_File_Formats
* QR code information - https://gist.github.com/ajc2/25258be3296847bc55cec9e27d13f053
