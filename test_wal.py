from pxr import Usd, UsdGeom, Gf

# 打开现有的USD文件
stage = Usd.Stage.Open("/home/zgao/house_usd_yup/train_5/house_train_5_processed.usda")
original_mesh_path = "/World/Structure/Walls/Mesh_Wall_7_3"


def create_shifted_mesh(stage, original_mesh, shift_vector, new_mesh_path):
    """沿指定向量移动原始Mesh，创建一个新的Mesh"""
    old_points = original_mesh.GetPointsAttr().Get()
    new_points = [Gf.Vec3f(p[0], p[1], p[2]) + shift_vector for p in old_points]
    
    new_mesh = UsdGeom.Mesh.Define(stage, new_mesh_path)
    new_mesh.GetPointsAttr().Set(new_points)
    new_mesh.GetFaceVertexCountsAttr().Set(original_mesh.GetFaceVertexCountsAttr().Get())
    new_mesh.GetFaceVertexIndicesAttr().Set(original_mesh.GetFaceVertexIndicesAttr().Get())

    return new_mesh
# 获取原始的平面Mesh
original_mesh_prim = stage.GetPrimAtPath(original_mesh_path)

if not original_mesh_prim:
    print(f"Mesh at path '{original_mesh_path}' not found.")
else:
    original_mesh = UsdGeom.Mesh(original_mesh_prim)
    
    # 获取法线（假设每个顶点的法线相同，使用第一个法线即可）
    normals_attr = original_mesh.GetNormalsAttr()
    normals = normals_attr.Get()
    normal = Gf.Vec3f(*normals[0])  # 使用第一个法线向量
    
    # 定义移动距离
    shift_distance = 0.05
    
    # 生成沿正法线方向移动的平面
    mesh1_path = "/World/Structure/Walls/ShiftedPlane_Positive"
    shift_vector_positive = normal * shift_distance
    mesh1 = create_shifted_mesh(stage, original_mesh, shift_vector_positive, mesh1_path)
    
    # 生成沿负法线方向移动的平面
    mesh2_path = "/World/Structure/Walls/ShiftedPlane_Negative"
    shift_vector_negative = -normal * shift_distance
    mesh2 = create_shifted_mesh(stage, original_mesh, shift_vector_negative, mesh2_path)
    
    # 获取移动后的两个Mesh的顶点数据
    mesh1_points = mesh1.GetPointsAttr().Get()
    mesh2_points = mesh2.GetPointsAttr().Get()
    
    # 创建一个新的矩形体的Mesh
    rectangular_mesh_path = "/World/Structure/Walls/Rectangular_Prism_With_Hole"
    rectangular_mesh = UsdGeom.Mesh.Define(stage, rectangular_mesh_path)
    
    # 合并两个平面的顶点数据
    combined_points = mesh1_points + mesh2_points
    rectangular_mesh.GetPointsAttr().Set(combined_points)
    
    # 设置面数据
    face_vertex_counts = []
    face_vertex_indices = []
    
    # 获取原始Mesh的面数据
    original_face_counts = original_mesh.GetFaceVertexCountsAttr().Get()
    original_face_indices = original_mesh.GetFaceVertexIndicesAttr().Get()
    num_faces = len(original_face_counts)
    num_vertices_per_face = original_face_counts[0]  # 假设每个面顶点数量相同

    for i in range(num_faces):
        # 前面（Mesh1）
        face_vertex_indices += [i * num_vertices_per_face + j for j in range(original_face_counts[i])]
        face_vertex_counts.append(original_face_counts[i])
        
        # 后面（Mesh2）
        face_vertex_indices += [len(mesh1_points) + i * num_vertices_per_face + j for j in range(original_face_counts[i])]
        face_vertex_counts.append(original_face_counts[i])
        
        # 侧面连接前后顶点
        for j in range(original_face_counts[i]):
            k = (j + 1) % original_face_counts[i]
            face_vertex_indices += [
                i * num_vertices_per_face + j,
                len(mesh1_points) + i * num_vertices_per_face + j,
                len(mesh1_points) + i * num_vertices_per_face + k,
                i * num_vertices_per_face + k
            ]
            face_vertex_counts.append(4)  # 侧面是四个顶点

    # 设置矩形体的面顶点数量和顶点索引
    rectangular_mesh.GetFaceVertexCountsAttr().Set(face_vertex_counts)
    rectangular_mesh.GetFaceVertexIndicesAttr().Set(face_vertex_indices)
    

    # # stage.GetRootLayer().Save()
    new_file_path = f'/home/zgao/house_usd_yup/train_5/wall_test.usda'
    stage.GetRootLayer().Export(new_file_path)

print(f"Rectangular prism created at '{rectangular_mesh_path}' by shifting the original plane mesh.")