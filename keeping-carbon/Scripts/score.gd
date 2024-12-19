extends Node2D
var value
@onready var title_card = $titleCard
var totalSent = 100

# Called when the node enters the scene tree for the first time.
func _ready():
	value = score.getScore()
	title_card.set_text("You managed to keep " + str(value) + " out of " + str(totalSent) + " carbon sinks from releasing!")
	
# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta):
	pass
