from procthor.generation import PROCTHOR10K_ROOM_SPEC_SAMPLER, HouseGenerator
from procthor.generation.room_specs import *
from procthor.generation.house import House, HouseStructure, NextSamplingStage, PartialHouse


# """
# three levels of input

# ui input:  room type, objs in rooms,
# user input dict: set the room id automaticly
# room specs: input for procthor

# """

# # example user's input
# # 
# # 

# # ui--> user input-->
user_defined_house_settings = {
    2: {  # 房间 ID
        "type": "bedroom",
        "complete": False,  # False 表示还有额外的随机物品
        "FLOOR_OBJS": [ "Desk", "Bed"],
        "WALL_OBJS": ["painting", "mirror"],
        "SMALL_OBJS": {
            "lamp": {"on": "bed"},
            "book": {"on": "desk"}
        }
    },
    4: {  # 另一个房间
        "type": "kitchen",
        "complete": True,  # True 表示房间里只有用户指定的物品，ProcTHOR 不会添加额外物品
        "FLOOR_OBJS": ["DiningTable", ],
        "WALL_OBJS": ["cabinet"],
        "SMALL_OBJS": {
            "plate": {"on": "stove"},
            "cup": {"on": "stove"}
        }
    },
    3: {
    },

}

#     PRIORITY_ASSET_TYPES={
#         "Bedroom": ["Bed", "Dresser"],
#         "LivingRoom": ["Television", "DiningTable", "Sofa"],
#         "Kitchen": ["CounterTop", "Fridge"],
#         "Bathroom": ["Toilet", "Sink"],
#     },

# example of a custom sampler
LIVING_ROOM_SPEC_SAMPLER = RoomSpecSampler(
    [      
        # here only sample living room
        # RoomSpec(
        #     room_spec_id="living-room",
        #     sampling_weight=1,
        #     spec=[LeafRoom(room_id=2, ratio=1, room_type="LivingRoom")],
        # ),

        # RoomSpec(
        #     room_spec_id="4-room",
        #     sampling_weight=5,
        #     spec=[
        #         MetaRoom(
        #             ratio=2,
        #             children=[
        #                 LeafRoom(room_id=4, ratio=2, room_type="Bedroom"),
        #                 LeafRoom(
        #                     room_id=5,
        #                     ratio=1,
        #                     room_type="Bathroom",
        #                     avoid_doors_from_metarooms=True,
        #                 ),
        #             ],
        #         ),
        #         MetaRoom(
        #             ratio=2,
        #             children=[
        #                 LeafRoom(room_id=6, ratio=3, room_type="Kitchen"),
        #                 LeafRoom(room_id=7, ratio=2, room_type="LivingRoom"),
        #             ],
        #         ),
        #     ],
        # ),
        RoomSpec(
            room_spec_id="kitchen-living-bedroom-room",
            sampling_weight=1,
            spec=[
                MetaRoom(
                    ratio=2,
                    children=[
                        LeafRoom(room_id=4, ratio=3, room_type="Kitchen"),
                        LeafRoom(room_id=3, ratio=2, room_type="LivingRoom"),
                    ],
                ),
                LeafRoom(room_id=2, ratio=1, room_type="Bedroom"),
            ],
        ),




    ]
)


# for i in range(5):

#     house_generator = HouseGenerator(
#         split="train", seed=i, room_spec_sampler=LIVING_ROOM_SPEC_SAMPLER
#     )
#     house, _ = house_generator.sample()
#     house.validate(house_generator.controller)
#     house.to_json(f"/home/zgao/procthor/procthor/houses/house_{i+8}.json")


# house_generator = HouseGenerator(
#     split="train", seed=50, room_spec_sampler=LIVING_ROOM_SPEC_SAMPLER,
#      user_defined_params = user_defined_house_settings)

# # house, _ = house_generator.sample()
# house, sampling_stage_to_ph = house_generator.sample(return_partial_houses=False)
# house.to_json("temp4.json")

# partial_house = sampling_stage_to_ph[NextSamplingStage.SMALL_OBJS]
# print(partial_house.objects)
# print('___________________________________________')
# # partial_house.reset_room(2)
# # print(partial_house.objects)
# partial_house.reset_receptacle('Dining_Table_211|2|0|0')
# print(partial_house.objects)


# for stage in NextSamplingStage:
#     if stage != NextSamplingStage.COMPLETE:
#         partial_house = sampling_stage_to_ph[stage]
#         house = partial_house.to_house()
#         house.to_json(f"{stage.value}_{stage.name}.json")


# house.to_json("/home/zgao/procthor/procthor/house_0.json")


# partial_house = PartialHouse.from_structure_and_room_spec(
#     house_structure=house_structure,
#     room_spec=room_spec,
# )



# # example of different sample stages
# house_generator = HouseGenerator(
#     split="train", seed=50, room_spec_sampler=LIVING_ROOM_SPEC_SAMPLER
# )

# # house, sampling_stage_to_ph = house_generator.sample()
# house, sampling_stage_to_ph = house_generator.sample(return_partial_houses=True)


# # keys = list(sampling_stage_to_ph.keys())
# # # print(keys)
# for i in range(9):
#     ph  = sampling_stage_to_ph[keys[i]]

# example of different sample stages
# house_generator = HouseGenerator(
#     split="train", seed=50, room_spec_sampler=LIVING_ROOM_SPEC_SAMPLER
# )
# house, sampling_stage_to_ph = house_generator.sample()
# house, sampling_stage_to_ph = house_generator.sample(return_partial_houses=True)

# keys = list(sampling_stage_to_ph.keys())
# # print(keys)

# ph = sampling_stage_to_ph[keys[2]] 
# house.validate(house_generator.controller)

# house.to_json("temp2.json")

# # instance a new HouseGenerator with different seed, only for the small objs
# house_generator1 = HouseGenerator(
#     split="train", seed=59, room_spec_sampler=LIVING_ROOM_SPEC_SAMPLER
# )

# house, _ = house_generator1.sample(partial_house = ph)
# # # print(sampling_stage_to_ph[keys[0]])

# house.validate(house_generator.controller)
# house.to_json("temp4.json")