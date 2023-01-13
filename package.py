from ptc_file import PTCFile, CHR_TYPE, MEM_TYPE, SCR_TYPE, COL_TYPE, GRP_TYPE

package_resources = [
	"SPU0", "SPU1", "SPU2", "SPU3", "SPU4", "SPU5", "SPU6", "SPU7",
	"BGU0U", "BGU1U", "BGU2U", "BGU3U",
	"BGF0U",
	"COL0U", "COL1U", "COL2U",
	"SCU0U", "SCU1U",
	"GRP0", "GRP1", "GRP2", "GRP3",
	"MEM",
	"SPD0", "SPD1", "SPD2", "SPD3",
	"BGU0L", "BGU1L", "BGU2L", "BGU3L",
	"BGF0L",
	"COL0L", "COL1L", "COL2L",
	"SCU0L", "SCU1L",
	"SPS0U", "SPS1U",
	"BGD0U", "BGD1U",
	"SPS0L", "SPS1L",
	"BGD0L", "BGD1L"
]

package_types = [CHR_TYPE]*13 + [COL_TYPE]*3 + [SCR_TYPE]*2 + [GRP_TYPE]*4 + [MEM_TYPE] + [CHR_TYPE]*9 + [COL_TYPE]*3 + [SCR_TYPE]*2 + [CHR_TYPE]*8

def pack(args):
	package_prg = PTCFile(file=args.source_file)
	if package_prg.package != b"\0\0\0\0\0\0\0\0":
		raise Exception("This program already has packaged contents!")
	
	package_prg.set_package_str(int(args.package_str, 0))
	
	bits = int(args.package_str, 0)
	files = iter(args.data_names)
	for i in range(0,len(package_resources)):
		if bits & (1 << i):
			try:
				to_pack = PTCFile(file=next(files))
			except StopIteration:
				raise Exception("Not enough PTC files provided for given package string!")
			if package_types[i] != to_pack.type_str:
				raise Exception("Provided input PTC data file does not match expected packed type " + package_types[i].decode())
			package_prg.data += to_pack.type_str + to_pack.data
	
	try:
		next(files)
		raise Exception("Too many PTC files passed for given package string!")
	except StopIteration:
		pass
	
	package_prg.write_file(args.output)
