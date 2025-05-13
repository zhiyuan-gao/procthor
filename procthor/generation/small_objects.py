"""
Add small objects to the house.

Also randomizes the openness of some of the objects.
"""

import copy
import logging
import random
from collections import defaultdict
from typing import Dict, List, Optional
import numpy as np
from ai2thor.controller import Controller

from procthor.constants import FLOOR_Y, OPENNESS_RANDOMIZATIONS
from procthor.utils.types import Object, Split, Vector3
from . import PartialHouse
from .objects import ProceduralRoom, sample_openness
from ..databases import ProcTHORDatabase
from collections import Counter

PARENT_BIAS = defaultdict(
    lambda: 0.2, {"Chair": 0, "ArmChair": 0, "Countertop": 0.2, "ShelvingUnit": 0.4}
)
"""The sampling bias for how often an object is placed in a receptacle."""

CHILD_BIAS = defaultdict(
    lambda: 0,
    {
        "HousePlant": 0.25,
        "Basketball": 0.2,
        "SprayBottle": 0.2,
        "Pot": 0.1,
        "Pan": 0.1,
        "Bowl": 0.05,
        "BaseballBat": 0.1,
    },
)
"""The sampling bias for how often an individual object is sampled."""


def randomize_bias():
    """Randomize the sampling bias for the parent and child objects."""
    lower = -0.3
    upper = 0.1
    return (upper - lower) * np.random.beta(a=3.5, b=1.9) + lower


MAX_OF_TYPE_ON_RECEPTACLE = 3
"""The maximum number of objects of a given type that can be placed on a receptacle."""

HOUSE_PLANT_MAX_HEIGHT = 0.75
"""The maximum height of a house plant that is considered small.

Note: There are some large house plants are intended to be placed on the floor.
"""

FLOOR_OBJECTS_TO_DROP = {"BaseballBat": {"p": 0.7}}
"""The objects that are dropped to be put in place."""

OBJECTS_TO_DROP = {"BaseballBat": {"p": 0.97}}
"""The objects that are pushed when they are placed on a receptacle.

Helps avoid the baseball bat from always standing upright.
"""


def default_add_small_objects(
    partial_house: PartialHouse,
    controller: Controller,
    pt_db: ProcTHORDatabase,
    split: Split,
    rooms: Dict[int, ProceduralRoom],
    max_object_types_per_room: int = 10000,
    target_receptacle_ids: Optional[List[str]] = None,
    user_small_objs: Optional[dict] = None,
    randomize_rest: bool = True,
) -> None:
    """
    Adds small objects to the house by placing them on suitable receptacles 
    (e.g., tables, chairs, shelves) based on placement rules and randomization.

    Parameters:
    - partial_house: A PartialHouse object representing the current state of the house.
    - controller: A Controller object for interacting with the simulation.
    - pt_db: A ProcTHORDatabase object containing object and placement data.
    - split: Specifies the data split (e.g., train, test) for selecting objects.
    - rooms: A dictionary of ProceduralRoom objects, keyed by room IDs.
    - max_object_types_per_room: The maximum number of object types allowed per room.
    - target_receptacle_ids: (Optional) A list of receptacle object IDs to target.
      - If None (default), small objects will be added to all suitable receptacles.
      - If provided, only the specified receptacles will receive small objects.
    - user_small_objs: (Optional) A dictionary of user-specified small objects to add.
    """
    controller.reset()
    controller.step(action="ResetObjectFilter")
    event = controller.step(
        action="CreateHouse", house=partial_house.to_house_dict(), renderImage=False
    )
    assert event, "Unable to CreateHouse!"
    controller.step(action="SetObjectFilter", objectIds=[])

    # NOTE: Get the objects in the room.
    objects = [
        obj
        for obj in event.metadata["objects"]
        if not any(
            obj["objectId"].startswith(k)
            for k in ["wall|", "room|", "Floor", "door|", "window|"]
        )
    ]
    objects_per_room = defaultdict(list)
    for obj in objects:
        object_id = obj["objectId"]
        parts = object_id.split("|")
        room_id = int(parts[1])
        # room_id = int(object_id[: object_id.find("|")])
        objects_per_room[room_id].append(obj)
    objects_per_room = dict(objects_per_room)

    # NOTE: Modify to filter target receptacles
    receptacles_per_room = {
        room_id: [
            obj
            for obj in objects
            if obj["objectType"] in pt_db.OBJECTS_IN_RECEPTACLES
            and (not target_receptacle_ids or obj["objectId"] in target_receptacle_ids)  # 新增过滤条件
        ]
        for room_id, objects in objects_per_room.items()
    }

    object_types_in_rooms = {
        room_id: set(obj["objectType"] for obj in objects)
        for room_id, objects in objects_per_room.items()
    }

    objects_in_house = {obj["id"]: obj for obj in partial_house.objects}

    house_bias = randomize_bias()
    logging.debug(f"Small object bias: {house_bias}")

    def transform_small_objects(small_objects):
        transformed_data = defaultdict(lambda: defaultdict(list))
        
        for obj in small_objects:
            receptacle_type = obj["receptacle_type"]
            receptacle_name = obj["placed_on"]
            small_object = obj["small_object"]
            
            transformed_data[receptacle_type][receptacle_name].append(small_object)
        
        return dict(transformed_data)

    # NOTE: Place the objects
    num_placed_object_instances = 0
    for room_id, room in rooms.items():
        if room_id not in receptacles_per_room:
            continue
        receptacles_in_room = receptacles_per_room[room_id]
        room_type = room.room_type
        spawnable_objects = []

        if user_small_objs is not None:
            user_small_objs_per_room = [obj for obj in user_small_objs if obj.get("room") == str(room_id)]
        else:
            user_small_objs_per_room = []

        user_receptacle_per_room = transform_small_objects(user_small_objs_per_room)  # 转换用户提供的数据
        user_receptacle_types = list(user_receptacle_per_room.keys())
        remaining_receptacles = [] 

        # Here we just assign a receptacle type to small obj for random user input, 
        # and the specific receptacle asset is chosen in the later for loop
        receptacle_type_counts = Counter([receptacle["objectType"] for receptacle in receptacles_in_room])
        for _user_small_obj in user_small_objs_per_room:
            if _user_small_obj['placed_on'].casefold() == "random":
                
                small_obj_type = _user_small_obj['small_object']
                place_weight = {}
                for _receptacle_type in list(receptacle_type_counts.keys()):
                    prob = pt_db.OBJECTS_IN_RECEPTACLES[_receptacle_type].get(small_obj_type, {}).get('p', 0)
                    place_weight[_receptacle_type] = prob /receptacle_type_counts[_receptacle_type]

                options = list(place_weight.keys())
                weights = list(place_weight.values())
                choice = random.choices(options, weights=weights, k=1)[0]
                _user_small_obj["small_object"] == choice
                print('success for small obj random')

        for receptacle in receptacles_in_room:

            receptacle_type = receptacle["objectType"]

            if receptacle_type in user_receptacle_types:
                    # 只处理仍有物体需要放置的 receptacle 类型
                if receptacle_type in user_receptacle_per_room and user_receptacle_per_room[receptacle_type]:

                    chosen_receptacle = random.choice(list(user_receptacle_per_room[receptacle_type].keys()))
                    small_objects_to_place = user_receptacle_per_room[receptacle_type].pop(chosen_receptacle)

                    for small_object in small_objects_to_place:
                        asset_candidates = pt_db.ASSETS_DF[
                            (pt_db.ASSETS_DF["objectType"] == small_object)
                            & pt_db.ASSETS_DF["split"].isin([split, None])
                        ]

                        chosen_asset_id = asset_candidates.sample()["assetId"].iloc[0]
                        obj_type = pt_db.ASSET_ID_DATABASE[chosen_asset_id]["objectType"]
                        generated_object_id = f"{obj_type}|{room_id}|{num_placed_object_instances}"

                        event = controller.step(action="ResetObjectFilter")
                        
                        event = controller.step(
                            action="SpawnAsset",
                            assetId=chosen_asset_id,
                            generatedId=generated_object_id,
                            position=Vector3(x=0, y=FLOOR_Y - 20, z=0),
                            renderImage=False,
                        )
                        
                        receptacle_object_ids = [receptacle["objectId"]]

                        assert event, f"SpawnAsset failed for {small_object}!"

                        openness = None
                        if (
                            obj_type in OPENNESS_RANDOMIZATIONS
                            and "CanOpen"
                            in pt_db.ASSET_ID_DATABASE[chosen_asset_id]["secondaryProperties"]
                        ):
                            openness = sample_openness(obj_type)
                            controller.step(
                                action="OpenObject",
                                objectId=generated_object_id,
                                openness=openness,
                                forceAction=True,
                                raise_for_failure=True,
                                renderImage=False,
                            )
                        event = controller.step(
                            action="InitialRandomSpawn",
                            randomSeed=random.randint(0, 1_000_000_000),
                            # placeStationary=False,
                            objectIds=[generated_object_id],
                            receptacleObjectIds=receptacle_object_ids,
                            forceVisible=False,
                            allowFloor=False,
                            renderImage=False,
                            allowMoveable=True,
                        )

                        obj = next(
                            obj
                            for obj in event.metadata["objects"]
                            if obj["objectId"] == generated_object_id
                        )

                        center_position = obj["axisAlignedBoundingBox"]["center"].copy()

                        # NOTE: Sometimes InitialRandomSpawn succeeds when it should
                        # be failing. In these cases, the object will appear below
                        # the floor.

                        if event:
                            print('spawn object success')
                        if event and center_position["y"] > FLOOR_Y:
                            if obj["breakable"]:
                                # NOTE: often avoids objects shattering upon initialization.
                                center_position["y"] += 0.05

                            states = {}
                            if openness is not None:
                                states["openness"] = openness

                            house_data_receptacle = receptacle["objectId"]

                            if "children" not in objects_in_house[house_data_receptacle]:
                                objects_in_house[house_data_receptacle]["children"] = []

                            objects_in_house[house_data_receptacle]["children"].append(
                                Object(
                                    id=generated_object_id,
                                    assetId=chosen_asset_id,
                                    rotation=obj["rotation"],
                                    position=center_position,
                                    kinematic=bool(
                                        pt_db.PLACEMENT_ANNOTATIONS.loc[
                                            small_object
                                        ]["isKinematic"]
                                    ),
                                    **states,
                                )
                            )
                            num_placed_object_instances += 1


                            # do we need this? if set here, maybe we can't place more objects of the same type in the same room
                            # it will destroy the randomness of the remaining objects
                            # objects_types_placed_in_room.add(obj_type)
                            # object_types_in_rooms[room_id].add(small_object)
                        else:
                            print('disable object')
                            controller.step(
                                action="DisableObject",
                                objectId=generated_object_id,
                                renderImage=False,
                            )

            else:
                remaining_receptacles.append(receptacle)

        # process the remaining random receptacle items in the room
        if randomize_rest:
    
            for receptacle in remaining_receptacles:

                objects_in_receptacle = pt_db.OBJECTS_IN_RECEPTACLES[receptacle["objectType"]]
                for object_type, data in objects_in_receptacle.items():
                    room_weight = pt_db.PLACEMENT_ANNOTATIONS.loc[object_type][f"in{room_type}s"]
                    if room_weight == 0:
                        continue
                    spawnable_objects.append(
                        {
                            "receptacleId": receptacle["objectId"],
                            "receptacleType": receptacle["objectType"],
                            "childObjectType": object_type,
                            "childRoomWeight": room_weight,
                            "pSpawn": data["p"],
                        }
                    )

        filtered_spawnable_groups = [
            group
            for group in spawnable_objects
            if random.random()
            <= (
                group["pSpawn"]
                + PARENT_BIAS[group["receptacleType"]]
                + CHILD_BIAS[group["childObjectType"]]
                + house_bias
            )
        ]

        random.shuffle(filtered_spawnable_groups)
        objects_types_placed_in_room = set()
        for group in filtered_spawnable_groups:
            if len(objects_types_placed_in_room) >= max_object_types_per_room:
                break

            # NOTE: Supports things like 3 plates on a surface.
            num_of_type = 1
            # NOTE: intentionally has no bias on > 1 samples.
            while random.random() <= group["pSpawn"]:
                num_of_type += 1
                if num_of_type >= MAX_OF_TYPE_ON_RECEPTACLE:
                    break

            for _ in range(num_of_type):
                # NOTE: Check if there can be multiple of the same type in the room.
                if (
                    group["childObjectType"] in object_types_in_rooms[room_id]
                    and not pt_db.PLACEMENT_ANNOTATIONS.loc[group["childObjectType"]][
                        "multiplePerRoom"
                    ]
                ):
                    break

                asset_candidates = pt_db.ASSETS_DF[
                    (pt_db.ASSETS_DF["objectType"] == group["childObjectType"])
                    & pt_db.ASSETS_DF["split"].isin([split, None])
                ]

                if group["childObjectType"] == "HousePlant":
                    # NOTE: House plants are a weird exception where there are massive
                    # house plants meant to be placed on the floor, and smaller
                    # house plants that can be placed on receptacles. This filters
                    # to only place smaller house plants on receptacles.
                    asset_candidates = asset_candidates[
                        asset_candidates["ySize"] < HOUSE_PLANT_MAX_HEIGHT
                    ]

                # NOTE: Some objects have multiple sim object receptacles within it,
                # so we need to specify all of them as possible receptacle object ids.
                event = controller.step(action="ResetObjectFilter")
                receptacle_object_ids = [
                    obj["objectId"]
                    for obj in event.metadata["objects"]
                    if obj["objectId"].startswith(group["receptacleId"])
                ]

                chosen_asset_id = asset_candidates.sample()["assetId"].iloc[0]
                obj_type = pt_db.ASSET_ID_DATABASE[chosen_asset_id]["objectType"]
                generated_object_id = f"{obj_type}|{room_id}|{num_placed_object_instances}"

                # NOTE: spawn below the floor so it doesn't tip over any other objects.
                event = controller.step(
                    action="SpawnAsset",
                    assetId=chosen_asset_id,
                    generatedId=generated_object_id,
                    position=Vector3(x=0, y=FLOOR_Y - 20, z=0),
                    renderImage=False,
                )
                assert (
                    event
                ), f"SpawnAsset failed for {chosen_asset_id} with {event.metadata['actionReturn']}!"
                controller.step(
                    action="SetObjectFilter", objectIds=[generated_object_id]
                )

                # obj_type = pt_db.ASSET_ID_DATABASE[chosen_asset_id]["objectType"]
                openness = None
                if (
                    obj_type in OPENNESS_RANDOMIZATIONS
                    and "CanOpen"
                    in pt_db.ASSET_ID_DATABASE[chosen_asset_id]["secondaryProperties"]
                ):
                    openness = sample_openness(obj_type)
                    controller.step(
                        action="OpenObject",
                        objectId=generated_object_id,
                        openness=openness,
                        forceAction=True,
                        raise_for_failure=True,
                        renderImage=False,
                    )
                event = controller.step(
                    action="InitialRandomSpawn",
                    randomSeed=random.randint(0, 1_000_000_000),
                    # placeStationary=False,
                    objectIds=[generated_object_id],
                    receptacleObjectIds=receptacle_object_ids,
                    forceVisible=False,
                    allowFloor=False,
                    renderImage=False,
                    allowMoveable=True,
                )
                obj = next(
                    obj
                    for obj in event.metadata["objects"]
                    if obj["objectId"] == generated_object_id
                )
                center_position = obj["axisAlignedBoundingBox"]["center"].copy()

                # NOTE: Sometimes InitialRandomSpawn succeeds when it should
                # be failing. In these cases, the object will appear below
                # the floor.
                if event and center_position["y"] > FLOOR_Y:
                    if obj["breakable"]:
                        # NOTE: often avoids objects shattering upon initialization.
                        center_position["y"] += 0.05

                    states = {}
                    if openness is not None:
                        states["openness"] = openness

                    # NOTE: "___" is when there is a child SimObjPhysics of another
                    # SimObjPhysics object (e.g., drawers on dressers).
                    house_data_receptacle = group["receptacleId"]
                    if "___" in group["receptacleId"]:
                        house_data_receptacle = group["receptacleId"][
                            : group["receptacleId"].find("___")
                        ]
                    if "children" not in objects_in_house[house_data_receptacle]:
                        objects_in_house[house_data_receptacle]["children"] = []

                    objects_in_house[house_data_receptacle]["children"].append(
                        Object(
                            id=generated_object_id,
                            assetId=chosen_asset_id,
                            rotation=obj["rotation"],
                            position=center_position,
                            kinematic=bool(
                                pt_db.PLACEMENT_ANNOTATIONS.loc[
                                    group["childObjectType"]
                                ]["isKinematic"]
                            ),
                            **states,
                        )
                    )

                    num_placed_object_instances += 1
                    objects_types_placed_in_room.add(obj_type)
                    object_types_in_rooms[room_id].add(group["childObjectType"])
                else:
                    controller.step(
                        action="DisableObject",
                        objectId=generated_object_id,
                        renderImage=False,
                    )

    # NOTE: Drop object from near ceiling so it falls
    def _set_drop_heights(objects: List[Object], obj_types):
        for obj in objects:
            obj_type = pt_db.ASSET_ID_DATABASE[obj["assetId"]]["objectType"]
            if obj_type in obj_types and random.random() < obj_types[obj_type]["p"]:
                obj["position"]["y"] = 3
                obj["rotation"]["x"] = random.random() * 2 + 3
                obj["rotation"]["y"] = random.random() * 360
                changed_ids.add(obj["id"])
            if "children" in obj:
                _set_drop_heights(obj["children"], obj_types=OBJECTS_TO_DROP)

    # NOTE: Get pose of dropped object
    def _save_new_heights(objects: List[Object]):
        for obj in objects:
            if obj["id"] in changed_ids:
                thor_obj = next(
                    o for o in event.metadata["objects"] if o["objectId"] == obj["id"]
                )
                obj["position"] = thor_obj["axisAlignedBoundingBox"]["center"].copy()
                obj["rotation"] = thor_obj["rotation"].copy()
            if "children" in obj:
                _save_new_heights(obj["children"])

    changed_ids = set()
    orig_objects = copy.deepcopy(partial_house.objects)
    _set_drop_heights(objects=partial_house.objects, obj_types=FLOOR_OBJECTS_TO_DROP)
    if changed_ids:
        controller.reset()
        event = controller.step(
            action="CreateHouse", house=partial_house.to_house_dict(), renderImage=False
        )
        assert event, "Unable to CreateHouse!"

        # NOTE: wait for objects to settle.
        last_objs = [
            obj for obj in event.metadata["objects"] if obj["objectId"] in changed_ids
        ]
        i = 0
        failed = False
        while True:
            i += 1
            if i > 1000:
                failed = True
                print("Objects not settling!")
                break

            event = controller.step(
                action="AdvancePhysicsStep",
                timeStep=0.01,
                allowAutoSimulation=True,
                renderImage=False,
            )
            objs = [
                obj
                for obj in event.metadata["objects"]
                if obj["objectId"] in changed_ids
            ]

            if all(
                all(
                    abs(obj["position"][k] - last_obj["position"][k]) < 1e-3
                    and abs(obj["rotation"][k] - last_obj["rotation"][k]) < 1e-3
                    for k in ["x", "y", "z"]
                )
                for obj, last_obj in zip(objs, last_objs)
            ):
                break
            last_objs = objs

        if failed:
            partial_house.objects = orig_objects
        else:
            _save_new_heights(objects=partial_house.objects)
