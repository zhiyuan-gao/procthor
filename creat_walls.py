import numpy as np

class Wall:
    def __init__(self, id, p0, p1, height, thickness, material, empty, roomId, hole=None, layer=None):
        self.id = id
        self.p0 = np.array(p0)
        self.p1 = np.array(p1)
        self.height = height
        self.thickness = thickness
        self.material = material
        self.empty = empty
        self.roomId = roomId
        self.hole = hole
        self.layer = layer

class PolygonWall:
    def __init__(self, id, polygon, material, empty, roomId, thickness, layer=None):
        self.id = id
        self.polygon = [np.array(point) for point in polygon]  # List of points defining the polygon
        self.material = material
        self.empty = empty
        self.roomId = roomId
        self.thickness = thickness
        self.layer = layer

class WallRectangularHole:
    def __init__(self, id, asset_id, room0, room1, wall0, wall1, hole_polygon, asset_position,  scale=None, material=None):
        self.id = id
        self.asset_id = asset_id
        self.room0 = room0
        self.room1 = room1
        self.wall0 = wall0
        self.wall1 = wall1
        self.hole_polygon = [np.array(point) for point in hole_polygon]
        # print(self.hole_polygon)
        self.asset_position = np.array(asset_position)
        # self.openness = openness
        self.scale = np.array(scale) if scale else None
        self.material = material

class BoundingBox:
    def __init__(self, min_point, max_point):
        # 由于min_point和max_point是numpy数组，且包含字典，需要先将字典提取出来
        min_point_dict = min_point.item() if isinstance(min_point, np.ndarray) else min_point
        max_point_dict = max_point.item() if isinstance(max_point, np.ndarray) else max_point

        # 提取字典中的坐标值并转换为 numpy 数组
        self.min = np.array([min_point_dict['x'], min_point_dict['y'], min_point_dict['z']])
        self.max = np.array([max_point_dict['x'], max_point_dict['y'], max_point_dict['z']])

    def center(self):
        return self.min + (self.max - self.min) / 2.0

    def size(self):
        return self.max - self.min
    
def polygon_wall_to_simple_wall(wall, holes):
    # 提取 y 坐标并排序
    sorted_polygon = sorted(wall.polygon, key=lambda p: p.item()['y'])

    # 找到最大 y 坐标
    max_y = max(p.item()['y'] for p in wall.polygon)

    # 查找对应的 hole
    hole = holes.get(wall.id, None)

    # 获取排序后的前两个点
    p0 = sorted_polygon[0].item()
    p1 = sorted_polygon[1].item()

    return Wall(
        id=wall.id,
        p0=np.array([p0['x'], p0['y'], p0['z']]),
        p1=np.array([p1['x'], p1['y'], p1['z']]),
        height=max_y - p0['y'],  # 计算高度
        thickness=wall.thickness,  # 使用已存在的厚度
        material=wall.material,
        empty=wall.empty,
        roomId=wall.roomId,
        hole=hole,
        layer=wall.layer
    )



def generate_holes(house):
    windows_and_doors = house['doors'] + house['windows']

    holes = {}
    for hole in windows_and_doors:
        hole_obj = WallRectangularHole(
            id=hole['id'],
            asset_id=hole['assetId'],
            room0=hole['room0'],
            room1=hole['room1'],
            wall0=hole['wall0'],
            wall1=hole['wall1'],
            hole_polygon=hole['holePolygon'],
            asset_position=hole['assetPosition'],
            # openness=hole['openness'],
            scale=hole.get('scale'),
            material=hole.get('material')
        )
        if hole_obj.wall0:
            holes[hole_obj.wall0] = hole_obj
        if hole_obj.wall1:
            holes[hole_obj.wall1] = hole_obj
    return holes

def generate_wall_mesh(to_create, global_vertex_positions=False, back_faces=False):
    p0p1 = np.array(to_create.p1) - np.array(to_create.p0)
    p0p1_norm = p0p1 / np.linalg.norm(p0p1)

    width = np.linalg.norm(p0p1)
    height = to_create.height
    thickness = to_create.thickness
    # print(thickness)

    if global_vertex_positions:
        p0 = to_create.p0
        p1 = to_create.p1
    else:
        p0 = [-width / 2.0, -height / 2.0, -thickness / 2.0]
        p1 = [width / 2.0, -height / 2.0, -thickness / 2.0]

    vertices = []
    triangles = []

    if to_create.hole:
        hole_bb = get_hole_bounding_box(to_create.hole)
        dims = hole_bb.size()
        offset = [hole_bb.min[0], hole_bb.min[1]]

        if to_create.hole.wall1 == to_create.id:
            offset = [width - hole_bb.max[0], hole_bb.min[1]]

        vertices = [
            p0,
            [p0[0], height, p0[2]],
            [p0[0] + offset[0], offset[1], p0[2]],
            [p0[0] + offset[0], offset[1] + dims[1], p0[2]],
            [p1[0], height, p1[2]],
            [p0[0] + offset[0] + dims[0], offset[1] + dims[1], p0[2]],
            p1,
            [p0[0] + offset[0] + dims[0], offset[1], p0[2]]
        ]

        triangles = [
            0, 1, 2, 1, 3, 2, 1, 4, 3, 3, 4, 5, 4, 6, 5, 5, 6, 7, 7, 6, 0, 0, 2, 7
        ]

        if back_faces:
            triangles.extend([t for t in reversed(triangles)])
    else:
        vertices = [
            p0,
            [p0[0], height, p0[2]],
            [p1[0], height, p1[2]],
            p1
        ]

        triangles = [1, 2, 0, 2, 3, 0]

        if back_faces:
            triangles.extend([t for t in reversed(triangles)])

    return vertices, triangles

def get_hole_bounding_box(hole):
    if hole.hole_polygon is None or len(hole.hole_polygon) < 2:
        raise ValueError(f"Invalid `holePolygon` for object id: '{hole.id}'. Minimum 2 vertices indicating first min and second max of hole bounding box.")
    return BoundingBox(min_point=hole.hole_polygon[0], max_point=hole.hole_polygon[1])

def create_walls(house, material_db, procedural_parameters, game_object_id="Structure"):
    holes = generate_holes(house)

    structure = {"id": game_object_id, "walls": []}

    # Convert each wall dictionary to a PolygonWall object, and set a default thickness if missing
    walls = [PolygonWall(
                id=w['id'],
                polygon=w['polygon'],
                material=w.get('material'),
                empty=w.get('empty', False),
                roomId=w['roomId'],
                thickness=w.get('thickness', 0.0),  # 使用默认值 0.1
                layer=w.get('layer')
            ) for w in house['walls']]

    walls = [polygon_wall_to_simple_wall(w, holes) for w in walls]

    walls_per_room = {}
    for wall in walls:
        walls_per_room.setdefault(wall.roomId, []).append(wall)

    zip3 = []
    for room_walls in walls_per_room.values():
        room_zip3 = []
        n = len(room_walls)
        for i in range(n):
            w0 = room_walls[i]
            w1 = room_walls[(i + 1) % n]
            w2 = room_walls[(i - 1) % n]
            room_zip3.append((w0, w1, w2))
        zip3.append(room_zip3)

    index = 0
    for wall_tuples in zip3:
        for w0, w1, w2 in wall_tuples:
            if not w0.empty:
                vertices, triangles = generate_wall_mesh(
                    w0,
                    global_vertex_positions=procedural_parameters.get('globalVertexPositions', True),
                    back_faces=procedural_parameters.get('backFaces', False)
                )
                wall_go = {
                    "index": index,
                    "id": w0.id,
                    "vertices": vertices,
                    "triangles": triangles,
                }
                structure["walls"].append(wall_go)
                index += 1

    return structure

import json

with open('/home/zhiyuan/procthor/train_5.json') as f:
    house = json.load(f)
procedural_parameters = {
    "globalVertexPositions": True,
    "backFaces": True
}

structure = create_walls(house, material_db={}, procedural_parameters=procedural_parameters)

for wall in structure["walls"]:

    print(f"Wall ID: {wall['id']}")
    print(f"Vertices: {wall['vertices']}")
    print(f"Triangles: {wall['triangles']}")
