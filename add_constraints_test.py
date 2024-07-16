from pxr import Usd, UsdGeom, Sdf

stage = Usd.Stage.Open('/home/zgao/procthor/train_8/house_train_8_rg.usda')

# Define the root path and attribute names and default values
root_path = "/World/Objects"
max_open_angle_attr_name = "maxOpenAngle"
rotation_axis_attr_name = "rotationAxis"
default_max_open_angle = 90.0  # For example, default maximum open angle is 90 degrees
default_rotation_axis = (0, 1, 0)  # For example, rotate around the Y axis

# Function to add attributes to a prim
def add_attributes(prim, max_open_angle, rotation_axis):
    if prim:
        max_open_angle_attr = prim.CreateAttribute(max_open_angle_attr_name, Sdf.ValueTypeNames.Float)
        max_open_angle_attr.Set(max_open_angle)
        rotation_axis_attr = prim.CreateAttribute(rotation_axis_attr_name, Sdf.ValueTypeNames.Float3)
        rotation_axis_attr.Set(rotation_axis)
    else:
        print(f"Prim at path {prim.GetPath()} does not exist")

        
root_prim = stage.GetPrimAtPath(root_path)
for prim in root_prim.GetChildren():
    if prim.GetName().startswith("door") or prim.GetName().startswith("Door"):
        for child in prim.GetChildren():
            add_attributes(child, default_max_open_angle, default_rotation_axis)


new_file_path = '/home/zgao/procthor/train_8/house_train_8_rg_constraint.usda'

stage.GetRootLayer().Export(new_file_path)

