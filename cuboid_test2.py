from pxr import Usd, UsdGeom, Sdf, Gf

# 假设你已经打开了 USD Stage
stage = Usd.Stage.Open("/home/zhiyuan/Downloads/house_better_name/train_5/wall_test.usda")  # 替换为你的 USD 文件路径

# 获取原始 Mesh 的顶点位置
original_mesh = UsdGeom.Mesh.Get(stage, "/World/Mesh_Wall_7_3")
original_points = original_mesh.GetPointsAttr().Get()

# 创建一个新的 Mesh 对象
new_mesh = UsdGeom.Mesh.Define(stage, "/World/Mesh_Wall_7_3_shifted")

# 沿 Z 轴平移顶点位置
shifted_points = [Gf.Vec3f(p[0], p[1], p[2] + 0.5) for p in original_points]

# 设置新的顶点位置
new_mesh.GetPointsAttr().Set(shifted_points)

# 复制面顶点数量
new_mesh.GetFaceVertexCountsAttr().Set(original_mesh.GetFaceVertexCountsAttr().Get())

# 复制面顶点索引
new_mesh.GetFaceVertexIndicesAttr().Set(original_mesh.GetFaceVertexIndicesAttr().Get())

# 复制法线（如果需要，法线可以根据新位置重新计算）
new_mesh.GetNormalsAttr().Set(original_mesh.GetNormalsAttr().Get())

# 复制双面属性
new_mesh.GetDoubleSidedAttr().Set(original_mesh.GetDoubleSidedAttr().Get())



new_file_path = f'/home/zhiyuan/Downloads/house_better_name/train_5/wall_test1.usda'
stage.GetRootLayer().Export(new_file_path)
print("Rectangular prism with hole created in 'wall_test1.usda'.")
