from pxr import Usd, UsdGeom, Gf

def create_rectangular_prism_with_through_hole(stage, path, width, height, depth, hole_width, hole_height):
    # 定义新的矩形体，包含一个矩形洞
    rect_prism = UsdGeom.Mesh.Define(stage, path)
    
    half_width = width / 2
    half_height = height / 2
    half_depth = depth / 2
    half_hole_width = hole_width / 2
    half_hole_height = hole_height / 2

    # 设置顶点
    rect_prism_points = [
        # 外部顶点 (底面)
        Gf.Vec3f(-half_width, -half_height, -half_depth),  # 0: 底部左前
        Gf.Vec3f(half_width, -half_height, -half_depth),   # 1: 底部右前
        Gf.Vec3f(half_width, half_height, -half_depth),    # 2: 底部右后
        Gf.Vec3f(-half_width, half_height, -half_depth),   # 3: 底部左后

        # 外部顶点 (顶面)
        Gf.Vec3f(-half_width, -half_height, half_depth),   # 4: 顶部左前
        Gf.Vec3f(half_width, -half_height, half_depth),    # 5: 顶部右前
        Gf.Vec3f(half_width, half_height, half_depth),     # 6: 顶部右后
        Gf.Vec3f(-half_width, half_height, half_depth),    # 7: 顶部左后

        # 内部矩形洞的顶点 (底面)
        Gf.Vec3f(-half_hole_width, -half_hole_height, -half_depth),  # 8: 底面洞左前
        Gf.Vec3f(half_hole_width, -half_hole_height, -half_depth),   # 9: 底面洞右前
        Gf.Vec3f(half_hole_width, half_hole_height, -half_depth),    # 10: 底面洞右后
        Gf.Vec3f(-half_hole_width, half_hole_height, -half_depth),   # 11: 底面洞左后

        # 内部矩形洞的顶点 (顶面)
        Gf.Vec3f(-half_hole_width, -half_hole_height, half_depth),   # 12: 顶面洞左前
        Gf.Vec3f(half_hole_width, -half_hole_height, half_depth),    # 13: 顶面洞右前
        Gf.Vec3f(half_hole_width, half_hole_height, half_depth),     # 14: 顶面洞右后
        Gf.Vec3f(-half_hole_width, half_hole_height, half_depth)     # 15: 顶面洞左后
    ]
    rect_prism.GetPointsAttr().Set(rect_prism_points)
    
    # 设置面顶点数量和索引
    rect_prism_face_vertex_counts = [
        4, 4, 4, 4,  # 外部的四个侧面
        8,            # 顶面 (带洞)
        8,            # 底面 (带洞)
        4, 4, 4, 4    # 矩形洞的四个侧面
    ]

    rect_prism_face_vertex_indices = [
        # 外部的四个侧面
        0, 1, 5, 4,  # 前面
        1, 2, 6, 5,  # 右面
        2, 3, 7, 6,  # 后面
        3, 0, 4, 7,  # 左面
        
        # 顶面 (带洞)
        4, 5, 13, 12, 7, 6, 14, 15,  # 顶面
            
        # 底面 (带洞)
        0, 1, 9, 8, 3, 2, 10, 11,  # 底面
        
        # 矩形洞的四个侧面
        8, 9, 13, 12,  # 左侧面
        9, 10, 14, 13,  # 前侧面
        10, 11, 15, 14,  # 右侧面
        11, 8, 12, 15   # 后侧面
    ]
    rect_prism.GetFaceVertexCountsAttr().Set(rect_prism_face_vertex_counts)
    rect_prism.GetFaceVertexIndicesAttr().Set(rect_prism_face_vertex_indices)
    
    # 设置法线 (根据面的方向)
    rect_prism_normals = [
        Gf.Vec3f(0, 0, 1),   # 前面
        Gf.Vec3f(1, 0, 0),   # 右面
        Gf.Vec3f(0, 0, -1),  # 后面
        Gf.Vec3f(-1, 0, 0),  # 左面

        Gf.Vec3f(0, 1, 0),   # 顶面
        Gf.Vec3f(0, -1, 0),  # 底面
        
        Gf.Vec3f(0, -1, 0),  # 矩形洞左侧面
        Gf.Vec3f(1, 0, 0),   # 矩形洞前侧面
        Gf.Vec3f(0, 1, 0),   # 矩形洞右侧面
        Gf.Vec3f(-1, 0, 0)   # 矩形洞后侧面
    ]
    rect_prism.GetNormalsAttr().Set(rect_prism_normals)



# 打开现有的USD文件
stage = Usd.Stage.Open("/home/zgao/house_usd_yup/train_5/house_train_5_processed.usda")
# original_mesh_path = "/World/Structure/Walls/Mesh_Wall_7_3"

create_rectangular_prism_with_through_hole(stage, "/World/RectangularPrismWithHole", width=4, height=4, depth=1, hole_width=2, hole_height=2)
# # stage.GetRootLayer().Save()
new_file_path = f'/home/zgao/house_usd_yup/train_5/wall_test.usda'
stage.GetRootLayer().Export(new_file_path)
print("Rectangular prism with hole created in 'rectangular_prism_with_hole.usda'.")
