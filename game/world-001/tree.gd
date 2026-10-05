class_name WorldTree
extends Node2D


# =========================================================
# TREE STATE
# =========================================================

enum TreeState {
	GROWN,
	STUMP
}


var tree_id: String = ""

@export var max_wood: int = 10

# Temporário para teste.
# Depois usaremos uma escala de tempo mais apropriada.
@export var regrow_time_seconds: float = 30.0


var wood_amount: int = 10

var state: int = TreeState.GROWN

var regrow_remaining: float = 0.0


# Citizen que atualmente trabalha nesta árvore.
var reserved_by: Node = null

# No máximo um Citizen pode estar indo
# tentar roubar este spot.
var challenger_by: Node = null


# =========================================================
# READY
# =========================================================

func _ready():
	add_to_group("trees")

	wood_amount = max_wood

	queue_redraw()


# =========================================================
# PROCESS
# =========================================================

func _process(
	delta: float
):
	cleanup_references()

	if state != TreeState.STUMP:
		return

	regrow_remaining -= delta

	if regrow_remaining <= 0.0:
		regrow()


# =========================================================
# REFERENCES
# =========================================================

func cleanup_references():
	if (
		reserved_by != null
		and not is_instance_valid(reserved_by)
	):
		reserved_by = null

	if (
		challenger_by != null
		and not is_instance_valid(challenger_by)
	):
		challenger_by = null


func get_reserved_by() -> Node:
	cleanup_references()

	return reserved_by


func get_challenger_by() -> Node:
	cleanup_references()

	return challenger_by


# =========================================================
# TREE AVAILABILITY
# =========================================================

func has_wood() -> bool:
	return (
		state == TreeState.GROWN
		and wood_amount > 0
	)


func can_be_targeted(
	citizen: Node
) -> bool:

	cleanup_references()

	if not has_wood():
		return false

	if reserved_by == null:
		return true

	if reserved_by == citizen:
		return true

	return false


# =========================================================
# NORMAL RESERVATION
# =========================================================

func try_reserve(
	citizen: Node
) -> bool:

	if citizen == null:
		return false

	cleanup_references()

	if not has_wood():
		return false

	if (
		reserved_by != null
		and reserved_by != citizen
	):
		return false

	reserved_by = citizen

	return true


func release_reservation(
	citizen: Node
):
	cleanup_references()

	if reserved_by == citizen:
		reserved_by = null


# =========================================================
# CHALLENGE / RESOURCE STEAL
# =========================================================

func can_be_challenged_by(
	citizen: Node
) -> bool:

	cleanup_references()

	if citizen == null:
		return false

	if not has_wood():
		return false

	# Precisa existir alguém usando a árvore.
	if reserved_by == null:
		return false

	if reserved_by == citizen:
		return false

	# Já existe outro desafiante.
	if (
		challenger_by != null
		and challenger_by != citizen
	):
		return false

	return true


func try_register_challenge(
	citizen: Node
) -> bool:

	if not can_be_challenged_by(
		citizen
	):
		return false

	challenger_by = citizen

	return true


func cancel_challenge(
	citizen: Node
):
	cleanup_references()

	if challenger_by == citizen:
		challenger_by = null


func complete_challenge(
	citizen: Node
) -> Node:

	cleanup_references()

	if challenger_by != citizen:
		return null

	if not has_wood():
		challenger_by = null
		return null

	var previous_owner: Node = (
		reserved_by
	)

	# O ladrão só ganha a reserva AGORA,
	# depois de chegar fisicamente.
	reserved_by = citizen

	challenger_by = null

	return previous_owner


# =========================================================
# WOOD
# =========================================================

func remove_wood(
	amount: int,
	citizen: Node
) -> int:

	if amount <= 0:
		return 0

	if not has_wood():
		return 0

	# Somente o Citizen que possui
	# a reserva pode retirar madeira.
	if reserved_by != citizen:
		return 0

	var collected: int = min(
		amount,
		wood_amount
	)

	wood_amount -= collected

	if wood_amount <= 0:
		become_stump()

	queue_redraw()

	return collected


# =========================================================
# STUMP / REGENERATION
# =========================================================

func become_stump():
	wood_amount = 0

	state = TreeState.STUMP

	regrow_remaining = (
		regrow_time_seconds
	)

	reserved_by = null
	challenger_by = null

	queue_redraw()

	print(
		"🪵 ",
		tree_id,
		" virou toco."
	)


func regrow():
	state = TreeState.GROWN

	wood_amount = max_wood

	regrow_remaining = 0.0

	reserved_by = null
	challenger_by = null

	queue_redraw()

	print(
		"🌱 ",
		tree_id,
		" regenerou completamente."
	)


# =========================================================
# BACKEND SYNC
# =========================================================

func apply_backend_state(
	new_wood_amount: int,
	new_status: String,
	new_regrow_remaining: float = -1.0
):
	wood_amount = clamp(
		new_wood_amount,
		0,
		max_wood
	)

	if new_status == "STUMP":
		state = TreeState.STUMP

		# Quando o mundo acabou de carregar, o world.gd
		# pode informar exatamente quantos segundos faltam.
		# Quando este parâmetro não é enviado (ex.: corte ao vivo),
		# usamos o ciclo completo de desenvolvimento.
		if new_regrow_remaining >= 0.0:
			regrow_remaining = new_regrow_remaining
		else:
			regrow_remaining = regrow_time_seconds

		reserved_by = null
		challenger_by = null

		# Proteção caso recebamos um STUMP cujo prazo
		# já tenha acabado entre a resposta e este frame.
		if regrow_remaining <= 0.0:
			regrow()
			return

	else:
		state = TreeState.GROWN
		regrow_remaining = 0.0

	queue_redraw()


# =========================================================
# TEMPORARY VISUAL
# =========================================================

func _draw():
	# =====================================================
	# STUMP
	# =====================================================

	if state == TreeState.STUMP:
		draw_rect(
			Rect2(
				-10.0,
				-8.0,
				20.0,
				18.0
			),
			Color("#795548")
		)

		draw_circle(
			Vector2(
				0.0,
				-8.0
			),
			10.0,
			Color("#a67855")
		)

		return

	# =====================================================
	# GROWN TREE
	# =====================================================

	draw_rect(
		Rect2(
			-7.0,
			-5.0,
			14.0,
			40.0
		),
		Color("#795548")
	)

	draw_circle(
		Vector2(
			0.0,
			-22.0
		),
		28.0,
		Color("#397a46")
	)

	draw_circle(
		Vector2(
			-15.0,
			-15.0
		),
		18.0,
		Color("#448a50")
	)

	draw_circle(
		Vector2(
			15.0,
			-17.0
		),
		20.0,
		Color("#4b9457")
	)
