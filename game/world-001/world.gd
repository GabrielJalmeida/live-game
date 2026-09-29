extends Node2D


const WORLD_WIDTH = 3000
const WORLD_HEIGHT = 3000

const CITIZEN_SCENE = preload("res://citizen.tscn")

var simulated_user_counter: int = 1
var population: int = 0
var event_history: Array[String] = []
var world_day: int = 1
var websocket = WebSocketPeer.new()

func _ready():
	queue_redraw()

	$CitizensRequest.request_completed.connect(
		_on_citizens_request_completed
	)

	$RoseRequest.request_completed.connect(
		_on_rose_request_completed
	)
	
	connect_websocket()
	load_citizens_from_backend()

func connect_websocket():
	var error = websocket.connect_to_url(
		"ws://127.0.0.1:8000/ws/world"
	)

	if error != OK:
		push_error("Não foi possível iniciar o WebSocket.")


func _process(_delta):
	websocket.poll()

	var state = websocket.get_ready_state()

	if state == WebSocketPeer.STATE_OPEN:
		while websocket.get_available_packet_count() > 0:
			var packet = websocket.get_packet()
			var text = packet.get_string_from_utf8()

			handle_websocket_message(text)

	if state == WebSocketPeer.STATE_OPEN:
		while websocket.get_available_packet_count() > 0:
			var packet = websocket.get_packet()
			var text = packet.get_string_from_utf8()

			handle_websocket_message(text)

func handle_websocket_message(message: String):
	var data = JSON.parse_string(message)

	if typeof(data) != TYPE_DICTIONARY:
		push_error("Mensagem WebSocket inválida.")
		return

	if not data.has("type"):
		return

	if data["type"] == "citizen_spawned":
		handle_citizen_spawned(data)

func handle_citizen_spawned(data):
	if not data.has("citizen"):
		return

	var citizen_data = data["citizen"]

	spawn_citizen_from_backend(citizen_data)

	var username = str(citizen_data["name"])

	show_spawn_message(username)
	add_event("🌹 " + username + " nasceu no mundo")

	print("📡 Citizen recebido por WebSocket: ", username)

func add_event(message: String):
	event_history.push_front(message)

	if event_history.size() > 4:
		event_history.pop_back()

	$HUD/EventFeed.text = "\n".join(event_history)

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

func load_citizens_from_backend():
	var url = "http://127.0.0.1:8000/api/v1/citizens"

	var error = $CitizensRequest.request(url)

	if error != OK:
		push_error("Não foi possível iniciar a requisição de cidadãos.")

func _on_citizens_request_completed(
	result,
	response_code,
	headers,
	body
):
	if result != HTTPRequest.RESULT_SUCCESS:
		push_error("Falha ao conectar com o backend.")
		return

	if response_code != 200:
		push_error(
			"Backend respondeu com código: " +
			str(response_code)
		)
		return

	var data = JSON.parse_string(
		body.get_string_from_utf8()
	)

	if typeof(data) != TYPE_ARRAY:
		push_error("Resposta de cidadãos inválida.")
		return

	for citizen_data in data:
		spawn_citizen_from_backend(citizen_data)

	print(
		"Citizens carregados do backend: ",
		data.size()
	)

func spawn_citizen_from_backend(data):
	var citizen = CITIZEN_SCENE.instantiate()

	citizen.citizen_name = str(data["name"])

	citizen.position = Vector2(
		float(data["x"]),
		float(data["y"])
	)

	add_child(citizen)

	population += 1
	update_population()

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

	var url = "http://127.0.0.1:8000/api/v1/dev/events/rose"

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
		push_error("Não foi possível enviar a Rosa para o backend.")

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

func _on_rose_request_completed(
	result,
	response_code,
	_headers,
	_body
):
	if result != HTTPRequest.RESULT_SUCCESS:
		push_error("Falha ao enviar Rosa ao backend.")
		return

	if response_code != 200:
		push_error(
			"Backend respondeu à Rosa com código: " +
			str(response_code)
		)
		return

	print("🌹 Rosa aceita pelo backend.")
