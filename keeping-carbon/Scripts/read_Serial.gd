extends Node2D

var data

func _ready():
	pass
	
# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta):
	data = null
	data = SerialCom.readSerial(data)
	if(!data.is_empty()):
		print(data)
