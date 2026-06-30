import json
from collections import deque

TRAIL_LEN = 4 # how long the snake is (how many blocks behind the head)

def in_bounds(grid, w, d):
    return 0 <= w < len(grid) and 0 <= d < 7 # grid is always 7 days tall because a week always has 7 days

def bfs_path(grid, start, goal):
    if start == goal:
        return [start]

    queue = deque([start])
    came_from = {start: None}

    while queue:
        cur = queue.popleft()
        if cur == goal:
            break
        cw, cd = cur
        for dw, dd in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cw + dw, cd + dd)
            if nxt not in came_from and in_bounds(grid, *nxt):
                came_from[nxt] = cur
                queue.append(nxt)

    if goal not in came_from:
        return None # grid has no obstacles so shouldn't happen
# have to reverse to find the path because came_from only goes backwards
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path

def nearest_target(grid, start, eaten, targets):
    # stop at first uneaten cell
    # finds closest cell so the movement looks like someone playing the game vs just finding any uneaten cell
    if start in targets and start not in eaten:
        return start

    queue = deque([start])
    visited = {start}
    while queue:
        cw, cd = queue.popleft()
        for dw, dd in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cw + dw, cd + dd)
            if nxt in visited or not in_bounds(grid, *nxt):
                continue
            visited.add(nxt)
            if nxt in targets and nxt not in eaten:
                return nxt
            queue.append(nxt)
    return None

def build_path(grid):
    targets = {(w, d) for w, col in enumerate(grid) for d, c in enumerate(col) if c > 0} # cells with at least one contribution
    start = (0, 0)
    cells = [start] # snake's path
    eaten = set()
    if start in targets:
        eaten.add(start)
# main loop for finding food and moving
    cur = start
    while True:
        target = nearest_target(grid, cur, eaten, targets)
        if target is None:
            break
        step = bfs_path(grid, cur, target)
        for cell in step[1:]:
            cells.append(cell)
            if cell in targets:
                eaten.add(cell)
        cur = step[-1]

    # make sure whole grid is visited and walk over unvisited cells to finish animation
    visited = set(cells)
    for week, col in enumerate(grid):
        days = range(7) if week % 2 == 0 else range(6, -1, -1) # alternate snake directions
        for day in days:
            cell = (week, day)
            if cell not in visited:
                step = bfs_path(grid, cur, cell)
                for c in step[1:]:
                    cells.append(c)
                    visited.add(c)
                cur = cell
# attach cell's contribution count for render_svg
    return [(w, d, grid[w][d]) for (w, d) in cells]

def build_frames(path):
    # make a list of frames by walking the path & recording each step
    frames = []
    eaten = []
    eaten_set = set()

    for (week, day, count) in path:
        if count > 0 and (week, day) not in eaten_set:
            eaten.append([week, day])
            eaten_set.add((week, day))
        frames.append({"head": [week, day], "eaten": list(eaten)})
    # body is the last TRAIL_LEN steps
    for i, frame in enumerate(frames):
        start = max(0, i - TRAIL_LEN)
        frame["body"] = [[w, d] for (w, d, _c) in path[start:i]]
    return frames

if __name__ == "__main__":
    with open("contributions.json") as f:
        data = json.load(f)
    path = build_path(data["grid"])
    frames = build_frames(path)
    with open("frames.json", "w") as f:
        json.dump({"grid": data["grid"], "frames": frames}, f)
    print(f"built {len(frames)} frames from {len(data['grid'])} weeks")