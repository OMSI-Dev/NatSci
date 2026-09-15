extends Node2D

@onready var value = 0

# Called when the node enters the scene tree for the first time.
func _ready():
	pass


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta):
	pass
	
func setScore(score):
	value += score
	print("Current Score: " + str(score))

func getScore():
	return value
