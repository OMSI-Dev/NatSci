extends Node2D


@onready var game_time = $GameTime
@onready var timer = $timer

var easytime = 100
var medTime = 80
var hardTime = 60
var meterHeight
var meterPos
var currentMax = hardTime
var maxHeight = 300
var lastTime
var currentPoints = 0

@onready var meter = $Meter
@onready var current_points = $currentPoints

# Called when the node enters the scene tree for the first time.
func _ready():
	game_time.start(15)
	

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta):
	
	updateGame()

func readCom():
	var data = null
	data = SerialCom.readSerial()
	data = int(data)
	return data

func updateGame():
	var timeleft = round(game_time.get_time_left())
	var incoming = readCom()
	#update the point gain if a button was pressed
	if incoming == 1:
		maxHeight += 5
		score.setScore(1)
		currentPoints += 1
		current_points.set_text(str(currentPoints))
		
		if maxHeight > 300:
			maxHeight = 300
		print(maxHeight)
	
	#update the point loss if 1 second has passed
	if timeleft != lastTime:
		lastTime = timeleft
		maxHeight -= 5

	#change format based on current time
	if timeleft < 10:
		timer.set_text("00:0" + str(timeleft))
	else:
		timer.set_text("00:" + str(timeleft))
	
	#update meter height 
	meter.set_size(Vector2(251,maxHeight))

func _on_game_time_timeout():
	get_tree().change_scene_to_file("res://Scenes/results.tscn")
