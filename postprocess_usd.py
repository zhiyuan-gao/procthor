import json
from pxr import Usd, UsdGeom, UsdPhysics, Gf

usd_file = '/home/zgao/Downloads/house_usd_yup/train_8/house_train_8.usda'

output_file = '/home/zgao/Downloads/house_usd_yup/train_8/house_train_8_rg.usda'
# 打开JSON文件
with open('/home/zgao/procthor-10k-main/train/train_8.json', 'r') as file:
    # 加载JSON内容
    data = json.load(file)


def add_rigidbody_and_collision_to_xform(prim):
    
    UsdPhysics.RigidBodyAPI.Apply(prim)
    UsdPhysics.CollisionAPI.Apply(prim)

    rigidBodyAPI = UsdPhysics.RigidBodyAPI(prim)
    rigidBodyAPI.GetRigidBodyEnabledAttr().Set(True)


def add_rigidbody_and_collision_to_mesh(prim):

    UsdPhysics.MassAPI.Apply(prim)
    UsdPhysics.CollisionAPI.Apply(prim)

    mass_api = UsdPhysics.MassAPI(prim)
    mass_api.GetMassAttr().Set(10.0)  #set mass  =10



def process_children(children, parent_id):
    for child in children:
        # 输出子项的 ID 以及其父项的 ID
        # print(f"Child ID: {child['id']}, Parent ID: {parent_id}")

        small_obj_name = child['id'].replace("|", "_")
        small_obj_path = "/World/Objects/" + small_obj_name
        small_obj_prim = stage.GetPrimAtPath(small_obj_path)
        small_obj = UsdGeom.Xformable(small_obj_prim)

        receptacle_name = parent_id.replace("|", "_")
        receptacle_path = "/World/Objects/" + receptacle_name
        receptacle_prim = stage.GetPrimAtPath(receptacle_path)
        receptacle = UsdGeom.Xformable(receptacle_prim)


        add_rigidbody_and_collision_to_xform(small_obj_prim)

        # 获取边界框，指定purpose为"default"
        small_obj_bounds = small_obj.ComputeWorldBound(Usd.TimeCode.Default(), "default").GetBox()
        receptacle_bounds = receptacle.ComputeWorldBound(Usd.TimeCode.Default(), "default").GetBox()

        # 计算需要移动的距离，沿Y轴对齐
        distance_to_move = receptacle_bounds.GetMax()[1] - small_obj_bounds.GetMin()[1]

        # 获取杯子的Prim对象
        small_obj_prim = small_obj.GetPrim()

        # 获取当前的变换矩阵属性
        transform_attr = small_obj_prim.GetAttribute('xformOp:transform')
        if transform_attr:
            current_transform = transform_attr.Get()
            # 将当前的矩阵变换为列表以便于修改
            new_transform = Gf.Matrix4d(current_transform)
            # 直接更新矩阵的平移分量
            new_transform.SetRow(3, Gf.Vec4d(new_transform.GetRow(3)[0], new_transform.GetRow(3)[1] + distance_to_move, new_transform.GetRow(3)[2], new_transform.GetRow(3)[3]))
            transform_attr.Set(new_transform)


        # 递归地处理存在于子项中的更深层次的 children
        if 'children' in child:
            process_children(child['children'], child['id'])


# 打开USD场景
stage = Usd.Stage.Open(usd_file)

for prim in stage.Traverse():
    
    if prim.IsA(UsdGeom.Mesh):
        add_rigidbody_and_collision_to_mesh(prim)
# 遍历每个对象，并对其子对象进行处理
for obj in data['objects']:
    if 'children' in obj:
        process_children(obj['children'], obj['id'])


# 保存修改到新的文件
stage.Export(output_file)

