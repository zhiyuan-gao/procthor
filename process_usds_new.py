from pxr import Usd, UsdGeom, UsdPhysics
import json
import re

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

        if 'children' in child:
            process_children(child['children'], child['id'])


# def rename_children(parent_path):


#     print(f"Processing children of {parent_path}")
    
#     parent_prim = stage.GetPrimAtPath(parent_path)

#     if parent_prim.GetChildren():
#         children = parent_prim.GetChildren()
#         mesh_count = {}
#         xform_count = {}
        
#         for child in children:
#             child_name = child.GetName()
#             child_type = child.GetTypeName()
            
#             if child_type == "Mesh":
#                 # 生成新的名字
#                 new_name_prefix = f"SM_{parent_prim.GetName()}_"
#                 if child_name in mesh_count:
#                     mesh_count[child_name] += 1
#                     new_name = f"{new_name_prefix}{child_name}_{mesh_count[child_name]}"
#                 else:
#                     mesh_count[child_name] = 1
#                     new_name = f"{new_name_prefix}{child_name}"
                
#                 # 重命名子对象
#                 # stage.DefinePrim(child.GetPath().ReplaceName(new_name), child_type)

#                 # new_path = child.GetPath().GetParentPath().AppendChild(new_name)
#                 stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name




#             elif child_type == "Xform":
#                 # 生成新的名字
#                 new_name_prefix = f"{parent_prim.GetName()}_"
#                 if child_name in xform_count:
#                     xform_count[child_name] += 1
#                     new_name = f"{new_name_prefix}{child_name}_{xform_count[child_name]}"
#                 else:
#                     xform_count[child_name] = 1
#                     new_name = f"{new_name_prefix}{child_name}"
                
#                 # 重命名子对象
#                 # stage.DefinePrim(child.GetPath().ReplaceName(new_name), child_type)

#                 stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name

#                 rename_children(child.GetPath())



def rename_prim(stage, prim_path, new_name):
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        print(f"Prim at path {prim_path} is not valid")
        return None
    
    parent = prim.GetParent()
    if not parent.IsValid():
        print(f"Parent of prim at path {prim_path} is not valid")
        return None
    
    prim_spec = stage.GetEditTarget().GetLayer().GetPrimAtPath(prim.GetPath())
    if prim_spec:
        new_path = prim.GetPath().GetParentPath().AppendChild(new_name)
        prim_spec.name = new_name
        return new_path
    return None

def rename_children(stage, parent_path):
    parent_prim = stage.GetPrimAtPath(parent_path)
    if not parent_prim.IsValid():
        return
    
    children = parent_prim.GetChildren()
    
    mesh_count = {}
    xform_count = {}
    
    for child in children:
        if not child.IsValid():
            continue
        
        child_name = child.GetName()
        child_type = child.GetTypeName()
        
        if child_type == "Mesh":
            # 生成新的名字
            new_name_prefix = f"SM_{parent_prim.GetName()}_"
            if child_name in mesh_count:
                mesh_count[child_name] += 1
                new_name = f"{new_name_prefix}{child_name}_{mesh_count[child_name]}"
            else:
                mesh_count[child_name] = 1
                new_name = f"{new_name_prefix}{child_name}"
            
            # 重命名子对象
            new_path = rename_prim(stage, child.GetPath(), new_name)
        
        elif child_type == "Xform":
            # 生成新的名字
            new_name_prefix = f"{parent_prim.GetName()}_"
            if child_name in xform_count:
                xform_count[child_name] += 1
                new_name = f"{new_name_prefix}{child_name}_{xform_count[child_name]}"
            else:
                xform_count[child_name] = 1
                new_name = f"{new_name_prefix}{child_name}"
            
            # 重命名子对象
            new_path = rename_prim(stage, child.GetPath(), new_name)
            
            # 检查是否有子对象并递归处理
            if child.GetChildrenNames() and new_path:
                rename_children(stage, new_path)

# def rename_objects_xform_prims(prim):
#     xform_name_count = {}

#     for child in prim.GetChildren():
#         if child.GetTypeName() == "Xform":
#             current_name = child.GetName()
#             parts = current_name.split('_')

#             new_base_name = '_'.join(part for part in parts if not re.search(r'\d', part))
#             for part in parts:
#                 if re.search(r'\d', part):
#                     new_base_name += f'_{part}'
#                     break

#             if new_base_name not in xform_name_count:
#                 xform_name_count[new_base_name] = 0
#             xform_name_count[new_base_name] += 1

#             # check if the new name already exists
#             new_name = f"{new_base_name}_{xform_name_count[new_base_name]}"
#             while stage.GetPrimAtPath(child.GetPath().GetParentPath().AppendChild(new_name)).IsValid():
#                 print(f"Name {new_name} already exists, incrementing count")
#                 xform_name_count[new_base_name] += 1
#                 new_name = f"{new_base_name}_{xform_name_count[new_base_name]}"

#             new_path = child.GetPath().GetParentPath().AppendChild(new_name)
#             stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name

# def rename_objects_mesh_prims(prim, mesh_count_dict):
#     for child in prim.GetChildren():
#         if child.GetTypeName() == "Mesh":
#             current_name = child.GetName()
#             parent_name = child.GetParent().GetName()

#             if parent_name not in mesh_count_dict:
#                 mesh_count_dict[parent_name] = 0

#             if current_name.lower() == "mesh":
#                 mesh_count_dict[parent_name] += 1
#                 new_name = f"Mesh_{parent_name}_{mesh_count_dict[parent_name]}"
#             else:
#                 # if ends with "Mesh", remove "Mesh" part
#                 if current_name.lower().endswith("mesh"):
#                     current_name = current_name[:-4]
#                 new_name = f"Mesh_{current_name}"
            
#             new_path = child.GetPath().GetParentPath().AppendChild(new_name)
#             # rename prim
#             stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name

#         elif child.GetTypeName() == "Xform":
#             # recursively process child Xform
#             rename_objects_mesh_prims(child, mesh_count_dict)


def rename_wall_mesh_prims(prim):
    wall_mesh_count = {}
    for child in prim.GetChildren():
        if child.GetTypeName() == "Mesh":
            current_name = child.GetName()
            # keep the first two parts of the name
            parts = current_name.split('_')
            if len(parts) > 2:
                new_base_name = '_'.join(parts[:2])
                if new_base_name not in wall_mesh_count:
                    wall_mesh_count[new_base_name] = 0
                wall_mesh_count[new_base_name] += 1
            
                new_name = f"Mesh_{new_base_name}_{wall_mesh_count[new_base_name]}".replace("wall", "Wall")

            else:
                new_name = current_name


            new_path = child.GetPath().GetParentPath().AppendChild(new_name)
            stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name


def rename_ceiling_mesh_prims(prim):
    for child in prim.GetChildren():
        if child.GetTypeName() == "Mesh":
            current_name = child.GetName()
            new_name = f"Mesh_{current_name}"
            new_path = child.GetPath().GetParentPath().AppendChild(new_name)
            stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name


def rename_floor_mesh_prims(prim):
    for child in prim.GetChildren():
        if child.GetTypeName() == "Mesh":
            current_name = child.GetName()
            new_name = f"Mesh_Floor_{current_name}"
            new_path = child.GetPath().GetParentPath().AppendChild(new_name)
            stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name


# load usd file
if __name__ == "__main__":

    index_list = [5]
    for i in index_list:

        # stage = Usd.Stage.Open('/home/zgao/house_usd_yup/train_8/house_train_8.usda')
        usd_file_path = f'/home/zhiyuan/Downloads/house_better_name/train_{i}/house_train_{i}.usda'
        stage = Usd.Stage.Open(usd_file_path)

        # stage = Usd.Stage.Open('/home/zgao/procthor/train_8/house_train_8.usda')

        with open(f'/home/zhiyuan/allenai_ai2thor_unity/Assets/Resources/rooms/train/train_{i}.json', 'r') as file:
            data = json.load(file)

        for prim in stage.Traverse():
            
            if prim.IsA(UsdGeom.Mesh):
                add_rigidbody_and_collision_to_mesh(prim)

        for obj in data['objects']:
            if 'children' in obj:
                process_children(obj['children'], obj['id'])

        # better name for mesh prims
        objects_prim = stage.GetPrimAtPath('/World/Objects')
        walls_prim = stage.GetPrimAtPath('/World/Structure/Walls')
        ceiling_prim = stage.GetPrimAtPath('/World/Structure/Ceiling')
        floor_prim = stage.GetPrimAtPath('/World/Structure/Floor')

        # 对/World/Objects下的所有xform对象进行处理

        for xform_prim in objects_prim.GetChildren():
            if xform_prim.GetTypeName() == "Xform":
                rename_children(stage, xform_prim.GetPath())


        # rename_objects_xform_prims(objects_prim)
        # rename_objects_mesh_prims(objects_prim, {})
        rename_wall_mesh_prims(walls_prim)
        rename_ceiling_mesh_prims(ceiling_prim)
        rename_floor_mesh_prims(floor_prim)

        # save usd file
        # stage.GetRootLayer().Save()

        # or save to a new file
        new_file_path = f'/home/zhiyuan/Downloads/house_better_name/train_{i}/new_house_train_{i}_processed.usda'
        stage.GetRootLayer().Export(new_file_path)
        print(f"Modified USD file has been saved as {new_file_path}")
