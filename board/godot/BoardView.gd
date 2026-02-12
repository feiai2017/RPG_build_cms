extends Node2D

var board_data = {}
var nodes = []
var edges = []
var rings = []
var node_map = {}
var hovered_id = ""

var element_colors = {
    "金": Color("#E6E6E6"),
    "木": Color("#39D98A"),
    "水": Color("#3AA0FF"),
    "火": Color("#FF4D4D"),
    "土": Color("#FFD166")
}

func _ready():
    load_board()
    set_process(true)

func load_board():
    var file = FileAccess.open("res://board.json", FileAccess.READ)
    if file == null:
        push_error("board.json not found")
        return
    var text = file.get_as_text()
    board_data = JSON.parse_string(text)
    nodes = board_data.get("nodes", [])
    edges = board_data.get("edges", [])
    rings = board_data.get("rings", [])
    for n in nodes:
        node_map[n["id"]] = n
    queue_redraw()

func _process(_delta):
    var mouse = get_local_mouse_position()
    hovered_id = ""
    var min_dist = 99999.0
    for n in nodes:
        var pos = Vector2(n["x"], n["y"])
        var d = pos.distance_to(mouse)
        if d < 12 and d < min_dist:
            min_dist = d
            hovered_id = n["id"]
    queue_redraw()

func _draw():
    # rings
    for r in rings:
        if r["id"] == "core":
            continue
        draw_circle(Vector2.ZERO, r["radius"], Color(0.16, 0.2, 0.25, 0.45))

    # edges
    for e in edges:
        var a = node_map.get(e["a"])
        var b = node_map.get(e["b"])
        if a == null or b == null:
            continue
        var col = Color(0.5, 0.6, 0.7, 0.22)
        if e["kind"] == "radial":
            col = Color(0.5, 0.65, 0.75, 0.3)
        elif e["kind"] == "special":
            col = Color(0.6, 0.7, 0.8, 0.38)
        draw_line(Vector2(a["x"], a["y"]), Vector2(b["x"], b["y"]), col, 1.2)

    # nodes
    for n in nodes:
        var pos = Vector2(n["x"], n["y"])
        var element = n["element"]
        var color = element_colors.get(element, Color(0.6, 0.7, 0.8))
        var t = n["type"]
        var size = 6
        if t == "medium":
            size = 9
        elif t == "keystone":
            size = 12
        elif t == "socket":
            size = 10
        elif t == "bridge" or t == "convert":
            size = 9
        elif t == "core":
            size = 14
        var outline = color
        if n["id"] == hovered_id:
            outline = Color(0.7, 0.9, 1.0)

        if t == "small":
            draw_circle(pos, size * 0.5, Color(0, 0, 0, 0))
            draw_arc(pos, size * 0.5, 0, TAU, 32, outline, 1.3)
        elif t == "medium":
            draw_circle(pos, size * 0.6, outline)
        elif t == "keystone":
            draw_polygon(hex_points(pos, size * 0.7), [outline])
        elif t == "socket":
            draw_circle(pos, size * 0.55, Color(0, 0, 0, 0))
            draw_arc(pos, size * 0.55, 0, TAU, 32, outline, 1.4)
            draw_circle(pos, size * 0.2, outline)
        elif t == "bridge":
            draw_rect(Rect2(pos - Vector2(size * 0.4, size * 0.4), Vector2(size * 0.8, size * 0.8)), outline)
        elif t == "convert":
            draw_polygon(diamond_points(pos, size * 0.6), [outline])
        elif t == "core":
            draw_circle(pos, size * 0.8, Color(0.6, 0.9, 1.0, 0.8))
            draw_arc(pos, size * 0.8, 0, TAU, 48, outline, 2.0)

    # labels
    var font = ThemeDB.fallback_font
    if font != null:
        for i in range(board_data.get("meta", {}).get("elements", []).size()):
            var element = board_data.get("meta", {}).get("elements", [])[i]
            var angle = i * TAU / 5.0 + TAU / 10.0
            var radius = rings[3]["radius"] + 30
            var pos = Vector2(cos(angle), sin(angle)) * radius
            draw_string(font, pos, element, Color(0.9, 0.95, 1.0), 18)

func hex_points(center: Vector2, radius: float) -> PackedVector2Array:
    var pts: PackedVector2Array = []
    for i in range(6):
        var ang = deg_to_rad(60 * i - 30)
        pts.append(center + Vector2(cos(ang), sin(ang)) * radius)
    return pts

func diamond_points(center: Vector2, radius: float) -> PackedVector2Array:
    return PackedVector2Array([
        center + Vector2(0, -radius),
        center + Vector2(radius, 0),
        center + Vector2(0, radius),
        center + Vector2(-radius, 0),
    ])
