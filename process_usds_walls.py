from pxr import Usd, UsdGeom, Gf, Sdf

def apply_transform(points, transform_matrix):
    """应用变换矩阵到点阵列"""
    transformed_points = [Gf.Vec3f(transform_matrix.Transform(Gf.Vec4f(p[0], p[1], p[2], 1))) for p in points]
    return transformed_points

def connect_meshes(stage, mesh1_prim, mesh2_prim, new_mesh_path):
    """连接两个Mesh并生成一个新的带厚度的矩形体"""
    mesh1 = UsdGeom.Mesh(mesh1_prim)
    mesh2 = UsdGeom.Mesh(mesh2_prim)
    
    # 获取顶点数据并应用变换
    mesh1_points = mesh1.GetPointsAttr().Get()
    mesh1_transform = Gf.Matrix4d(mesh1_prim.GetAttribute('xformOp:transform').Get())
    mesh1_points = apply_transform(mesh1_points, mesh1_transform)
    
    mesh2_points = mesh2.GetPointsAttr().Get()
    mesh2_transform = Gf.Matrix4d(mesh2_prim.GetAttribute('xformOp:transform').Get())
    mesh2_points = apply_transform(mesh2_points, mesh2_transform)
    
    # 合并顶点数据
    combined_points = mesh1_points + mesh2_points
    
    # 创建新的Mesh
    new_mesh = UsdGeom.Mesh.Define(stage, new_mesh_path)
    new_mesh.GetPointsAttr().Set(combined_points)
    
    # 设置面的顶点索引
    face_vertex_counts = []
    face_vertex_indices = []
    
    num_vertices_per_face = 3  # 原始面是三角形
    num_faces = len(mesh1.GetFaceVertexCountsAttr().Get())
    
    # 添加前后两个面的顶点索引
    for i in range(num_faces):
        face_vertex_indices += [i * num_vertices_per_face + j for j in range(num_vertices_per_face)]
        face_vertex_counts.append(num_vertices_per_face)
        
        face_vertex_indices += [len(mesh1_points) + i * num_vertices_per_face + j for j in range(num_vertices_per_face)]
        face_vertex_counts.append(num_vertices_per_face)
    
    # 连接侧面的顶点
    for i in range(num_vertices_per_face):
        j = (i + 1) % num_vertices_per_face
        face_vertex_indices += [
            i, j, len(mesh1_points) + j, len(mesh1_points) + i
        ]
        face_vertex_counts.append(4)  # 侧面是四边形
    
    new_mesh.GetFaceVertexCountsAttr().Set(face_vertex_counts)
    new_mesh.GetFaceVertexIndicesAttr().Set(face_vertex_indices)
    
    # 设置法线
    new_mesh_normals = mesh1.GetNormalsAttr().Get() + mesh2.GetNormalsAttr().Get()
    new_mesh.GetNormalsAttr().Set(new_mesh_normals)
    
    return new_mesh
# 打开现有的USD文件
stage = Usd.Stage.Open("/home/zgao/house_usd_yup/train_5/house_train_5_processed.usda")

# 获取两个Mesh的Prim
mesh1_prim = stage.GetPrimAtPath("/World/Structure/Walls/Mesh_Wall_7_3")
mesh2_prim = stage.GetPrimAtPath("/World/Structure/Walls/Mesh_Wall_exterior_2")

# 连接两个Mesh生成一个新的矩形体
new_mesh_path = "/World/Structure/Walls/Connected_Wall"
new_mesh = connect_meshes(stage, mesh1_prim, mesh2_prim, new_mesh_path)


# # 保存修改后的USD文件
# # stage.GetRootLayer().Save()
new_file_path = f'/home/zgao/house_usd_yup/train_5/wall_test.usda'
stage.GetRootLayer().Export(new_file_path)
print("Walls have been set to double-sided in 'wall_test.usda'.")
