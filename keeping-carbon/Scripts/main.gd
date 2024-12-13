extends Node2D


@onready var game_time = $GameTime
@onready var timer = $timer

var easytime = 100
var medTime = 80
var hardTime = 60



# Called when the node enters the scene tree for the first time.
func _ready():
	game_time.start(hardTime)
	

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta):
	var timeleft = game_time.get_time_left()
	timer.set_text(str(round(timeleft)))
	print(timeleft)
