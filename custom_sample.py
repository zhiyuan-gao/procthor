from procthor.generation import PROCTHOR10K_ROOM_SPEC_SAMPLER, HouseGenerator
from procthor.generation.room_specs import *
from procthor.generation.house import House, HouseStructure, NextSamplingStage, PartialHouse


# example of a custom sampler
LIVING_ROOM_SPEC_SAMPLER = RoomSpecSampler(
    [      
        # # here only sample living room
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
                        LeafRoom(room_id=6, ratio=3, room_type="Kitchen"),
                        LeafRoom(room_id=7, ratio=2, room_type="LivingRoom"),
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
#     house.to_json(f"/home/zgao/procthor/procthor/klbr/house_{i+8}.json")


house_generator = HouseGenerator(
    split="train", seed=0, room_spec_sampler=LIVING_ROOM_SPEC_SAMPLER)


house, _ = house_generator.sample()
house.validate(house_generator.controller)

house.to_json("/home/zgao/procthor/procthor/klbr/house_0.json")


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

# keys = list(sampling_stage_to_ph.keys())
# # print(keys)

# ph = sampling_stage_to_ph[keys[7]] 
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