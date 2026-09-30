extends CharacterBody2D


@export var speed: float = 120.0
@export var citizen_name: String = "@Citizen"


# Área válida atual do mundo.
# O mapa lógico possui 3000x3000,
# mas mantemos uma margem de segurança.
const MAP_MIN := Vector2(200.0, 200.0)
const MAP_MAX := Vector2(2800.0, 2800.0)


var target_position: Vector2

var rng = RandomNumberGenerator.new()

var can_move: bool = false

var spawn_effect_radius: float = 0.0
var spawn_effect_alpha: float = 1.0

var citizen_id: String = ""

var total_roses: int = 1
var wealth: int = 10


func _ready():
	add_to_group("citizens")

	rng.randomize()

	# Proteção para Citizens carregados do banco
	# com alguma posição inválida.
	position = position.clamp(
		MAP_MIN,
		MAP_MAX
	)

	update_label()

	scale = Vector2(0.1, 0.1)

	queue_redraw()

	play_spawn_animation()


func update_label():
	$NameLabel.text = (
		citizen_name
		+ "\n🌹 "
		+ str(total_roses)
	)


func update_progress(
	new_total_roses: int,
	new_wealth: int
):
	total_roses = new_total_roses
	wealth = new_wealth

	update_label()
	queue_redraw()

	var tween = create_tween()

	tween.tween_property(
		self,
		"scale",
		Vector2(1.25, 1.25),
		0.15
	)

	tween.tween_property(
		self,
		"scale",
		Vector2(1.0, 1.0),
		0.15
	)


func play_spawn_animation():
	spawn_effect_radius = 10.0
	spawn_effect_alpha = 1.0

	var tween = create_tween()

	tween.set_trans(
		Tween.TRANS_BACK
	)

	tween.set_ease(
		Tween.EASE_OUT
	)

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


func update_spawn_effect(
	progress: float
):
	spawn_effect_radius = lerp(
		10.0,
		100.0,
		progress
	)

	spawn_effect_alpha = lerp(
		1.0,
		0.0,
		progress
	)

	queue_redraw()


func choose_new_target():
	target_position = Vector2(
		rng.randf_range(
			MAP_MIN.x,
			MAP_MAX.x
		),
		rng.randf_range(
			MAP_MIN.y,
			MAP_MAX.y
		)
	)


func _physics_process(_delta):
	if not can_move:
		velocity = Vector2.ZERO
		return

	var distance_to_target = position.distance_to(
		target_position
	)

	if distance_to_target < 10.0:
		velocity = Vector2.ZERO

		choose_new_target()

		return

	var direction = position.direction_to(
		target_position
	)

	velocity = direction * speed

	move_and_slide()

	# Proteção definitiva:
	# mesmo que alguma lógica futura tente
	# empurrar o Citizen para fora do mapa,
	# ele permanece na área válida.
	position = position.clamp(
		MAP_MIN,
		MAP_MAX
	)


func get_body_color() -> Color:
	if total_roses >= 25:
		return Color("#ffe66d")

	if total_roses >= 10:
		return Color("#b77cff")

	if total_roses >= 5:
		return Color("#58c7ff")

	return Color("#f4b942")


func get_aura_color() -> Color:
	if total_roses >= 25:
		return Color(
			1.0,
			0.9,
			0.3,
			0.25
		)

	if total_roses >= 10:
		return Color(
			0.72,
			0.48,
			1.0,
			0.20
		)

	if total_roses >= 5:
		return Color(
			0.35,
			0.78,
			1.0,
			0.16
		)

	return Color(
		0,
		0,
		0,
		0
	)


func get_aura_radius() -> float:
	if total_roses >= 25:
		return 58.0

	if total_roses >= 10:
		return 50.0

	if total_roses >= 5:
		return 43.0

	return 0.0


func _draw():
	# Efeito de nascimento
	if spawn_effect_alpha > 0.0:
		draw_circle(
			Vector2.ZERO,
			spawn_effect_radius,
			Color(
				0.96,
				0.72,
				0.25,
				spawn_effect_alpha
			)
		)

	# Aura de prestígio
	var aura_radius = get_aura_radius()

	if aura_radius > 0.0:
		draw_circle(
			Vector2(0, -8),
			aura_radius,
			get_aura_color()
		)

	# Corpo
	draw_circle(
		Vector2.ZERO,
		25,
		get_body_color()
	)

	# Cabeça
	draw_circle(
		Vector2(0, -32),
		16,
		Color("#f2d0a7")
	)
