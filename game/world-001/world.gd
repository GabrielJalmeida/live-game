extends Node2D


# =========================================================
# WORLD 001
# =========================================================

const WORLD_WIDTH: float = 3000.0
const WORLD_HEIGHT: float = 3000.0

const WORLD_CENTER := Vector2(
	WORLD_WIDTH / 2.0,
	WORLD_HEIGHT / 2.0
)

const CITIZEN_MIN := Vector2(200.0, 200.0)
const CITIZEN_MAX := Vector2(2800.0, 2800.0)


# =========================================================
# BACKEND
# =========================================================

const API_BASE_URL = "http://127.0.0.1:8000/api/v1"

const WEBSOCKET_URL = "ws://127.0.0.1:8000/ws/world"

const WEBSOCKET_RECONNECT_DELAY: float = 3.0


# =========================================================
# CAMERA / SPOTLIGHT
# =========================================================

# Quando ainda ninguém recebeu spotlight.
const CAMERA_IDLE_ZOOM := Vector2(
	0.55,
	0.55
)

# Zoom usado quando estamos acompanhando um Citizen.
const CAMERA_SPOTLIGHT_ZOOM := Vector2(
	1.15,
	1.15
)

const CAMERA_SMOOTHING_SPEED: float = 6.0


# =========================================================
# SCENES
# =========================================================

const CITIZEN_SCENE = preload(
	"res://citizen.tscn"
)


# =========================================================
# WORLD STATE
# =========================================================

var simulated_user_counter: int = 1

var population: int = 0

var event_history: Array[String] = []

var world_day: int = 1


# =========================================================
# WEBSOCKET
# =========================================================

var websocket = WebSocketPeer.new()

var websocket_reconnect_timer: float = 0.0

var websocket_is_open: bool = false

var websocket_has_connected_once: bool = false


# =========================================================
# CAMERA STATE
# =========================================================

var world_camera: Camera2D

var spotlight_citizen = null

var spotlight_citizen_id: String = ""

var camera_zoom_tween: Tween


# =========================================================
# VISUAL DECORATION
# =========================================================

var grass_patches: Array[Vector2] = []

var bushes: Array[Vector2] = []

var flowers: Array[Vector2] = []

var visual_rng = RandomNumberGenerator.new()


# =========================================================
# READY
# =========================================================

func _ready():
	generate_world_decorations()

	setup_camera()

	queue_redraw()

	$CitizensRequest.request_completed.connect(
		_on_citizens_request_completed
	)

	$RoseRequest.request_completed.connect(
		_on_rose_request_completed
	)

	$WorldRequest.request_completed.connect(
		_on_world_request_completed
	)

	connect_websocket()

	load_citizens_from_backend()

	load_world_from_backend()


# =========================================================
# PROCESS
# =========================================================

func _process(delta):
	process_websocket(delta)

	process_camera()


# =========================================================
# CAMERA / SPOTLIGHT
# =========================================================

func setup_camera():
	world_camera = get_viewport().get_camera_2d()

	if world_camera == null:
		world_camera = Camera2D.new()

		world_camera.name = "WorldCamera"

		add_child(
			world_camera
		)

		world_camera.make_current()

	world_camera.limit_enabled = true

	world_camera.limit_left = 0
	world_camera.limit_top = 0

	world_camera.limit_right = int(
		WORLD_WIDTH
	)

	world_camera.limit_bottom = int(
		WORLD_HEIGHT
	)

	world_camera.position_smoothing_enabled = true

	world_camera.position_smoothing_speed = (
		CAMERA_SMOOTHING_SPEED
	)

	world_camera.limit_smoothed = true

	world_camera.global_position = (
		WORLD_CENTER
	)

	world_camera.zoom = (
		CAMERA_IDLE_ZOOM
	)


func process_camera():
	if world_camera == null:
		return

	# Existe um Citizen sendo acompanhado.
	if is_instance_valid(
		spotlight_citizen
	):
		world_camera.global_position = (
			spotlight_citizen.global_position
		)

		return

	# Caso o Citizen desapareça da cena
	# por qualquer motivo.
	if spotlight_citizen != null:
		spotlight_citizen = null
		spotlight_citizen_id = ""

		world_camera.global_position = (
			WORLD_CENTER
		)

		world_camera.zoom = (
			CAMERA_IDLE_ZOOM
		)


func focus_citizen(citizen):
	if citizen == null:
		return

	if not is_instance_valid(
		citizen
	):
		return

	spotlight_citizen = citizen

	spotlight_citizen_id = (
		citizen.citizen_id
	)

	print(
		"🎥 Spotlight agora acompanha: ",
		citizen.citizen_name
	)

	# Cancela um tween anterior caso
	# outra Rosa chegue rapidamente.
	if (
		camera_zoom_tween != null
		and camera_zoom_tween.is_valid()
	):
		camera_zoom_tween.kill()

	camera_zoom_tween = create_tween()

	camera_zoom_tween.set_trans(
		Tween.TRANS_QUAD
	)

	camera_zoom_tween.set_ease(
		Tween.EASE_OUT
	)

	camera_zoom_tween.tween_property(
		world_camera,
		"zoom",
		CAMERA_SPOTLIGHT_ZOOM,
		0.35
	)


func find_citizen_by_id(
	citizen_id: String
):
	for citizen in get_tree().get_nodes_in_group(
		"citizens"
	):
		if citizen.citizen_id == citizen_id:
			return citizen

	return null


# =========================================================
# WORLD API
# =========================================================

func load_world_from_backend():
	var url = (
		API_BASE_URL
		+ "/world"
	)

	var error = $WorldRequest.request(
		url
	)

	if error != OK:
		push_error(
			"Não foi possível carregar o WORLD 001."
		)


func _on_world_request_completed(
	result,
	response_code,
	_headers,
	body
):
	if result != HTTPRequest.RESULT_SUCCESS:
		push_error(
			"Falha ao carregar informações do mundo."
		)

		return

	if response_code != 200:
		push_error(
			"Backend respondeu ao mundo com código: "
			+ str(response_code)
		)

		return

	var data = JSON.parse_string(
		body.get_string_from_utf8()
	)

	if typeof(data) != TYPE_DICTIONARY:
		push_error(
			"Resposta do WORLD 001 inválida."
		)

		return

	world_day = int(
		data.get(
			"day",
			1
		)
	)

	update_population()

	print(
		"🌍 WORLD 001 carregado | DIA ",
		world_day
	)


# =========================================================
# WEBSOCKET
# =========================================================

func connect_websocket():
	websocket = WebSocketPeer.new()

	var error = websocket.connect_to_url(
		WEBSOCKET_URL
	)

	if error != OK:
		push_error(
			"Não foi possível iniciar o WebSocket."
		)

	else:
		print(
			"🔌 Tentando conectar ao WebSocket..."
		)


func process_websocket(delta):
	websocket.poll()

	var state = websocket.get_ready_state()

	if state == WebSocketPeer.STATE_OPEN:

		if not websocket_is_open:
			websocket_is_open = true

			websocket_reconnect_timer = 0.0

			print(
				"🔌 WebSocket conectado."
			)

			if websocket_has_connected_once:
				print(
					"🔄 Ressincronizando WORLD 001..."
				)

				resync_world_from_backend()

			else:
				websocket_has_connected_once = true

		while (
			websocket.get_available_packet_count()
			> 0
		):
			var packet = websocket.get_packet()

			var text = (
				packet.get_string_from_utf8()
			)

			handle_websocket_message(
				text
			)

	elif state == WebSocketPeer.STATE_CLOSING:
		pass

	elif state == WebSocketPeer.STATE_CLOSED:

		if websocket_is_open:
			websocket_is_open = false

			print(
				"⚠️ WebSocket desconectado."
			)

		websocket_reconnect_timer += delta

		if (
			websocket_reconnect_timer
			>= WEBSOCKET_RECONNECT_DELAY
		):
			websocket_reconnect_timer = 0.0

			print(
				"🔄 Tentando reconectar WebSocket..."
			)

			connect_websocket()


func resync_world_from_backend():
	load_world_from_backend()

	load_citizens_from_backend()


func handle_websocket_message(
	message: String
):
	var data = JSON.parse_string(
		message
	)

	if typeof(data) != TYPE_DICTIONARY:
		push_error(
			"Mensagem WebSocket inválida."
		)

		return

	if not data.has("type"):
		return

	match data["type"]:

		"citizen_spawned":
			handle_citizen_spawned(
				data
			)

		"citizen_supported":
			handle_citizen_supported(
				data
			)

		"comment_received":
			handle_comment_received(
				data
			)


# =========================================================
# CITIZEN SPAWN
# =========================================================

func handle_citizen_spawned(
	data
):
	if not data.has("citizen"):
		return

	var citizen_data = data["citizen"]

	var citizen = spawn_citizen_from_backend(
		citizen_data
	)

	if citizen == null:
		return

	var username = str(
		citizen_data.get(
			"name",
			"Citizen"
		)
	)

	# A nova Rosa define imediatamente
	# o protagonista da transmissão.
	focus_citizen(
		citizen
	)

	show_spotlight_message(
		username,
		true
	)

	add_event(
		"🌹 "
		+ username
		+ " nasceu no mundo"
	)

	print(
		"📡 Citizen recebido por WebSocket: ",
		username
	)


# =========================================================
# CITIZEN SUPPORT / ROSA REPETIDA
# =========================================================

func handle_citizen_supported(
	data
):
	if not data.has("citizen"):
		return

	var citizen_data = data["citizen"]

	var incoming_id = str(
		citizen_data.get(
			"id",
			""
		)
	)

	var username = str(
		citizen_data.get(
			"name",
			"Citizen"
		)
	)

	var total_roses = int(
		citizen_data.get(
			"total_roses",
			1
		)
	)

	var wealth = int(
		citizen_data.get(
			"wealth",
			10
		)
	)

	var citizen = find_citizen_by_id(
		incoming_id
	)

	# Normalmente o Citizen já existe.
	if citizen != null:
		citizen.update_progress(
			total_roses,
			wealth
		)

	# Proteção caso o cliente tenha perdido
	# aquele Citizen por algum motivo.
	else:
		citizen = spawn_citizen_from_backend(
			citizen_data
		)

	if citizen != null:
		# Mesmo um usuário antigo volta
		# a ser protagonista ao mandar Rosa.
		focus_citizen(
			citizen
		)

		show_spotlight_message(
			username,
			false
		)

	add_event(
		"🌹 "
		+ username
		+ " agora tem "
		+ str(total_roses)
		+ " rosas"
	)

	print(
		"💰 ",
		username,
		" | Rosas: ",
		total_roses,
		" | Patrimônio: ",
		wealth
	)


# =========================================================
# COMMENTS
# =========================================================

func handle_comment_received(
	data
):
	if not data.has(
		"username"
	):
		return

	if not data.has(
		"comment"
	):
		return

	var username = str(
		data["username"]
	)

	var comment = str(
		data["comment"]
	)

	add_event(
		"💬 "
		+ username
		+ ": "
		+ comment
	)


# =========================================================
# CITIZENS API
# =========================================================

func load_citizens_from_backend():
	var url = (
		API_BASE_URL
		+ "/citizens"
	)

	var error = $CitizensRequest.request(
		url
	)

	if error != OK:
		push_error(
			"Não foi possível iniciar "
			+ "a requisição de cidadãos."
		)


func _on_citizens_request_completed(
	result,
	response_code,
	_headers,
	body
):
	if result != HTTPRequest.RESULT_SUCCESS:
		push_error(
			"Falha ao conectar com o backend."
		)

		return

	if response_code != 200:
		push_error(
			"Backend respondeu com código: "
			+ str(response_code)
		)

		return

	var data = JSON.parse_string(
		body.get_string_from_utf8()
	)

	if typeof(data) != TYPE_ARRAY:
		push_error(
			"Resposta de cidadãos inválida."
		)

		return

	for citizen_data in data:
		spawn_citizen_from_backend(
			citizen_data
		)

	refresh_population_from_scene()

	print(
		"Citizens carregados do backend: ",
		data.size()
	)


# =========================================================
# SPAWN / SYNC CITIZEN
# =========================================================

func spawn_citizen_from_backend(
	data
):
	var incoming_id = str(
		data.get(
			"id",
			""
		)
	)

	if incoming_id.is_empty():
		push_error(
			"Citizen recebido sem ID."
		)

		return null

	# -----------------------------------------------------
	# Citizen já existe.
	# Apenas sincroniza.
	# -----------------------------------------------------

	for existing_citizen in get_tree().get_nodes_in_group(
		"citizens"
	):
		if (
			existing_citizen.citizen_id
			== incoming_id
		):
			existing_citizen.citizen_name = str(
				data.get(
					"name",
					"Citizen"
				)
			)

			existing_citizen.total_roses = int(
				data.get(
					"total_roses",
					1
				)
			)

			existing_citizen.wealth = int(
				data.get(
					"wealth",
					10
				)
			)

			var synced_position = Vector2(
				float(
					data.get(
						"x",
						existing_citizen.position.x
					)
				),
				float(
					data.get(
						"y",
						existing_citizen.position.y
					)
				)
			)

			existing_citizen.position = (
				synced_position.clamp(
					CITIZEN_MIN,
					CITIZEN_MAX
				)
			)

			existing_citizen.update_label()

			existing_citizen.queue_redraw()

			return existing_citizen

	# -----------------------------------------------------
	# Citizen novo.
	# -----------------------------------------------------

	var citizen = CITIZEN_SCENE.instantiate()

	citizen.citizen_id = incoming_id

	citizen.citizen_name = str(
		data.get(
			"name",
			"Citizen"
		)
	)

	citizen.total_roses = int(
		data.get(
			"total_roses",
			1
		)
	)

	citizen.wealth = int(
		data.get(
			"wealth",
			10
		)
	)

	citizen.position = Vector2(
		float(
			data.get(
				"x",
				WORLD_CENTER.x
			)
		),
		float(
			data.get(
				"y",
				WORLD_CENTER.y
			)
		)
	)

	citizen.position = citizen.position.clamp(
		CITIZEN_MIN,
		CITIZEN_MAX
	)

	add_child(
		citizen
	)

	refresh_population_from_scene()

	return citizen


# =========================================================
# LOCAL DEBUG SPAWN
# =========================================================

func spawn_citizen(
	new_citizen_name: String
):
	var citizen = CITIZEN_SCENE.instantiate()

	citizen.citizen_name = new_citizen_name

	citizen.position = Vector2(
		randf_range(
			1100.0,
			1900.0
		),
		randf_range(
			1100.0,
			1900.0
		)
	)

	add_child(
		citizen
	)

	refresh_population_from_scene()


# =========================================================
# POPULATION
# =========================================================

func refresh_population_from_scene():
	population = get_tree().get_nodes_in_group(
		"citizens"
	).size()

	update_population()


func update_population():
	$HUD/PopulationLabel.text = (
		"DIA "
		+ str(world_day)
		+ "\n"
		+ "POPULAÇÃO: "
		+ str(population)
	)


# =========================================================
# EVENT FEED
# =========================================================

func add_event(
	message: String
):
	event_history.push_front(
		message
	)

	if event_history.size() > 4:
		event_history.pop_back()

	$HUD/EventFeed.text = "\n".join(
		event_history
	)


# =========================================================
# TEST ROSE
# =========================================================

func _input(event):
	if event is InputEventKey:

		if (
			event.pressed
			and not event.echo
			and event.keycode == KEY_R
		):
			simulate_rose()


func simulate_rose():
	var username = (
		"@Viewer_%03d"
		% simulated_user_counter
	)

	simulated_user_counter += 1

	var url = (
		API_BASE_URL
		+ "/dev/events/rose"
	)

	var body = JSON.stringify({
		"username": username
	})

	var headers = [
		"Content-Type: application/json"
	]

	var error = $RoseRequest.request(
		url,
		headers,
		HTTPClient.METHOD_POST,
		body
	)

	if error != OK:
		push_error(
			"Não foi possível enviar "
			+ "a Rosa para o backend."
		)


func _on_rose_request_completed(
	result,
	response_code,
	_headers,
	_body
):
	if result != HTTPRequest.RESULT_SUCCESS:
		push_error(
			"Falha ao enviar Rosa ao backend."
		)

		return

	if response_code != 200:
		push_error(
			"Backend respondeu à Rosa com código: "
			+ str(response_code)
		)

		return

	print(
		"🌹 Rosa aceita pelo backend."
	)


# =========================================================
# SPOTLIGHT MESSAGE
# =========================================================

func show_spotlight_message(
	username: String,
	is_new_citizen: bool
):
	var message = $HUD/SpawnMessage

	if is_new_citizen:
		message.text = (
			"🌹 ROSA RECEBIDA"
			+ "\n\n"
			+ "NOVO CIDADÃO"
			+ "\n"
			+ username
		)

	else:
		message.text = (
			"🌹 ROSA RECEBIDA"
			+ "\n\n"
			+ "ACOMPANHANDO"
			+ "\n"
			+ username
		)

	message.modulate.a = 1.0

	message.visible = true

	message.scale = Vector2(
		0.85,
		0.85
	)

	var intro_tween = create_tween()

	intro_tween.set_trans(
		Tween.TRANS_BACK
	)

	intro_tween.set_ease(
		Tween.EASE_OUT
	)

	intro_tween.tween_property(
		message,
		"scale",
		Vector2.ONE,
		0.25
	)

	await get_tree().create_timer(
		2.0
	).timeout

	var outro_tween = create_tween()

	outro_tween.tween_property(
		message,
		"modulate:a",
		0.0,
		0.5
	)

	await outro_tween.finished

	message.visible = false


# =========================================================
# TEMPORARY WORLD VISUAL
# =========================================================

func generate_world_decorations():
	visual_rng.seed = 1001

	grass_patches.clear()
	bushes.clear()
	flowers.clear()

	for i in range(34):
		grass_patches.append(
			Vector2(
				visual_rng.randf_range(
					100.0,
					2900.0
				),
				visual_rng.randf_range(
					100.0,
					2900.0
				)
			)
		)

	while bushes.size() < 42:
		var candidate = Vector2(
			visual_rng.randf_range(
				120.0,
				2880.0
			),
			visual_rng.randf_range(
				120.0,
				2880.0
			)
		)

		if is_valid_decoration_position(
			candidate
		):
			bushes.append(
				candidate
			)

	while flowers.size() < 120:
		var flower_position = Vector2(
			visual_rng.randf_range(
				120.0,
				2880.0
			),
			visual_rng.randf_range(
				120.0,
				2880.0
			)
		)

		if (
			flower_position.distance_to(
				WORLD_CENTER
			) > 300.0
		):
			flowers.append(
				flower_position
			)


func is_valid_decoration_position(
	position_to_check: Vector2
) -> bool:
	if abs(
		position_to_check.x
		- WORLD_CENTER.x
	) < 250.0:
		return false

	if abs(
		position_to_check.y
		- WORLD_CENTER.y
	) < 250.0:
		return false

	if (
		position_to_check.distance_to(
			WORLD_CENTER
		)
		< 420.0
	):
		return false

	return true


func _draw():
	# =====================================================
	# FUNDO EXTERNO
	# =====================================================

	draw_rect(
		Rect2(
			-2500.0,
			-2500.0,
			8000.0,
			8000.0
		),
		Color("#18281f")
	)

	# =====================================================
	# TERRENO
	# =====================================================

	draw_rect(
		Rect2(
			0.0,
			0.0,
			WORLD_WIDTH,
			WORLD_HEIGHT
		),
		Color("#78ad58")
	)

	draw_rect(
		Rect2(
			55.0,
			55.0,
			WORLD_WIDTH - 110.0,
			WORLD_HEIGHT - 110.0
		),
		Color("#83b961")
	)

	# =====================================================
	# MANCHAS DE GRAMA
	# =====================================================

	for i in range(
		grass_patches.size()
	):
		var patch = grass_patches[i]

		var radius = (
			100.0
			+ float(i % 5) * 24.0
		)

		var patch_color: Color

		if i % 2 == 0:
			patch_color = Color(
				0.36,
				0.58,
				0.27,
				0.20
			)

		else:
			patch_color = Color(
				0.68,
				0.82,
				0.42,
				0.16
			)

		draw_circle(
			patch,
			radius,
			patch_color
		)

	# =====================================================
	# ESTRADAS
	# =====================================================

	var road_outer = Color(
		"#b99769"
	)

	var road_inner = Color(
		"#d7bf91"
	)

	draw_rect(
		Rect2(
			1330.0,
			0.0,
			340.0,
			WORLD_HEIGHT
		),
		road_outer
	)

	draw_rect(
		Rect2(
			1370.0,
			0.0,
			260.0,
			WORLD_HEIGHT
		),
		road_inner
	)

	draw_rect(
		Rect2(
			0.0,
			1330.0,
			WORLD_WIDTH,
			340.0
		),
		road_outer
	)

	draw_rect(
		Rect2(
			0.0,
			1370.0,
			WORLD_WIDTH,
			260.0
		),
		road_inner
	)

	for i in range(12):
		var line_offset = (
			260.0
			+ float(i) * 220.0
		)

		draw_circle(
			Vector2(
				1500.0,
				line_offset
			),
			5.0,
			Color(
				1.0,
				0.94,
				0.75,
				0.35
			)
		)

		draw_circle(
			Vector2(
				line_offset,
				1500.0
			),
			5.0,
			Color(
				1.0,
				0.94,
				0.75,
				0.35
			)
		)

	# =====================================================
	# PRAÇA CENTRAL
	# =====================================================

	draw_circle(
		WORLD_CENTER,
		300.0,
		Color("#a68159")
	)

	draw_circle(
		WORLD_CENTER,
		260.0,
		Color("#d3b47d")
	)

	draw_circle(
		WORLD_CENTER,
		205.0,
		Color("#edd398")
	)

	draw_circle(
		WORLD_CENTER,
		155.0,
		Color("#87bc63")
	)

	draw_circle(
		WORLD_CENTER,
		70.0,
		Color("#709f50")
	)

	draw_circle(
		WORLD_CENTER,
		40.0,
		Color("#f3c755")
	)

	# =====================================================
	# ARBUSTOS
	# =====================================================

	for bush_position in bushes:
		draw_circle(
			bush_position,
			34.0,
			Color("#426f3a")
		)

		draw_circle(
			bush_position
			+ Vector2(
				-12.0,
				-8.0
			),
			24.0,
			Color("#5d9148")
		)

		draw_circle(
			bush_position
			+ Vector2(
				13.0,
				-4.0
			),
			21.0,
			Color("#6fa653")
		)

	# =====================================================
	# FLORES
	# =====================================================

	for i in range(
		flowers.size()
	):
		var flower = flowers[i]

		var flower_color: Color

		match i % 4:

			0:
				flower_color = Color(
					"#ffe06b"
				)

			1:
				flower_color = Color(
					"#ff9db4"
				)

			2:
				flower_color = Color(
					"#ffffff"
				)

			_:
				flower_color = Color(
					"#b9a4ff"
				)

		draw_circle(
			flower,
			7.0,
			flower_color
		)

		draw_circle(
			flower,
			2.5,
			Color("#f2b84b")
		)

	# =====================================================
	# BORDA
	# =====================================================

	draw_rect(
		Rect2(
			0.0,
			0.0,
			WORLD_WIDTH,
			WORLD_HEIGHT
		),
		Color(
			0.11,
			0.22,
			0.14,
			0.65
		),
		false,
		20.0
	)
