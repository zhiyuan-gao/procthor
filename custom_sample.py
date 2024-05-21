from procthor.generation import PROCTHOR10K_ROOM_SPEC_SAMPLER, HouseGenerator
from procthor.generation.room_specs import *
from procthor.generation.house import House, HouseStructure, NextSamplingStage, PartialHouse

LIVING_ROOM_SPEC_SAMPLER = RoomSpecSampler(
    [
        RoomSpec(
            room_spec_id="living-room",
            sampling_weight=1,
            spec=[LeafRoom(room_id=2, ratio=1, room_type="LivingRoom")],
        ),
    ]
)


# partial_house = PartialHouse.from_structure_and_room_spec(
#     house_structure=house_structure,
#     room_spec=room_spec,
# )
# ori seed 42
house_generator = HouseGenerator(
    split="train", seed=50, room_spec_sampler=LIVING_ROOM_SPEC_SAMPLER
)
# house, sampling_stage_to_ph = house_generator.sample()
house, sampling_stage_to_ph = house_generator.sample(return_partial_houses=True)

keys = list(sampling_stage_to_ph.keys())
# print(keys)

ph = sampling_stage_to_ph[keys[7]] 
house.validate(house_generator.controller)

house.to_json("temp2.json")
# print(ph)
# print(sampling_stage_to_ph[keys[8]] )
# # instance a new HouseGenerator with different seed, only for the small objs
house_generator1 = HouseGenerator(
    split="train", seed=59, room_spec_sampler=LIVING_ROOM_SPEC_SAMPLER
)

house, _ = house_generator1.sample(partial_house = ph)
# # print(sampling_stage_to_ph[keys[0]])

house.validate(house_generator.controller)
house.to_json("temp4.json")