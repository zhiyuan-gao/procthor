from pxr import Usd, UsdGeom, Gf

# 指定文件路径
usd_file = "/home/zgao/livRoom_usd/temp2/house_temp2_rg.usda"
output_file = "/home/zgao/livRoom_usd/temp2/test001.usda"
table_path = "/World/Objects/__0_0"
cup_path = "/World/Objects/small_2_1"


# 打开USD场景
stage = Usd.Stage.Open(usd_file)

# 获取杯子和桌子的参考
cup = UsdGeom.Xformable(stage.GetPrimAtPath(cup_path))
table = UsdGeom.Xformable(stage.GetPrimAtPath(table_path))

# 获取边界框，指定purpose为"default"
cup_bounds = cup.ComputeWorldBound(Usd.TimeCode.Default(), "default").GetBox()
table_bounds = table.ComputeWorldBound(Usd.TimeCode.Default(), "default").GetBox()

# 计算需要移动的距离，沿Y轴对齐
distance_to_move = table_bounds.GetMax()[1] - cup_bounds.GetMin()[1]

# 获取杯子的Prim对象
cup_prim = cup.GetPrim()

# 获取当前的变换矩阵属性
transform_attr = cup_prim.GetAttribute('xformOp:transform')
if transform_attr:
    current_transform = transform_attr.Get()
    # 将当前的矩阵变换为列表以便于修改
    new_transform = Gf.Matrix4d(current_transform)
    # 直接更新矩阵的平移分量
    new_transform.SetRow(3, Gf.Vec4d(new_transform.GetRow(3)[0], new_transform.GetRow(3)[1] + distance_to_move, new_transform.GetRow(3)[2], new_transform.GetRow(3)[3]))
    transform_attr.Set(new_transform)

# 保存修改到新的文件
stage.Export(output_file)