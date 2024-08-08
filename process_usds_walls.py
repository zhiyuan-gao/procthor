from pxr import Usd, UsdGeom, Gf

def calculate_normal(p0, p1, p2):
    """计算给定三个顶点的法线向量"""
    v1 = p1 - p0
    v2 = p2 - p0
    normal = Gf.Cross(v1, v2)
    return normal.GetNormalized()

# 打开现有的USD文件
stage = Usd.Stage.Open("/home/zgao/house_usd_yup/train_5/house_train_5_processed.usda")

# 假设已有的两个矩形Mesh分别为
front_wall_path = "/World/Structure/Walls/Mesh_Wall_7_3"
back_wall_path = "/World/Structure/Walls/Mesh_Wall_exterior_2"

# 获取前墙和后墙的Mesh
front_wall = stage.GetPrimAtPath(front_wall_path)
back_wall = stage.GetPrimAtPath(back_wall_path)

if not front_wall or not back_wall:
    print("One or both of the walls not found.")
else:
    front_mesh = UsdGeom.Mesh(front_wall)
    back_mesh = UsdGeom.Mesh(back_wall)
    
    # 获取前墙和后墙的点
    front_points = front_mesh.GetPointsAttr().Get()
    back_points = back_mesh.GetPointsAttr().Get()
    
    # 计算前墙的法线方向（假设使用前三个顶点）
    normal = calculate_normal(Gf.Vec3f(*front_points[0]), Gf.Vec3f(*front_points[1]), Gf.Vec3f(*front_points[2]))
    
    # 设置墙的厚度
    thickness = 0.5
    
    # 按照法线方向移动后墙的点
    moved_back_points = [Gf.Vec3f(p[0], p[1], p[2]) + normal * thickness for p in back_points]
    
    # 创建一个新的具有厚度的墙体的Mesh
    thick_wall_path = "/World/Structure/Walls/ThickWall"
    thick_wall = UsdGeom.Mesh.Define(stage, thick_wall_path)
    
    # 合并前墙和后墙的点
    thick_wall_points = front_points + moved_back_points
    thick_wall.GetPointsAttr().Set(thick_wall_points)
    
    # 设置墙体的面，假设每个矩形都有4个顶点，0-3为前面，4-7为后面
    thick_wall.GetFaceVertexCountsAttr().Set([4, 4, 4, 4, 4, 4])
    thick_wall.GetFaceVertexIndicesAttr().Set([
        0, 1, 2, 3,  # 前面
        4, 5, 6, 7,  # 后面
        0, 1, 5, 4,  # 底面
        2, 3, 7, 6,  # 顶面
        1, 2, 6, 5,  # 右侧面
        3, 0, 4, 7   # 左侧面
    ])
    
    # 设置Normals
    thick_wall_normals = [
        (0, 0, -1),  # 前面
        (0, 0, 1),   # 后面
        (0, -1, 0),  # 底面
        (0, 1, 0),   # 顶面
        (1, 0, 0),   # 右侧面
        (-1, 0, 0)   # 左侧面
    ]
    thick_wall.GetNormalsAttr().Set(thick_wall_normals)
    
# # 保存修改后的USD文件
# # stage.GetRootLayer().Save()
new_file_path = f'/home/zgao/house_usd_yup/train_5/wall_test.usda'
stage.GetRootLayer().Export(new_file_path)
print("Walls have been set to double-sided in 'wall_test.usda'.")
