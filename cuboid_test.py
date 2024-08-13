from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf

# 打开现有的USD文件
stage = Usd.Stage.Open("/home/zhiyuan/Downloads/house_better_name/train_5/house_train_5_processed.usda")

# def create_thick_wall():
# 获取现有的 /World Xform
world_xform = UsdGeom.Xform.Get(stage, "/World")

# 确保 /World Xform 存在
if not world_xform:
    raise RuntimeError("Xform /World does not exist in the USD stage")

# 在 /World Xform 下创建新的 Mesh 对象
mesh = UsdGeom.Mesh.Define(stage, "/World/Mesh_Wall_7_3_test")

# 设置顶点位置
points = [
    # face 1
    Gf.Vec3f(-3.073, -1.5854203, 0),  # 顶点 0
    Gf.Vec3f(-3.073, 1.5854203, 0),   # 顶点 1
    Gf.Vec3f(-1.20612, -0.5436654, 0),# 顶点 2
    Gf.Vec3f(-1.20612, 0.36767626, 0),# 顶点 3
    Gf.Vec3f(3.073, 1.5854203, 0),    # 顶点 4
    Gf.Vec3f(-0.2969494, 0.36767626, 0),# 顶点 5
    Gf.Vec3f(3.073, -1.5854203, 0),   # 顶点 6
    Gf.Vec3f(-0.2969494, -0.5436654, 0), # 顶点 7
    # face 2
    Gf.Vec3f(-3.073, -1.5854203, -0.1),  # 顶点 8
    Gf.Vec3f(-3.073, 1.5854203, -0.1),   # 顶点 9
    Gf.Vec3f(-1.20612, -0.5436654, -0.1),# 顶点 10
    Gf.Vec3f(-1.20612, 0.36767626, -0.1),# 顶点 11
    Gf.Vec3f(3.073, 1.5854203, -0.1),    # 顶点 12
    Gf.Vec3f(-0.2969494, 0.36767626, -0.1),# 顶点 13
    Gf.Vec3f(3.073, -1.5854203, -0.1),   # 顶点 14
    Gf.Vec3f(-0.2969494, -0.5436654, -0.1) # 顶点 15
]
mesh.GetPointsAttr().Set(points)

# 设置面顶点数量
faceVertexCounts = [3, 3, 3, 3, 3, 3, 3, 3,  #front with hole
                    3, 3, 3, 3, 3, 3, 3, 3,  #back with hole
                    3,3, #left outside
                    3,3, #right outside
                    3,3, #top outside
                    3,3, #bottom outside
                    3,3, #left inside
                    3,3, #right inside
                    3,3, #top inside
                    3,3 ]#bottom inside
mesh.GetFaceVertexCountsAttr().Set(faceVertexCounts)

# 设置面顶点索引
faceVertexIndices = [1, 0, 2, 3, 1, 2, 4, 1, 3, 4, 3, 5, 6, 4, 5, 6, 5, 7, 6, 7, 0, 2, 0, 7,#front with hole
                     
                     8, 9, 10, 9, 11, 10, 9, 12, 11, 11, 12, 13, 12, 14, 13, 13, 14, 15, 15, 14, 8, 8, 10, 15,#back with hole

                    #  9, 8, 10, 11, 9, 10, 12, 9, 11, 12, 11, 13, 14, 12, 13, 14, 13, 15, 14, 15, 8, 10, 8, 15,#back with hole

                     1, 9, 8, 1, 8, 0, #left outside
                     4, 6, 14, 4, 14, 12, #right outside
                     1, 4, 12, 1, 12, 9, #top outside
                     0, 8, 14, 0, 14, 6, #bottom outside
                     
                     2, 10, 11, 2, 11, 3, #left inside
                     5, 13, 15, 5, 15, 7, #right inside
                     11, 13, 5, 11, 5, 3, #top inside
                     2, 7, 15, 2, 15, 10, #bottom inside
                     
                     ]
mesh.GetFaceVertexIndicesAttr().Set(faceVertexIndices)

# 设置法线
normals = [
    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), 
    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), 
    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), 
    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), 
    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), 
    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), 
    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), 
    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), 
    #front with hole


    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1),
    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1),
    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1),
    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1),
    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1),
    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1),
    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1),
    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), #back with hole

    Gf.Vec3f(-1, 0, 0), Gf.Vec3f(-1, 0, 0), Gf.Vec3f(-1, 0, 0), 
    Gf.Vec3f(-1, 0, 0), Gf.Vec3f(-1, 0, 0), Gf.Vec3f(-1, 0, 0),#left outside

    Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0),
    Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0), Gf.Vec3f(1, 0, 0),#right outside

    Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0),
    Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0),#top outside

    Gf.Vec3f(0, -1, 0), Gf.Vec3f(0, -1, 0), Gf.Vec3f(0, -1, 0),
    Gf.Vec3f(0, -1, 0), Gf.Vec3f(0, -1, 0), Gf.Vec3f(0, -1, 0),#bottom outside

    Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0),
    Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0), Gf.Vec3f(0, 1, 0),#left inside

    Gf.Vec3f(0, -1, 0), Gf.Vec3f(0, -1, 0), Gf.Vec3f(0, -1, 0),
    Gf.Vec3f(0, -1, 0), Gf.Vec3f(0, -1, 0), Gf.Vec3f(0, -1, 0),#right inside

    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1),
    Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), Gf.Vec3f(0, 0, -1), #top inside

    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1),
    Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 1) #bottom inside

]
# mesh.GetNormalsAttr().Set(normals)
# mesh.GetNormalsInterpolationAttr().Set("faceVarying")

# normals_attr = mesh.GetNormalsAttr()
# normals_attr.Set(normals)
# normals_attr.SetInterpolation("faceVarying")  # 显式指定插值方式为 "vertex"

mesh.GetNormalsAttr().Set(normals)

# 显式指定法线插值方式
mesh.SetNormalsInterpolation("faceVarying")  # 选择合适的插值方式，如 "vertex", "faceVarying", "uniform", "constant"


material_global = UsdShade.Material.Get(stage, "/World/Materials/WhiteMarble__115104")
UsdShade.MaterialBindingAPI(mesh).Bind(material_global)

# /World/Materials/WhiteMarble__115104  /World/Materials/TexturesCom_WoodFine0050_1_seamless_S_white__116060

material1_path = "/World/Materials/TexturesCom_WoodFine0031_1_seamless_S__116074"
material2_path = "/World/Materials/TexturesCom_WoodFine0050_1_seamless_S_white__116060"


# 创建子集 (Subset)
subset1 = UsdGeom.Subset.Define(stage, "/World/Mesh_Wall_7_3_test/Subset1")
subset1.GetIndicesAttr().Set([0,1,2,3,4,5,6,7])  # front with hole

subset2 = UsdGeom.Subset.Define(stage, "/World/Mesh_Wall_7_3_test/Subset2")
subset2.GetIndicesAttr().Set([8,9,10,11,12,13,14,15])  # bottom with hole

# 使用 UsdShade.MaterialBindingAPI 将材质绑定到子集
UsdShade.MaterialBindingAPI(subset1).Bind(UsdShade.Material(stage.GetPrimAtPath(material1_path)))
UsdShade.MaterialBindingAPI(subset2).Bind(UsdShade.Material(stage.GetPrimAtPath(material2_path)))



# 设置双面属性
mesh.GetDoubleSidedAttr().Set(True)

# # 设置材质绑定
# material_binding = Sdf.Path("/World/Materials/WhiteMarble__115514")
# mesh.GetPrim().CreateRelationship("material:binding").SetTargets([material_binding])

# # 设置物理属性
# mesh.GetPrim().CreateAttribute("physics:mass", Sdf.ValueTypeNames.Float).Set(10.0)

# # 设置颜色（可选）
# mesh.GetDisplayColorAttr().Set([Gf.Vec3f(1, 1, 1)])

# # 设置UV坐标
# primvarsAPI = UsdGeom.PrimvarsAPI(mesh)
# stPrimvar = primvarsAPI.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
# st = [
#     Gf.Vec2f(0, -0.5), Gf.Vec2f(0, 0.5), Gf.Vec2f(0.30375528, -0.17145783),
#     Gf.Vec2f(0.30375528, 0.11595546), Gf.Vec2f(1, 0.5), Gf.Vec2f(0.45168412, 0.11595546),
#     Gf.Vec2f(1, -0.5), Gf.Vec2f(0.45168412, -0.17145783)
# ]
# stPrimvar.Set(st)

# # 设置变换矩阵
# transform = Gf.Matrix4d((
#     (-1.1920928955078125e-7, 0, -1.0000001192092896, 0),
#     (0, 1, 0, 0),
#     (1.0000001192092896, 0, -1.1920928955078125e-7, 0),
#     (0, 1.5854202508926392, -3.072999954223633, 1)
# ))
# world_xform.AddTransformOp().Set(transform)



new_file_path = f'/home/zhiyuan/Downloads/house_better_name/train_5/wall_test.usda'
stage.GetRootLayer().Export(new_file_path)
print("Rectangular prism with hole created in 'wall_test.usda'.")