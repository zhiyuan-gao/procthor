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


def rename_objects_xform_prims(prim):
    xform_name_count = {}

    for child in prim.GetChildren():
        if child.GetTypeName() == "Xform":
            current_name = child.GetName()
            parts = current_name.split('_')

            # 查找并保留第一个包含数字的部分及其之前的部分
            new_base_name = '_'.join(part for part in parts if not re.search(r'\d', part))
            for part in parts:
                if re.search(r'\d', part):
                    new_base_name += f'_{part}'
                    break

            if new_base_name not in xform_name_count:
                xform_name_count[new_base_name] = 0
            xform_name_count[new_base_name] += 1
            new_name = f"{new_base_name}_{xform_name_count[new_base_name]}"

            new_path = child.GetPath().GetParentPath().AppendChild(new_name)
            stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name


def rename_objects_mesh_prims(prim, mesh_count_dict):
    for child in prim.GetChildren():
        if child.GetTypeName() == "Mesh":
            current_name = child.GetName()
            parent_name = child.GetParent().GetName()

            if parent_name not in mesh_count_dict:
                mesh_count_dict[parent_name] = 0

            if current_name.lower() == "mesh":
                mesh_count_dict[parent_name] += 1
                new_name = f"Mesh_{parent_name}_{mesh_count_dict[parent_name]}"
            else:
                # if ends with "Mesh", remove "Mesh" part
                if current_name.lower().endswith("mesh"):
                    current_name = current_name[:-4]
                new_name = f"Mesh_{current_name}"
            
            new_path = child.GetPath().GetParentPath().AppendChild(new_name)
            # rename prim
            stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name

        elif child.GetTypeName() == "Xform":
            # recursively process child Xform
            rename_objects_mesh_prims(child, mesh_count_dict)


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

    index_list = [8]
    for i in index_list:

        # stage = Usd.Stage.Open('/home/zgao/house_usd_yup/train_8/house_train_8.usda')
        usd_file_path = f'/home/zgao/house_usd_yup/train_{i}/house_train_{i}.usda'
        stage = Usd.Stage.Open(usd_file_path)

        # stage = Usd.Stage.Open('/home/zgao/procthor/train_8/house_train_8.usda')

        with open(f'/home/zgao/procthor-10k-main/train/train_{i}.json', 'r') as file:
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

        rename_objects_xform_prims(objects_prim)
        rename_objects_mesh_prims(objects_prim, {})
        rename_wall_mesh_prims(walls_prim)
        rename_ceiling_mesh_prims(ceiling_prim)
        rename_floor_mesh_prims(floor_prim)

        # save usd file
        # stage.GetRootLayer().Save()

        # or save to a new file
        new_file_path = f'/home/zgao/house_usd_yup/train_{i}/house_train_{i}_processed.usda'
        stage.GetRootLayer().Export(new_file_path)
        print(f"Modified USD file has been saved as {new_file_path}")
