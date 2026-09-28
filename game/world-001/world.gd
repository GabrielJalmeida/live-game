extends Node2D


const WORLD_WIDTH = 3000
const WORLD_HEIGHT = 3000

const CITIZEN_SCENE = preload("res://citizen.tscn")


var initial_citizens = [
	"@Gabriel",
	"@Maria",
	"@Lucas",
	"@Ana",
	"@Pedro"
]

var simulated_user_counter: int = 1
var population: int = 0
var event_history: Array[String] = []
var world_day: int = 1

func _ready():
	queue_redraw()
	spawn_initial_citizens()

func add_event(message: String):
	event_history.push_front(message)

	if event_history.size() > 4:
		event_history.pop_back()

	$HUD/EventFeed.text = "\n".join(event_history)
	
func spawn_initial_citizens():
	for citizen_name in initial_citizens:
		spawn_citizen(citizen_name)


func spawn_citizen(citizen_name: String):
	var citizen = CITIZEN_SCENE.instantiate()

	citizen.citizen_name = citizen_name

	citizen.position = Vector2(
		randf_range(1100, 1900),
		randf_range(1100, 1900)
	)

	add_child(citizen)

	population += 1
	update_population()

func update_population():
	$HUD/PopulationLabel.text = (
		"DIA " + str(world_day) + "\n" +
		"POPULAÇÃO: " + str(population)
	)

func _draw():
	# Terreno
	draw_rect(
		Rect2(0, 0, WORLD_WIDTH, WORLD_HEIGHT),
		Color("#6f9f52")
	)

	# Estrada vertical
	draw_rect(
		Rect2(1350, 0, 300, WORLD_HEIGHT),
		Color("#c8ad7f")
	)

	# Estrada horizontal
	draw_rect(
		Rect2(0, 1350, WORLD_WIDTH, 300),
		Color("#c8ad7f")
	)

	# Praça central
	draw_circle(
		Vector2(1500, 1500),
		220,
		Color("#b89b6c")
	)

func _input(event):
	if event is InputEventKey:
		if event.pressed and not event.echo and event.keycode == KEY_R:
			simulate_rose()

func simulate_rose():
	var username = "@Viewer_%03d" % simulated_user_counter

	simulated_user_counter += 1

	spawn_citizen(username)
	show_spawn_message(username)
	add_event("🌹 " + username + " nasceu no mundo")

	print("🌹 Rosa simulada por ", username)

func show_spawn_message(username: String):
	var message = $HUD/SpawnMessage

	message.text = (
		"🌹 ROSA RECEBIDA\n\n" +
		"NOVO CIDADÃO\n" +
		username
	)

	message.modulate.a = 1.0
	message.visible = true

	await get_tree().create_timer(2.0).timeout

	var tween = create_tween()

	tween.tween_property(
		message,
		"modulate:a",
		0.0,
		0.5
	)

	await tween.finished

	message.visible = false
