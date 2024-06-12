from pxr import Usd, UsdGeom, UsdPhysics

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

def process_stage(stage):

    objects_prim = stage.GetPrimAtPath('/World/Objects')


    small_prims = [prim for prim in objects_prim.GetChildren() if prim.GetName().startswith('Small')]
    for prim in small_prims:
        if prim.GetTypeName() == 'Xform':
            add_rigidbody_and_collision_to_xform(prim)


    for prim in stage.Traverse():
        
        if prim.IsA(UsdGeom.Mesh):
            add_rigidbody_and_collision_to_mesh(prim)


# load usd file
# stage = Usd.Stage.Open('/home/zgao/Downloads/house10/exported_usd/train_1/house_train_1.usda')
# stage = Usd.Stage.Open('/home/zgao/livRoom_usd/temp2/house_temp2.usda')
stage = Usd.Stage.Open('/home/zgao/Downloads/temp/temp/house_temp.usda')


process_stage(stage)

# save new usd file
# new_file_path = '/home/zgao/Downloads/house10/exported_usd/train_1/house_train_1_with_mass_and_collision1.usda'
new_file_path = '/home/zgao/Downloads/temp/temp/house_temp1.usda'

stage.GetRootLayer().Export(new_file_path)

print(f"Modified USD file has been saved as {new_file_path}")
