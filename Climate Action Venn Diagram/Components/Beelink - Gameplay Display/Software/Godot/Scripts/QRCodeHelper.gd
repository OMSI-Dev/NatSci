extends Node
class_name QRCodeHelper

const QRCodeClass := preload("res://addons/qr_code/qr_code.gd")

func generate_qr(text: String, size: int = 8) -> Image:
	var qr = QRCodeClass.new()
	
	#convert string to packedbytearray
	var byte_data = text.to_utf8_buffer()
	
	# Use put_byte if you want to handle full UTF-8 and non-alphanumeric characters
	qr.put_byte(byte_data)
	var image = qr.generate_image(size, Color.WHITE, Color.BLACK)

	# Generate the image with the given module pixel size
	return image
