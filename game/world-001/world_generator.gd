class_name WorldGenerator
extends RefCounted


# =========================================================
# WORLD CONFIGURATION
# =========================================================

const WORLD_SEED: int = 1001

const CELL_SIZE: int = 64

const GRID_WIDTH: int = 48
const GRID_HEIGHT: int = 48

const WORLD_WIDTH: int = GRID_WIDTH * CELL_SIZE
const WORLD_HEIGHT: int = GRID_HEIGHT * CELL_SIZE


enum TerrainType {
	GRASS,
	WATER
}


# =========================================================
# GENERATION SETTINGS
# =========================================================

const WATER_THRESHOLD: float = -0.30

# Mantém uma região segura no centro para spawn inicial.
const SAFE_CENTER_RADIUS: int = 10


# =========================================================
# STATE
# =========================================================

var terrain_noise := FastNoiseLite.new()

var terrain_grid: Array = []

var rng := RandomNumberGenerator.new()


# =========================================================
# INITIALIZATION
# =========================================================

func _init():
	configure_noise()

	generate_world()


func configure_noise():
	terrain_noise.seed = WORLD_SEED

	terrain_noise.noise_type = (
		FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	)

	terrain_noise.frequency = 0.055

	terrain_noise.fractal_type = (
		FastNoiseLite.FRACTAL_FBM
	)

	terrain_noise.fractal_octaves = 3

	rng.seed = WORLD_SEED


# =========================================================
# WORLD GENERATION
# =========================================================

func generate_world():
	terrain_grid.clear()

	for y in range(GRID_HEIGHT):
		var row: Array = []

		for x in range(GRID_WIDTH):
			var terrain = generate_cell(
				x,
				y
			)

			row.append(
				terrain
			)

		terrain_grid.append(
			row
		)


func generate_cell(
	x: int,
	y: int
) -> TerrainType:

	# -----------------------------------------------------
	# Região central garantidamente navegável.
	# -----------------------------------------------------

	var center = Vector2i(
		GRID_WIDTH / 2,
		GRID_HEIGHT / 2
	)

	var cell = Vector2i(
		x,
		y
	)

	if (
		cell.distance_to(center)
		<= SAFE_CENTER_RADIUS
	):
		return TerrainType.GRASS

	# -----------------------------------------------------
	# Terreno procedural.
	# -----------------------------------------------------

	var noise_value = terrain_noise.get_noise_2d(
		float(x),
		float(y)
	)

	if noise_value < WATER_THRESHOLD:
		return TerrainType.WATER

	return TerrainType.GRASS


# =========================================================
# TERRAIN QUERIES
# =========================================================

func get_terrain(
	cell: Vector2i
) -> TerrainType:

	if not is_cell_inside_world(
		cell
	):
		return TerrainType.WATER

	return terrain_grid[cell.y][cell.x]


func is_walkable_cell(
	cell: Vector2i
) -> bool:

	if not is_cell_inside_world(
		cell
	):
		return false

	return (
		get_terrain(cell)
		== TerrainType.GRASS
	)


func is_cell_inside_world(
	cell: Vector2i
) -> bool:

	return (
		cell.x >= 0
		and cell.y >= 0
		and cell.x < GRID_WIDTH
		and cell.y < GRID_HEIGHT
	)


# =========================================================
# COORDINATE CONVERSION
# =========================================================

func world_to_cell(
	world_position: Vector2
) -> Vector2i:

	return Vector2i(
		int(
			floor(
				world_position.x
				/ CELL_SIZE
			)
		),
		int(
			floor(
				world_position.y
				/ CELL_SIZE
			)
		)
	)


func cell_to_world(
	cell: Vector2i
) -> Vector2:

	return Vector2(
		cell.x * CELL_SIZE
		+ CELL_SIZE / 2.0,

		cell.y * CELL_SIZE
		+ CELL_SIZE / 2.0
	)


func is_walkable_position(
	world_position: Vector2
) -> bool:

	var cell = world_to_cell(
		world_position
	)

	return is_walkable_cell(
		cell
	)


# =========================================================
# VALID POSITIONS
# =========================================================

func get_random_walkable_position() -> Vector2:
	for attempt in range(500):

		var cell = Vector2i(
			rng.randi_range(
				1,
				GRID_WIDTH - 2
			),
			rng.randi_range(
				1,
				GRID_HEIGHT - 2
			)
		)

		if is_walkable_cell(
			cell
		):
			return cell_to_world(
				cell
			)

	# Fallback seguro.
	return Vector2(
		WORLD_WIDTH / 2.0,
		WORLD_HEIGHT / 2.0
	)

# =========================================================
# PATH VALIDATION
# =========================================================

func is_path_walkable(
	from_position: Vector2,
	to_position: Vector2,
	sample_distance: float = 24.0
) -> bool:

	var distance = from_position.distance_to(
		to_position
	)

	if distance <= 0.0:
		return is_walkable_position(
			from_position
		)

	var steps = max(
		1,
		int(
			ceil(
				distance / sample_distance
			)
		)
	)

	for i in range(steps + 1):
		var progress = (
			float(i)
			/ float(steps)
		)

		var sample_position = from_position.lerp(
			to_position,
			progress
		)

		if not is_walkable_position(
			sample_position
		):
			return false

	return true


func get_random_walkable_position_near(
	origin: Vector2,
	max_distance: float = 420.0
) -> Vector2:

	for attempt in range(100):
		var angle = rng.randf_range(
			0.0,
			TAU
		)

		var distance = rng.randf_range(
			100.0,
			max_distance
		)

		var candidate = (
			origin
			+ Vector2.RIGHT.rotated(angle)
			* distance
		)

		candidate.x = clamp(
			candidate.x,
			64.0,
			float(WORLD_WIDTH) - 64.0
		)

		candidate.y = clamp(
			candidate.y,
			64.0,
			float(WORLD_HEIGHT) - 64.0
		)

		if not is_walkable_position(
			candidate
		):
			continue

		if not is_path_walkable(
			origin,
			candidate
		):
			continue

		return candidate

	# Se não encontrar caminho seguro,
	# permanece onde está.
	return origin

# =========================================================
# STABLE TREE ID
# =========================================================

func get_tree_id_from_position(
	world_position: Vector2
) -> String:

	var cell := world_to_cell(
		world_position
	)

	return (
		"tree_%02d_%02d"
		% [
			cell.x,
			cell.y
		]
	)
	
# =========================================================
# PROCEDURAL TREES
# =========================================================

func has_walkable_clearance(
	cell: Vector2i,
	radius_cells: int = 1
) -> bool:

	for offset_y in range(
		-radius_cells,
		radius_cells + 1
	):
		for offset_x in range(
			-radius_cells,
			radius_cells + 1
		):
			var nearby_cell := Vector2i(
				cell.x + offset_x,
				cell.y + offset_y
			)

			if not is_walkable_cell(
				nearby_cell
			):
				return false

	return true

func get_procedural_tree_positions(
	count: int = 80,
	min_distance: float = 95.0
) -> Array[Vector2]:

	var positions: Array[Vector2] = []

	# RNG exclusivo da vegetação.
	# Assim a posição das árvores não depende
	# do movimento dos Citizens.
	var tree_rng := RandomNumberGenerator.new()

	tree_rng.seed = (
		WORLD_SEED
		+ 2718
	)

	var world_center := Vector2(
		WORLD_WIDTH / 2.0,
		WORLD_HEIGHT / 2.0
	)

	var attempts: int = 0

	var max_attempts: int = (
		count * 100
	)

	while (
		positions.size() < count
		and attempts < max_attempts
	):
		attempts += 1

		var cell := Vector2i(
			tree_rng.randi_range(
				1,
				GRID_WIDTH - 2
			),
			tree_rng.randi_range(
				1,
				GRID_HEIGHT - 2
			)
		)

		# Árvores somente em terra.
		if not is_walkable_cell(
			cell
		):
			continue
			
		# Árvores de recurso precisam ter
		# espaço terrestre ao redor.
		if not has_walkable_clearance(
			cell,
			1
		):
			continue

		var candidate := cell_to_world(
			cell
		)

		# Pequena variação dentro da célula
		# para evitar aparência de grade.
		var jitter: float = (
			float(CELL_SIZE)
			* 0.30
		)

		candidate += Vector2(
			tree_rng.randf_range(
				-jitter,
				jitter
			),
			tree_rng.randf_range(
				-jitter,
				jitter
			)
		)

		# Mantemos o centro mais aberto.
		if candidate.distance_to(
			world_center
		) < 420.0:
			continue

		# Evita árvores sobrepostas.
		var too_close: bool = false

		for existing_position in positions:
			if existing_position.distance_to(
				candidate
			) < min_distance:
				too_close = true
				break

		if too_close:
			continue

		positions.append(
			candidate
		)

	return positions
