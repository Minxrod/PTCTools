from PIL import Image

from ptc_file import CHR_TYPE, SCR_TYPE, GRP_TYPE

# Prioritize visual similarity:
CHARS =  "\0🅐🅑����☺☻⇥★🖛🅻\r��♪♫🆁��🭽🭶🭾🅧🅨⭗�⭢⭠⭡⭣"
CHARS += "".join([chr(c) for c in range(32,128)])
CHARS += "◇▘▝▀▖▌▞▛▗▚▐▜▄▙▟█┻┳┣╋┫━┃■┏┓┗┛◢◣◥◤～。「」、・ヲァィゥェォャュョッーアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン゛゜◼●▲▼□○△▽��������♠♥♦♣🯅���▔▏▕▁╱╲╳▒"

# Prioritize code accuracy:
MEM_CHARS = "\0\t\n\r ！”＃＄％＆’（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ［￥］＾＿｀ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ｛｜｝～｟ 。「」、・ヲァィゥェォャュョッｰアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン゛゜àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"

def palettize(image):
	pal_array = []
	for y in range(0,image.height):
		for x in range(0,image.width):
			pal_array.append(image.getpixel((x,y)))
	return pal_array

def load_palette(palette, type_str=None):
	if palette is None and (type_str == CHR_TYPE or type_str == SCR_TYPE):
		# open default CHR palette and use that
		palette = "col_bgsp.png"
	elif palette is None and type_str == GRP_TYPE:
		# open default GRP palette
		palette = "col_grp.png"
	# open provided palette
	if palette:
		palette = Image.open(palette)
	return palette
	

