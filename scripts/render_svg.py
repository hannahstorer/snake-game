import json

CELL_SIZE = 11
CELL_GAP = 3
RADIUS = 2 # how rounded the corners are
FRAME_MS = 220 # speed per step

THEMES = {
    "dark": { #github darkmode colors
        "bg": "transparent",
        "empty": "#161b22",
        "levels": ["#0e4429", "#006d32", "#26a641", "#39d353"],
        "head": "#ffb6c1",
        "body": "#ff9fb0",
    },
    "light": { #github lightmode colors
        "bg": "transparent",
        "empty": "#ebedf0",
        "levels": ["#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "head": "#ff85a2",
        "body": "#ffaebc",
    },
}
# separate contributions into 1-4 which is how github does it so it looks the same as the actual contribution graph
def level(count, max_count):
    if count <= 0 or max_count <= 0:
        return 0
    ratio = count / max_count
    if ratio <= 0.25:
        return 1
    if ratio <= 0.5:
        return 2
    if ratio <= 0.75:
        return 3
    return 4

# turns frames into animated svg with css keyframes
def render(grid, frames, theme_name):
    theme = THEMES[theme_name]
    width = len(grid) * (CELL_SIZE + CELL_GAP) + CELL_GAP
    height = 7 * (CELL_SIZE + CELL_GAP) + CELL_GAP
    duration = (len(frames) * FRAME_MS) / 1000 # animation total time (seconds)

    def xy(week, day):
        return CELL_GAP + week * (CELL_SIZE + CELL_GAP), CELL_GAP + day * (CELL_SIZE + CELL_GAP)

    svg = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    svg.append(f'<rect width="100%" height="100%" fill="{theme["bg"]}" />')
    svg.append("<style>")
# set cell color based on contribution level from before
    max_count = max((c for col in grid for c in col), default=0)
    colors = {}
    for week, col in enumerate(grid):
        for day, count in enumerate(col):
            lvl = level(count, max_count)
            color = theme["levels"][lvl - 1] if lvl else theme["empty"]
            colors[(week, day)] = color
            svg.append(f"#c-{week}-{day} {{ fill: {color}; }}")
    # find when the cell is eaten
    eaten_at = {}
    for i, frame in enumerate(frames):
        for (w, d) in frame["eaten"]:
            eaten_at.setdefault((w, d), i)
    # fade cell at eaten time and make sure it stays faded before animation starts over
    for (w, d), idx in eaten_at.items():
        pct = (idx / len(frames)) * 100
        name = f"eat-{w}-{d}"
        orig = colors[(w, d)]
        svg.append(
            f"@keyframes {name} {{ 0% {{ fill: {orig}; }} {pct:.3f}% {{ fill: {orig}; }} "
            f"{min(pct + 1, 100):.3f}% {{ fill: {theme['empty']}; }} 100% {{ fill: {theme['empty']}; }} }}"
        )
        svg.append(f"#c-{w}-{d} {{ animation: {name} {duration:.2f}s linear infinite; }}")
    n_body = max((len(f["body"]) for f in frames), default=0) # total body blocks
    # steps(1) makes the movement blocky instead of smooth
    head_kf = []
    for i, frame in enumerate(frames):
        pct = (i / len(frames)) * 100
        x, y = xy(*frame["head"])
        head_kf.append(f"{pct:.3f}% {{ x: {x}px; y: {y}px; }}")
    lx, ly = xy(*frames[-1]["head"])
    head_kf.append(f"100% {{ x: {lx}px; y: {ly}px; }}")
    svg.append("@keyframes snake-head { " + " ".join(head_kf) + " }")
    svg.append(f"#snake-head {{ animation: snake-head {duration:.2f}s steps(1) infinite; }}")
# one keyframe for each body block and hide the keyframes that arent on grid yet by turning the opacity to 0
    for seg in range(n_body):
        kf = []
        for i, frame in enumerate(frames):
            pct = (i / len(frames)) * 100
            body = frame["body"]
            back = n_body - seg
            if len(body) >= back:
                x, y = xy(*body[-back])
                opacity = 1
            else:
                x, y, opacity = -50, -50, 0
            kf.append(f"{pct:.3f}% {{ x: {x}px; y: {y}px; opacity: {opacity}; }}") # loop ends at last position
        svg.append(f"@keyframes snake-body-{seg} {{ " + " ".join(kf) + " }")
        svg.append(f"#snake-body-{seg} {{ animation: snake-body-{seg} {duration:.2f}s steps(1) infinite; }}")
    svg.append("</style>")
# draw grid, body, and head
    for week, col in enumerate(grid):
        for day in range(7):
            x, y = xy(week, day)
            svg.append(f'<rect id="c-{week}-{day}" x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="{RADIUS}" ry="{RADIUS}" />')
# keyframes put body on canvas
    for seg in range(n_body):
        svg.append(f'<rect id="snake-body-{seg}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="{RADIUS}" ry="{RADIUS}" fill="{theme["body"]}" x="-50" y="-50" />')
    svg.append(f'<rect id="snake-head" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="{RADIUS}" ry="{RADIUS}" fill="{theme["head"]}" x="-50" y="-50" />')
    svg.append("</svg>")
    return "\n".join(svg)


if __name__ == "__main__":
    with open("frames.json") as f:
        data = json.load(f)

    outputs = {"dark": "snake_darkmode.svg", "light": "snake_lightmode.svg"}
    for theme_name, filename in outputs.items():
        svg = render(data["grid"], data["frames"], theme_name)
        path = f"dist/{filename}"
        with open(path, "w") as f:
            f.write(svg)
        print(f"wrote {path}")