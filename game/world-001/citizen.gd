extends CharacterBody2D


@export var speed: float = 120.0
@export var citizen_name: String = "@Citizen"


var target_position: Vector2
var rng = RandomNumberGenerator.new()
var can_move: bool = false
var spawn_effect_radius: float = 0.0
var spawn_effect_alpha: float = 1.0


func _ready():
	rng.randomize()

	$NameLabel.text = citizen_name

	scale = Vector2(0.1, 0.1)

	queue_redraw()

	play_spawn_animation()


func play_spawn_animation():
	spawn_effect_radius = 10.0
	spawn_effect_alpha = 1.0

	var tween = create_tween()

	tween.set_trans(Tween.TRANS_BACK)
	tween.set_ease(Tween.EASE_OUT)

	tween.parallel().tween_property(
		self,
		"scale",
		Vector2(1.4, 1.4),
		0.35
	)

	tween.parallel().tween_method(
		update_spawn_effect,
		0.0,
		1.0,
		0.6
	)

	tween.tween_property(
		self,
		"scale",
		Vector2(1.0, 1.0),
		0.20
	)

	await tween.finished

	spawn_effect_alpha = 0.0
	queue_redraw()

	choose_new_target()
	can_move = true

func update_spawn_effect(progress: float):
	spawn_effect_radius = lerp(10.0, 100.0, progress)
	spawn_effect_alpha = lerp(1.0, 0.0, progress)

	queue_redraw()
	
func choose_new_target():
	target_position = Vector2(
		rng.randf_range(200, 2800),
		rng.randf_range(200, 2800)
	)


func _physics_process(delta):
	if not can_move:
		return

	var direction = global_position.direction_to(target_position)

	velocity = direction * speed
	move_and_slide()

	if global_position.distance_to(target_position) < 10:
		choose_new_target()


func _draw():
	# Efeito de nascimento
	if spawn_effect_alpha > 0.0:
		draw_circle(
			Vector2.ZERO,
			spawn_effect_radius,
			Color(0.96, 0.72, 0.25, spawn_effect_alpha)
		)

	# Corpo
	draw_circle(
		Vector2(0, 0),
		25,
		Color("#f4b942")
	)

	# Cabeça
	draw_circle(
		Vector2(0, -32),
		16,
		Color("#f2d0a7")
	)
