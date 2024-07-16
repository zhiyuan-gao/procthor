from pxr import Usd, UsdGeom, UsdPhysics,Sdf
import json
from procthor.databases import DEFAULT_PROCTHOR_DATABASE


default_max_open_angle = 90.0  
default_rotation_axis = (0, 1, 0) 

def add_door_attributes(prim, max_open_angle, rotation_axis):
    if prim:
        max_open_angle_attr = prim.CreateAttribute("maxOpenAngle", Sdf.ValueTypeNames.Float)
        max_open_angle_attr.Set(max_open_angle)
        rotation_axis_attr = prim.CreateAttribute("rotationAxis", Sdf.ValueTypeNames.Float3)
        rotation_axis_attr.Set(rotation_axis)
    else:
        print(f"Prim at path {prim.GetPath()} does not exist")



def add_objects_annotations(prim, attr_name, attr_value):
    if prim:
        custom_attr = prim.CreateAttribute(attr_name, Sdf.ValueTypeNames.Bool)
        custom_attr.Set(attr_value)
        print(f"Added attribute {attr_name} with value {attr_value} to {prim.GetPath()}")
    else:
        print(f"Prim at path {prim.GetPath()} does not exist")





def add_attributes_to_prims(input_usd_path,output_usd_path,json_path):
    stage = Usd.Stage.Open(input_usd_path)
    with open(json_path, 'r') as file:
        data = json.load(file)
    stage = Usd.Stage.Open(input_usd_path)


    for door in data['doors']:
        door_id = door['id'].replace('|', '_')

        door_prim_path = "/World/Objects/" + door_id
        door_prim = stage.GetPrimAtPath(door_prim_path)
        for child in door_prim.GetChildren():
            add_door_attributes(child, default_max_open_angle, default_rotation_axis)

    for object in data['objects']:
        object_id = object['id'].replace('|', '_')

        object_prim_path = "/World/Objects/" + object_id
        object_prim = stage.GetPrimAtPath(object_prim_path)

        database = DEFAULT_PROCTHOR_DATABASE.ASSET_DATABASE

        label = object['label']
        add_objects_annotations(object_prim, attr_name, attr_value)



    stage.GetRootLayer().Export(output_usd_path)





# process usd file
# if __name__ == "__main__":

    # input_usd_path = '/home/zgao/procthor/train_8/house_train_8_rg.usda'
    # output_usd_path = '/home/zgao/procthor/train_8/house_train_8_rg_anno.usda'
    # json_path = '/home/zgao/procthor-10k-main/train/train_8.json'

    # add_attributes_to_prims(input_usd_path,output_usd_path,json_path)