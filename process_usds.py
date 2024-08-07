from pxr import Usd, UsdGeom, UsdPhysics, Sdf
import json
import re

class UsdProcessor:
    def __init__(self, stage):
        self.stage = stage

    def add_rigidbody_and_collision_to_xform(self, prim):
        UsdPhysics.RigidBodyAPI.Apply(prim)
        UsdPhysics.CollisionAPI.Apply(prim)

        rigidBodyAPI = UsdPhysics.RigidBodyAPI(prim)
        rigidBodyAPI.GetRigidBodyEnabledAttr().Set(True)

    def add_rigidbody_and_collision_to_mesh(self, prim):
        UsdPhysics.MassAPI.Apply(prim)
        UsdPhysics.CollisionAPI.Apply(prim)

        mass_api = UsdPhysics.MassAPI(prim)
        mass_api.GetMassAttr().Set(10.0)  # set mass to 10

    def process_children(self, children, parent_id):
        for child in children:
            small_obj_name = child['id'].replace("|", "_")
            small_obj_path = "/World/Objects/" + small_obj_name
            small_obj_prim = self.stage.GetPrimAtPath(small_obj_path)
            small_obj = UsdGeom.Xformable(small_obj_prim)

            receptacle_name = parent_id.replace("|", "_")
            receptacle_path = "/World/Objects/" + receptacle_name
            receptacle_prim = self.stage.GetPrimAtPath(receptacle_path)
            receptacle = UsdGeom.Xformable(receptacle_prim)

            self.add_rigidbody_and_collision_to_xform(small_obj_prim)

            if 'children' in child:
                self.process_children(child['children'], child['id'])

    def rename_children_with_parent_name(self, parent_prim, name_count):
        # Get the layer of the edit target
        layer = self.stage.GetEditTarget().GetLayer()

        # Iterate through all children of the parent prim
        for child_prim in parent_prim.GetChildren():
            # Generate new name: parentName_childName
            base_name = f"{parent_prim.GetName()}_{child_prim.GetName()}"

            # Check the name counter and generate unique names
            if base_name not in name_count:
                name_count[base_name] = 1
                new_name = f"{base_name}"
            else:
                name_count[base_name] += 1
                new_name = f"{base_name}_{name_count[base_name]}"

            # Get the current path and new path of the child prim
            old_child_path = child_prim.GetPath()
            new_child_path = old_child_path.GetParentPath().AppendChild(new_name)

            # Copy the child prim to the new path
            Sdf.CopySpec(layer, old_child_path, layer, new_child_path)

            # Recursively process the new child prim
            self.rename_children_with_parent_name(self.stage.GetPrimAtPath(new_child_path), name_count)

            # Remove the old child prim
            self.stage.RemovePrim(old_child_path)

    def rename_prims_in_objects(self, objects_prim):
        name_count = {}
        for child_prim in objects_prim.GetChildren():
            self.rename_children_with_parent_name(child_prim, name_count)

    def rename_wall_mesh_prims(self, mesh_prim):
        wall_mesh_count = {}
        for child in mesh_prim.GetChildren():
            if child.GetTypeName() == "Mesh":
                current_name = child.GetName()
                # Keep the first two parts of the name
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
                self.stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name

    def rename_ceiling_mesh_prims(self, ceiling_prim):
        for child in ceiling_prim.GetChildren():
            if child.GetTypeName() == "Mesh":
                current_name = child.GetName()
                new_name = f"Mesh_{current_name}"
                new_path = child.GetPath().GetParentPath().AppendChild(new_name)
                self.stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name

    def rename_floor_mesh_prims(self, floor_prim):
        for child in floor_prim.GetChildren():
            if child.GetTypeName() == "Mesh":
                current_name = child.GetName()
                new_name = f"Mesh_Floor_{current_name}"
                new_path = child.GetPath().GetParentPath().AppendChild(new_name)
                self.stage.GetEditTarget().GetLayer().GetPrimAtPath(child.GetPath()).name = new_name

# Load USD file
if __name__ == "__main__":
    index_list = [5]
    for i in index_list:
        usd_file_path = f'/home/zgao/house_usd_yup/train_{i}/house_train_{i}.usda'
        stage = Usd.Stage.Open(usd_file_path)

        processor = UsdProcessor(stage)

        with open(f'/home/zgao/procthor-10k-main/train/train_{i}.json', 'r') as file:
            data = json.load(file)

        for prim in stage.Traverse():
            if prim.IsA(UsdGeom.Mesh):
                processor.add_rigidbody_and_collision_to_mesh(prim)

        for obj in data['objects']:
            if 'children' in obj:
                processor.process_children(obj['children'], obj['id'])

        # Better name for mesh prims
        objects_prim = stage.GetPrimAtPath('/World/Objects')
        walls_prim = stage.GetPrimAtPath('/World/Structure/Walls')
        ceiling_prim = stage.GetPrimAtPath('/World/Structure/Ceiling')
        floor_prim = stage.GetPrimAtPath('/World/Structure/Floor')

        processor.rename_wall_mesh_prims(walls_prim)
        processor.rename_ceiling_mesh_prims(ceiling_prim)
        processor.rename_floor_mesh_prims(floor_prim)
        processor.rename_prims_in_objects(objects_prim)

        # Save USD file
        # stage.GetRootLayer().Save()
        # or save to a new file
        new_file_path = f'/home/zgao/house_usd_yup/train_{i}/house_train_{i}_processed.usda'
        stage.GetRootLayer().Export(new_file_path)
        print(f"Modified USD file has been saved as {new_file_path}")
