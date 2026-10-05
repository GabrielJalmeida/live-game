extends CharacterBody2D


# =========================================================
# CITIZEN STATE
# =========================================================

enum CitizenState {
	IDLE,
	WANDERING,
	WALKING_TO_TREE,
	CHOPPING,
	CHALLENGING_TREE,
	PUSHED_AWAY
}


# =========================================================
# CONFIGURATION
# =========================================================

@export var speed: float = 120.0
@export var citizen_name: String = "@Citizen"


# =========================================================
# WORLD LIMITS
# =========================================================

const MAP_MIN := Vector2(
	WorldGenerator.CELL_SIZE,
	WorldGenerator.CELL_SIZE
)

const MAP_MAX := Vector2(
	WorldGenerator.WORLD_WIDTH - WorldGenerator.CELL_SIZE,
	WorldGenerator.WORLD_HEIGHT - WorldGenerator.CELL_SIZE
)

const API_BASE_URL: String = "http://127.0.0.1:8000/api/v1"

# =========================================================
# RESOURCE RULES
# =========================================================

const TREE_REACH_DISTANCE: float = 35.0

# Cada unidade de madeira leva 3 segundos.
const CHOP_INTERVAL: float = 3.0

# 5% por decisão de conflito.
const RESOURCE_STEAL_CHANCE: float = 0.05

# Distância que a vítima tenta se afastar.
const RESOURCE_STEAL_PUSH_DISTANCE: float = 150.0

# Evita revanche imediatamente após ser expulso.
const RESOURCE_CONFLICT_COOLDOWN: float = 4.0


# =========================================================
# STATE
# =========================================================

var chop_request: HTTPRequest = null

var chop_request_pending: bool = false

var citizen_state: int = CitizenState.IDLE

var target_position: Vector2

var rng := RandomNumberGenerator.new()

var can_move: bool = false

var spawn_effect_radius: float = 0.0
var spawn_effect_alpha: float = 1.0

var citizen_id: String = ""

var total_roses: int = 1
var wealth: int = 10

# Inventário inicial simples.
var wood: int = 0


var world_generator: WorldGenerator = null

var target_tree: WorldTree = null

var chop_timer: float = 0.0

var resource_conflict_cooldown: float = 0.0


# =========================================================
# READY
# =========================================================

func _ready():
	add_to_group("citizens")
	
	chop_request = HTTPRequest.new()

	chop_request.name = "ChopRequest"

	add_child(
		chop_request
	)

	chop_request.request_completed.connect(
		_on_chop_request_completed
	)

	rng.randomize()

	position = position.clamp(
		MAP_MIN,
		MAP_MAX
	)

	update_label()

	scale = Vector2(
		0.1,
		0.1
	)

	queue_redraw()

	play_spawn_animation()


func _exit_tree():
	release_current_tree_links()


# =========================================================
# LABEL
# =========================================================

func update_label():
	$NameLabel.text = (
		citizen_name
		+ "\n🌹 "
		+ str(total_roses)
		+ "  🪵 "
		+ str(wood)
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
		Vector2(
			1.25,
			1.25
		),
		0.15
	)

	tween.tween_property(
		self,
		"scale",
		Vector2.ONE,
		0.15
	)


# =========================================================
# SPAWN
# =========================================================

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
		Vector2(
			1.4,
			1.4
		),
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
		Vector2.ONE,
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


# =========================================================
# HELPERS
# =========================================================

func get_citizen_name(
	citizen: Node
) -> String:

	if citizen == null:
		return "Citizen"

	var value = citizen.get(
		"citizen_name"
	)

	if value == null:
		return "Citizen"

	return str(value)


# =========================================================
# TREE SEARCH
# =========================================================

func find_nearest_free_tree() -> WorldTree:
	if world_generator == null:
		return null

	var nearest_tree: WorldTree = null

	var nearest_distance: float = (
		999999999.0
	)

	for node in get_tree().get_nodes_in_group(
		"trees"
	):
		if not (node is WorldTree):
			continue

		var tree := node as WorldTree

		if not tree.has_wood():
			continue

		if not tree.can_be_targeted(
			self
		):
			continue

		# Se existe um desafiante,
		# não tentamos entrar nesse conflito.
		if (
			tree.get_challenger_by() != null
			and tree.get_challenger_by() != self
		):
			continue

		var distance := position.distance_to(
			tree.position
		)

		if distance >= nearest_distance:
			continue

		if not world_generator.is_path_walkable(
			position,
			tree.position
		):
			continue

		nearest_tree = tree
		nearest_distance = distance

	return nearest_tree


func find_nearest_challengeable_tree() -> WorldTree:
	if world_generator == null:
		return null

	var nearest_tree: WorldTree = null

	var nearest_distance: float = (
		999999999.0
	)

	for node in get_tree().get_nodes_in_group(
		"trees"
	):
		if not (node is WorldTree):
			continue

		var tree := node as WorldTree

		if not tree.can_be_challenged_by(
			self
		):
			continue

		var distance := position.distance_to(
			tree.position
		)

		if distance >= nearest_distance:
			continue

		if not world_generator.is_path_walkable(
			position,
			tree.position
		):
			continue

		nearest_tree = tree
		nearest_distance = distance

	return nearest_tree


# =========================================================
# TARGET
# =========================================================

func set_tree_target(
	tree: WorldTree,
	new_state: int
):
	target_tree = tree

	target_position = tree.position

	citizen_state = new_state


func release_current_tree_links():
	if target_tree == null:
		return

	if is_instance_valid(
		target_tree
	):
		target_tree.release_reservation(
			self
		)

		target_tree.cancel_challenge(
			self
		)

	target_tree = null

	chop_timer = 0.0


# =========================================================
# TARGET DECISION
# =========================================================

func choose_new_target():
	release_current_tree_links()

	# =====================================================
	# 1. TENTA UMA ÁRVORE LIVRE
	# =====================================================

	var free_tree := (
		find_nearest_free_tree()
	)

	if free_tree != null:
		if free_tree.try_reserve(
			self
		):
			set_tree_target(
				free_tree,
				CitizenState.WALKING_TO_TREE
			)

			print(
				"🌳 ",
				citizen_name,
				" reservou ",
				free_tree.tree_id
			)

			return

	# =====================================================
	# 2. NÃO HÁ ÁRVORE LIVRE.
	#    PODE TENTAR ROUBAR UMA.
	# =====================================================

	if resource_conflict_cooldown <= 0.0:
		var occupied_tree := (
			find_nearest_challengeable_tree()
		)

		if occupied_tree != null:
			# UMA rolagem de 5%.
			var steal_roll := rng.randf()

			if (
				steal_roll
				< RESOURCE_STEAL_CHANCE
			):
				if occupied_tree.try_register_challenge(
					self
				):
					set_tree_target(
						occupied_tree,
						CitizenState.CHALLENGING_TREE
					)

					print(
						"⚔️ ",
						citizen_name,
						" decidiu disputar ",
						occupied_tree.tree_id
					)

					return

	# =====================================================
	# 3. NADA PARA FAZER.
	#    ANDA PELO MUNDO.
	# =====================================================

	target_tree = null

	citizen_state = (
		CitizenState.WANDERING
	)

	if world_generator != null:
		target_position = (
			world_generator
			.get_random_walkable_position_near(
				position,
				420.0
			)
		)

		return

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


# =========================================================
# CHOPPING
# =========================================================

func start_chopping():
	citizen_state = (
		CitizenState.CHOPPING
	)

	velocity = Vector2.ZERO

	chop_timer = CHOP_INTERVAL

	print(
		"🪓 ",
		citizen_name,
		" começou a cortar ",
		target_tree.tree_id
	)


func process_chopping(
	delta: float
):
	velocity = Vector2.ZERO

	if (
		target_tree == null
		or not is_instance_valid(
			target_tree
		)
	):
		target_tree = null
		choose_new_target()
		return

	if not target_tree.has_wood():
		target_tree = null
		choose_new_target()
		return

	if (
		target_tree.get_reserved_by()
		!= self
	):
		target_tree = null
		choose_new_target()
		return

	if chop_request_pending:
		return

	chop_timer -= delta

	if chop_timer > 0.0:
		return

	request_tree_chop()

func request_tree_chop():
	if chop_request_pending:
		return

	if target_tree == null:
		choose_new_target()
		return

	if not is_instance_valid(
		target_tree
	):
		target_tree = null
		choose_new_target()
		return

	if citizen_id.is_empty():
		push_error(
			"Citizen sem ID não pode cortar árvore."
		)

		chop_timer = CHOP_INTERVAL
		return

	var url := (
		API_BASE_URL
		+ "/trees/"
		+ target_tree.tree_id.uri_encode()
		+ "/chop"
	)

	var body := JSON.stringify({
		"citizen_id": citizen_id
	})

	var headers := [
		"Content-Type: application/json"
	]

	chop_request_pending = true

	var error := chop_request.request(
		url,
		headers,
		HTTPClient.METHOD_POST,
		body
	)

	if error != OK:
		chop_request_pending = false

		chop_timer = CHOP_INTERVAL

		push_error(
			"Falha ao iniciar corte persistente."
		)


func _on_chop_request_completed(
	result,
	response_code,
	_headers,
	body
):
	chop_request_pending = false

	if result != HTTPRequest.RESULT_SUCCESS:
		chop_timer = CHOP_INTERVAL

		push_error(
			"Falha de conexão ao cortar árvore."
		)

		return

	if response_code != 200:
		chop_timer = CHOP_INTERVAL

		push_error(
			"Backend respondeu ao corte com código: "
			+ str(response_code)
		)

		return

	var data = JSON.parse_string(
		body.get_string_from_utf8()
	)

	if typeof(data) != TYPE_DICTIONARY:
		chop_timer = CHOP_INTERVAL

		push_error(
			"Resposta de corte inválida."
		)

		return

	var citizen_data = data.get(
		"citizen",
		{}
	)

	var tree_data = data.get(
		"tree",
		{}
	)

	var status := str(
		data.get(
			"status",
			""
		)
	)


	# =====================================================
	# CITIZEN
	# =====================================================

	if typeof(citizen_data) == TYPE_DICTIONARY:
		wood = int(
			citizen_data.get(
				"wood",
				wood
			)
		)

		update_label()


	# =====================================================
	# TREE
	# =====================================================

	if typeof(tree_data) == TYPE_DICTIONARY:
		var backend_tree_key := str(
			tree_data.get(
				"tree_key",
				""
			)
		)

		var backend_tree := find_tree_by_id(
			backend_tree_key
		)

		if backend_tree != null:
			backend_tree.apply_backend_state(
				int(
					tree_data.get(
						"wood_amount",
						backend_tree.wood_amount
					)
				),
				str(
					tree_data.get(
						"status",
						"GROWN"
					)
				)
			)


	# =====================================================
	# RESULT
	# =====================================================

	if status == "collected":
		print(
			"🪓 ",
			citizen_name,
			" coletou madeira persistente | ",
			"madeira do Citizen: ",
			wood,
			" | árvore restante: ",
			int(
				tree_data.get(
					"wood_amount",
					0
				)
			)
		)

		if (
			target_tree != null
			and is_instance_valid(target_tree)
			and target_tree.has_wood()
		):
			chop_timer = CHOP_INTERVAL

			return

		target_tree = null

		citizen_state = (
			CitizenState.IDLE
		)

		choose_new_target()

		return

	if status == "tree_unavailable":
		print(
			"🪵 ",
			citizen_name,
			" encontrou a árvore indisponível."
		)

		target_tree = null

		citizen_state = (
			CitizenState.IDLE
		)

		choose_new_target()

		return

	chop_timer = CHOP_INTERVAL
	
func find_tree_by_id(
	tree_id: String
) -> WorldTree:

	for node in get_tree().get_nodes_in_group(
		"trees"
	):
		if not (node is WorldTree):
			continue

		var tree := node as WorldTree

		if tree.tree_id == tree_id:
			return tree

	return null
	
# =========================================================
# RESOURCE CONFLICT
# =========================================================

func complete_tree_challenge():
	if (
		target_tree == null
		or not is_instance_valid(
			target_tree
		)
	):
		choose_new_target()
		return

	if not target_tree.has_wood():
		target_tree.cancel_challenge(
			self
		)

		target_tree = null

		choose_new_target()

		return

	var previous_owner: Node = (
		target_tree.complete_challenge(
			self
		)
	)

	# Confirma se realmente conquistamos
	# a reserva.
	if (
		target_tree.get_reserved_by()
		!= self
	):
		target_tree = null

		choose_new_target()

		return

	if (
		previous_owner != null
		and previous_owner != self
		and is_instance_valid(
			previous_owner
		)
	):
		print(
			"⚔️ ",
			citizen_name,
			" TOMOU ",
			target_tree.tree_id,
			" de ",
			get_citizen_name(
				previous_owner
			)
		)

		if previous_owner.has_method(
			"on_tree_reservation_stolen"
		):
			previous_owner.call(
				"on_tree_reservation_stolen",
				target_tree,
				self
			)

	start_chopping()


func on_tree_reservation_stolen(
	stolen_tree: WorldTree,
	thief: Node
):
	if target_tree != stolen_tree:
		return

	target_tree = null

	chop_timer = 0.0

	citizen_state = (
		CitizenState.PUSHED_AWAY
	)

	resource_conflict_cooldown = (
		RESOURCE_CONFLICT_COOLDOWN
	)

	velocity = Vector2.ZERO

	var away_direction := (
		stolen_tree.position.direction_to(
			position
		)
	)

	if away_direction.length_squared() < 0.01:
		away_direction = (
			Vector2.RIGHT.rotated(
				rng.randf_range(
					0.0,
					TAU
				)
			)
		)

	var push_target := (
		position
		+ away_direction
		* RESOURCE_STEAL_PUSH_DISTANCE
	)

	push_target = push_target.clamp(
		MAP_MIN,
		MAP_MAX
	)

	if (
		world_generator != null
		and world_generator.is_path_walkable(
			position,
			push_target
		)
	):
		target_position = push_target

	elif world_generator != null:
		target_position = (
			world_generator
			.get_random_walkable_position_near(
				position,
				180.0
			)
		)

	else:
		target_position = position

	can_move = true

	print(
		"💥 ",
		citizen_name,
		" foi expulso por ",
		get_citizen_name(
			thief
		),
		" | madeira preservada: ",
		wood
	)


# =========================================================
# PHYSICS
# =========================================================

func _physics_process(
	delta: float
):
	if resource_conflict_cooldown > 0.0:
		resource_conflict_cooldown = max(
			0.0,
			resource_conflict_cooldown
			- delta
		)

	if not can_move:
		velocity = Vector2.ZERO
		return

	# =====================================================
	# CHOPPING NÃO POSSUI MOVIMENTO
	# =====================================================

	if citizen_state == CitizenState.CHOPPING:
		process_chopping(
			delta
		)

		return

	# =====================================================
	# DISTANCE
	# =====================================================

	var distance_to_target := (
		position.distance_to(
			target_position
		)
	)

	var reach_distance: float = 10.0

	if target_tree != null:
		reach_distance = (
			TREE_REACH_DISTANCE
		)

	# =====================================================
	# ARRIVAL
	# =====================================================

	if distance_to_target < reach_distance:
		velocity = Vector2.ZERO

		match citizen_state:

			CitizenState.WALKING_TO_TREE:
				if (
					target_tree != null
					and target_tree.get_reserved_by()
					== self
				):
					start_chopping()

					return

				choose_new_target()

				return


			CitizenState.CHALLENGING_TREE:
				complete_tree_challenge()

				return


			CitizenState.PUSHED_AWAY:
				citizen_state = (
					CitizenState.IDLE
				)

				choose_new_target()

				return


			CitizenState.WANDERING:
				citizen_state = (
					CitizenState.IDLE
				)

				choose_new_target()

				return


			_:
				choose_new_target()

				return

	# =====================================================
	# MOVEMENT
	# =====================================================

	var direction := (
		position.direction_to(
			target_position
		)
	)

	velocity = (
		direction
		* speed
	)

	var next_position := (
		position
		+ velocity * delta
	)

	# Não atravessa água.
	if world_generator != null:
		if not world_generator.is_walkable_position(
			next_position
		):
			velocity = Vector2.ZERO

			release_current_tree_links()

			citizen_state = (
				CitizenState.IDLE
			)

			choose_new_target()

			return

	move_and_slide()

	position = position.clamp(
		MAP_MIN,
		MAP_MAX
	)


# =========================================================
# TEMPORARY APPEARANCE
# =========================================================

# =========================================================
# APARÊNCIA TEMPORÁRIA — AVATAR NEUTRO / CARISMÁTICO
# =========================================================

func get_outfit_main_color() -> Color:
	if total_roses >= 25:
		return Color("#f7d85c")

	if total_roses >= 10:
		return Color("#b77cff")

	if total_roses >= 5:
		return Color("#58c7ff")

	return Color("#f4b942")


func get_outfit_shadow_color() -> Color:
	return get_outfit_main_color().darkened(0.22)


func get_outfit_accent_color() -> Color:
	return get_outfit_main_color().lightened(0.16)


func get_skin_color() -> Color:
	return Color("#f2d0a7")


func get_eye_color() -> Color:
	return Color("#2b241f")


func get_blush_color() -> Color:
	return Color(1.0, 0.62, 0.72, 0.45)


func get_body_color() -> Color:
	return get_outfit_main_color()


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
		0.0,
		0.0,
		0.0,
		0.0
	)


func get_aura_radius() -> float:
	if total_roses >= 25:
		return 58.0

	if total_roses >= 10:
		return 50.0

	if total_roses >= 5:
		return 43.0

	return 0.0


# =========================================================
# DRAW
# =========================================================

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

	# Aura de progressão
	var aura_radius = get_aura_radius()

	if aura_radius > 0.0:
		draw_circle(
			Vector2(
				0.0,
				-8.0
			),
			aura_radius,
			get_aura_color()
		)

	var outfit_main = get_outfit_main_color()
	var outfit_shadow = get_outfit_shadow_color()
	var outfit_accent = get_outfit_accent_color()
	var skin = get_skin_color()
	var eye = get_eye_color()
	var blush = get_blush_color()

	# Sombra no chão
	draw_circle(
		Vector2(
			0.0,
			31.0
		),
		15.0,
		Color(0.0, 0.0, 0.0, 0.12)
	)

	# Perninhas / pés
	draw_circle(
		Vector2(
			-8.0,
			24.0
		),
		5.5,
		outfit_shadow
	)

	draw_circle(
		Vector2(
			8.0,
			24.0
		),
		5.5,
		outfit_shadow
	)

	# Bracinhos
	draw_circle(
		Vector2(
			-18.0,
			0.0
		),
		6.0,
		outfit_accent
	)

	draw_circle(
		Vector2(
			18.0,
			0.0
		),
		6.0,
		outfit_accent
	)

	# Corpo
	draw_rect(
		Rect2(
			-16.0,
			-6.0,
			32.0,
			28.0
		),
		outfit_main
	)

	draw_circle(
		Vector2(
			0.0,
			-6.0
		),
		16.0,
		outfit_main
	)

	draw_circle(
		Vector2(
			0.0,
			16.0
		),
		14.0,
		outfit_main
	)

	# Detalhe do corpo
	draw_circle(
		Vector2(
			0.0,
			8.0
		),
		8.0,
		outfit_accent
	)

	# Cabeça
	draw_circle(
		Vector2(
			0.0,
			-30.0
		),
		16.0,
		skin
	)

	# Tufo superior neutro / estilizado
	draw_circle(
		Vector2(
			0.0,
			-46.0
		),
		5.0,
		outfit_shadow
	)

	draw_circle(
		Vector2(
			-5.0,
			-44.0
		),
		3.0,
		outfit_shadow
	)

	draw_circle(
		Vector2(
			5.0,
			-44.0
		),
		3.0,
		outfit_shadow
	)

	# Olhos
	draw_circle(
		Vector2(
			-5.0,
			-32.0
		),
		2.1,
		eye
	)

	draw_circle(
		Vector2(
			5.0,
			-32.0
		),
		2.1,
		eye
	)

	# Brilhinhos dos olhos
	draw_circle(
		Vector2(
			-4.3,
			-32.8
		),
		0.7,
		Color.WHITE
	)

	draw_circle(
		Vector2(
			5.7,
			-32.8
		),
		0.7,
		Color.WHITE
	)

	# Bochechas
	draw_circle(
		Vector2(
			-10.0,
			-26.0
		),
		2.4,
		blush
	)

	draw_circle(
		Vector2(
			10.0,
			-26.0
		),
		2.4,
		blush
	)

	# Sorrisinho
	draw_arc(
		Vector2(
			0.0,
			-25.0
		),
		5.0,
		0.30,
		PI - 0.30,
		10,
		eye,
		1.6,
		true
	)
