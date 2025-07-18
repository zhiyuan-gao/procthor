import copy
import logging
import random
from contextlib import contextmanager
from typing import Dict, Optional, Tuple, Union, List, Any

import numpy as np
from ai2thor.controller import Controller
from attrs import Attribute, Factory, field
from attrs import define
from procthor.constants import PROCTHOR_INITIALIZATION
from procthor.utils.types import InvalidFloorplan, SamplingVars, Split

from ..databases import DEFAULT_PROCTHOR_DATABASE, ProcTHORDatabase
from .ceiling_height import sample_ceiling_height
from .color_objects import default_randomize_object_colors
from .doors import default_add_doors
from .exterior_walls import default_add_exterior_walls
from .generation import (
    create_empty_partial_house,
    default_sample_house_structure,
    find_walls,
    get_floor_polygons,
    get_xz_poly_map,
    scale_boundary_groups,
)
from .house import House, HouseStructure, NextSamplingStage, PartialHouse
from .interior_boundaries import sample_interior_boundary
from .layer import assign_layer_to_rooms
from .lights import default_add_lights
from .materials import randomize_wall_and_floor_materials
from .object_states import default_randomize_object_states
from .objects import default_add_floor_objects, default_add_rooms
from .protocols import (
    AddDoorsProtocol,
    AddExteriorWallsProtocol,
    AddFloorObjectsProtocol,
    AddLightsProtocol,
    AddRoomsProtocol,
    AddSkyboxProtocol,
    AddSmallObjectsProtocol,
    AddWallObjectsProtocol,
    RandomizeObjectAttributesProtocol,
    SampleHouseStructureProtocol,
)
from .room_specs import PROCTHOR10K_ROOM_SPEC_SAMPLER, RoomSpec, RoomSpecSampler
from .skyboxes import default_add_skybox
from .small_objects import default_add_small_objects
from .wall_objects import default_add_wall_objects
from collections import Counter

@define
class GenerationFunctions:
    sample_house_structure: SampleHouseStructureProtocol
    add_doors: AddDoorsProtocol
    add_lights: AddLightsProtocol
    add_skybox: AddSkyboxProtocol
    add_exterior_walls: AddExteriorWallsProtocol
    add_rooms: AddRoomsProtocol
    add_floor_objects: AddFloorObjectsProtocol
    add_wall_objects: AddWallObjectsProtocol
    add_small_objects: AddSmallObjectsProtocol
    randomize_object_colors: RandomizeObjectAttributesProtocol
    randomize_object_states: RandomizeObjectAttributesProtocol


def _create_default_generation_functions():
    return GenerationFunctions(
        sample_house_structure=default_sample_house_structure,
        add_doors=default_add_doors,
        add_lights=default_add_lights,
        add_skybox=default_add_skybox,
        add_exterior_walls=default_add_exterior_walls,
        add_rooms=default_add_rooms,
        add_floor_objects=default_add_floor_objects,
        add_wall_objects=default_add_wall_objects,
        add_small_objects=default_add_small_objects,
        randomize_object_colors=default_randomize_object_colors,
        randomize_object_states=default_randomize_object_states,
    )


@define
class HouseGenerator:
    split: Split = field()
    seed: Optional[int] = None
    room_spec: Optional[Union[RoomSpec, str]] = None
    room_spec_sampler: Optional[RoomSpecSampler] = None
    interior_boundary: Optional[np.array] = None
    controller: Optional[Controller] = None
    partial_house: Optional[PartialHouse] = None
    pt_db: ProcTHORDatabase = DEFAULT_PROCTHOR_DATABASE
    generation_functions: GenerationFunctions = Factory(
        _create_default_generation_functions
    )
    user_defined_params: Optional[Dict[str, Any]] = None 

    @split.validator
    def _valid_split(self, attribute: Attribute, value: Split) -> None:
        if value not in {"train", "val", "test"}:
            raise ValueError(f'split={value} must be in {{"train", "val", "test"}}')

    def __attrs_post_init__(self) -> None:
        if self.seed is None:
            self.seed = random.randint(0, 2**15)
            logging.debug(f"Using seed {self.seed}")
        if self.seed is not None:
            self.set_seed(self.seed)
        if self.room_spec_sampler is None:
            self.room_spec_sampler = PROCTHOR10K_ROOM_SPEC_SAMPLER
        if isinstance(self.room_spec, str):
            self.room_spec = self.room_spec_sampler[self.room_spec]

    def set_seed(self, seed: int) -> None:
        # TODO: Probably should not be done on a global level
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        if self.controller is not None:
            self.controller.step(action="SetRandomSeed", seed=seed, renderImage=False)

    def sample(
        self,
        partial_house: Optional[PartialHouse] = None,
        return_partial_houses: bool = False,
        sampling_vars: Optional[SamplingVars] = None,
        next_sampling_stage: Optional[NextSamplingStage] = NextSamplingStage.STRUCTURE,
    ) -> Tuple[House, Dict[NextSamplingStage, PartialHouse]]:
        """Sample a house specification compatible with AI2-THOR."""
        if self.controller is None:
            # NOTE: assumes images are never used by this Controller.
            # self.controller = Controller(quality="Low")
            self.controller = Controller(quality="Low", **PROCTHOR_INITIALIZATION)
            if self.seed is not None:
                self.controller.step(
                    action="SetRandomSeed", seed=self.seed, renderImage=False
                )

        sampling_stage_to_ph = {}
        sampling_vars = (
            SamplingVars.sample() if sampling_vars is None else sampling_vars
        )

        gfs = self.generation_functions
        if partial_house is None:
            # NOTE: grabbing existing values
            if self.partial_house is not None:
                room_spec = self.partial_house.room_spec
                interior_boundary = self.partial_house.house_structure.interior_boundary
            elif self.room_spec is not None:
                room_spec = self.room_spec
                interior_boundary = None
            else:
                room_spec = self.room_spec_sampler.sample()
                interior_boundary = None

            # NOTE: sample house structure via rejection sampling.
            room_ids = set(room_spec.room_type_map.keys())
            for _ in range(10):
                try:
                    house_structure = gfs.sample_house_structure(
                        interior_boundary=interior_boundary,
                        room_ids=room_ids,
                        room_spec=room_spec,
                        interior_boundary_scale=sampling_vars.interior_boundary_scale,
                        user_input = self.user_defined_params,
                        average_room_size = 6

                    )
                    break
                except InvalidFloorplan:
                    pass
            else:
                raise Exception(
                    f"Failed to generate interior boundary and floorplan"
                    "for room_spec={room_spec}!"
                )

            partial_house = PartialHouse.from_structure_and_room_spec(
                house_structure=house_structure,
                room_spec=room_spec,
            )
            partial_house.next_sampling_stage = next_sampling_stage

        # else:
        #     assert partial_house.next_sampling_stage > NextSamplingStage.STRUCTURE

        if return_partial_houses:
            sampling_stage_to_ph[partial_house.next_sampling_stage] = copy.deepcopy(
                partial_house
            )

        @contextmanager
        def advance_and_record_partial(partial_house: PartialHouse):
            try:
                yield None
            finally:
                partial_house.advance_sampling_stage()
                if return_partial_houses:
                    sampling_stage_to_ph[
                        partial_house.next_sampling_stage
                    ] = copy.deepcopy(partial_house)
        # print("____")
        # print(partial_house)
        # NOTE: DOORS
        if partial_house.next_sampling_stage <= NextSamplingStage.DOORS:
            with advance_and_record_partial(partial_house):
                door_polygons = gfs.add_doors(
                    partial_house=partial_house,
                    controller=self.controller,
                    pt_db=self.pt_db,
                    split=self.split,
                )
                randomize_wall_and_floor_materials(partial_house, pt_db=self.pt_db)

        floor_polygons = get_floor_polygons(
            xz_poly_map=partial_house.house_structure.xz_poly_map
        )
        # print("after doors")
        # print(partial_house)
        if partial_house.next_sampling_stage <= NextSamplingStage.LIGHTS:
            with advance_and_record_partial(partial_house):
                gfs.add_lights(
                    partial_house=partial_house,
                    controller=self.controller,
                    pt_db=self.pt_db,
                    split=self.split,
                    floor_polygons=floor_polygons,
                    ceiling_height=partial_house.house_structure.ceiling_height,
                )

        if partial_house.next_sampling_stage <= NextSamplingStage.SKYBOX:
            with advance_and_record_partial(partial_house):
                gfs.add_skybox(
                    partial_house=partial_house,
                    controller=self.controller,
                    pt_db=self.pt_db,
                    split=self.split,
                )

        # NOTE: added after `randomize_wall_and_floor_materials` on purpose
        if partial_house.next_sampling_stage <= NextSamplingStage.EXTERIOR_WALLS:
            with advance_and_record_partial(partial_house):
                gfs.add_exterior_walls(
                    partial_house=partial_house,
                    controller=self.controller,
                    pt_db=self.pt_db,
                    split=self.split,
                    boundary_groups=partial_house.house_structure.boundary_groups,
                )

        if partial_house.next_sampling_stage <= NextSamplingStage.ROOMS:
            with advance_and_record_partial(partial_house):
                gfs.add_rooms(
                    partial_house=partial_house,
                    controller=self.controller,
                    pt_db=self.pt_db,
                    split=self.split,
                    floor_polygons=floor_polygons,
                    room_type_map=partial_house.room_spec.room_type_map,
                    door_polygons=door_polygons,
                )

        if partial_house.next_sampling_stage <= NextSamplingStage.FLOOR_OBJS:
            
            if self.user_defined_params:
                user_floor_objs = self.user_defined_params.get('floor_wall_objects', None).get('floor_objects', None)
                randomize_rest = self.user_defined_params.get('randomize_rest', False)
                max_floor_objects = self.user_defined_params.get('max_floor_objects', sampling_vars.max_floor_objects)
                sampled_room_types = [room.room_type for room in partial_house.rooms.values()]
                room_type_counts = Counter(sampled_room_types)

                for floor_obj in user_floor_objs:
                    input_room_id = floor_obj.get('room')
                    if input_room_id.casefold() == "random":
                        room_place_weight = {}
                        for room in partial_house.rooms.values():
                            asset_factors = self.pt_db.PLACEMENT_ANNOTATIONS.loc[floor_obj['asset'],f'in{room.room_type}s']
                            room_count = room_type_counts[room.room_type]
                            room_place_weight[str(room.room_id)] = asset_factors/room_count

                        options = list(room_place_weight.keys())
                        weights = list(room_place_weight.values())
                        choice = random.choices(options, weights=weights, k=1)[0]
                        floor_obj['room'] = choice
            else:
                user_floor_objs = None
                randomize_rest = False
                max_floor_objects = sampling_vars.max_floor_objects

            with advance_and_record_partial(partial_house):

                gfs.add_floor_objects(
                    partial_house=partial_house,
                    controller=self.controller,
                    pt_db=self.pt_db,
                    split=self.split,
                    max_floor_objects=max_floor_objects,
                    user_floor_objs=user_floor_objs,
                    randomize_rest=randomize_rest,
                )
                floor_objects = [*partial_house.objects]
                gfs.randomize_object_colors(objects=floor_objects, pt_db=self.pt_db)
                gfs.randomize_object_states(objects=floor_objects, pt_db=self.pt_db)

        print('sample wall objs')
        if partial_house.next_sampling_stage < NextSamplingStage.WALL_OBJS:

            with advance_and_record_partial(partial_house):
                user_wall_objs = self.user_defined_params.get('floor_wall_objects', None).get('wall_objects', None) if self.user_defined_params else None
                gfs.add_wall_objects(
                    partial_house=partial_house,
                    controller=self.controller,
                    pt_db=self.pt_db,
                    split=self.split,
                    rooms=partial_house.rooms,
                    boundary_groups=partial_house.house_structure.boundary_groups,
                    room_type_map=partial_house.room_spec.room_type_map,
                    ceiling_height=partial_house.house_structure.ceiling_height,
                    user_wall_objs=user_wall_objs,
                    randomize_rest=randomize_rest
                )
                wall_objects = [*partial_house.objects[len(floor_objects) :]]
                gfs.randomize_object_colors(objects=wall_objects, pt_db=self.pt_db)
                gfs.randomize_object_states(objects=wall_objects, pt_db=self.pt_db)
        print('sample small objs')

        if partial_house.next_sampling_stage < NextSamplingStage.SMALL_OBJS:

            if self.user_defined_params:
                user_small_objs = self.user_defined_params.get('small_objects', None)

                sampled_room_types = [room.room_type for room in partial_house.rooms.values()]
                room_type_counts = Counter(sampled_room_types)
                # random distribute small objects to rooms
                for small_obj in user_small_objs:
                    input_room_id = small_obj.get('room')
                    if input_room_id.casefold() == "random":
                        room_place_weight = {}
                        for room in partial_house.rooms.values():
                            asset_factors = self.pt_db.PLACEMENT_ANNOTATIONS.loc[small_obj['small_object'],f'in{room.room_type}s']
                            room_count = room_type_counts[room.room_type]
                            room_place_weight[str(room.room_id)] = asset_factors/room_count

                        options = list(room_place_weight.keys())
                        weights = list(room_place_weight.values())
                        choice = random.choices(options, weights=weights, k=1)[0]
                        small_obj['room'] = choice
            else:
                user_floor_objs = None

            no_floor_and_wall_objs= len(partial_house.objects)
            with advance_and_record_partial(partial_house):
                user_small_objs = self.user_defined_params.get('small_objects', None) if self.user_defined_params else None
                gfs.add_small_objects(
                    partial_house=partial_house,
                    controller=self.controller,
                    pt_db=self.pt_db,
                    split=self.split,
                    rooms=partial_house.rooms,
                    user_small_objs=user_small_objs,
                    randomize_rest=randomize_rest,
                )
                small_objects = [
                    # *partial_house.objects[len(floor_objects) + len(wall_objects) :]
                    *partial_house.objects[no_floor_and_wall_objs :]
                ]
                gfs.randomize_object_colors(objects=small_objects, pt_db=self.pt_db)
                gfs.randomize_object_states(objects=small_objects, pt_db=self.pt_db)

        assign_layer_to_rooms(partial_house=partial_house)

        sampling_stage_to_ph[partial_house.next_sampling_stage] = partial_house

        print('end sample')

        return partial_house.to_house(), sampling_stage_to_ph
    
    def resample_room_objects(self, 
        target_room_ids: Optional[List[str]] = [2],
        partial_house: Optional[PartialHouse] = None,
        sampling_vars: Optional[SamplingVars] = None,
    ) -> House:
        
        for room_id in target_room_ids:
            partial_house.reset_room(room_id)
        
        gfs = self.generation_functions
        # resample floor objs
        gfs.add_floor_objects(
            partial_house=partial_house,
            controller=self.controller,
            pt_db=self.pt_db,
            split=self.split,
            max_floor_objects=sampling_vars.max_floor_objects,
            target_room_ids=target_room_ids
        )
        floor_objects = [*partial_house.objects]
        gfs.randomize_object_colors(objects=floor_objects, pt_db=self.pt_db)
        gfs.randomize_object_states(objects=floor_objects, pt_db=self.pt_db)

        target_rooms = {room_id: partial_house.rooms[room_id] for room_id in target_room_ids if room_id in partial_house.rooms}

        # resample wall objs
        gfs.add_wall_objects(
            partial_house=partial_house,
            controller=self.controller,
            pt_db=self.pt_db,
            split=self.split,
            rooms=target_rooms,
            boundary_groups=partial_house.house_structure.boundary_groups,
            room_type_map=partial_house.room_spec.room_type_map,
            ceiling_height=partial_house.house_structure.ceiling_height,
        )
        wall_objects = [*partial_house.objects[len(floor_objects) :]]
        gfs.randomize_object_colors(objects=wall_objects, pt_db=self.pt_db)
        gfs.randomize_object_states(objects=wall_objects, pt_db=self.pt_db)
        

        # resample small objs
        no_floor_and_wall_objs= len(partial_house.objects)
        gfs.add_small_objects(
            partial_house=partial_house,
            controller=self.controller,
            pt_db=self.pt_db,
            split=self.split,
            rooms=target_rooms,
        )
        small_objects = [
            # *partial_house.objects[len(floor_objects) + len(wall_objects) :]
            *partial_house.objects[no_floor_and_wall_objs :]
        ]
        gfs.randomize_object_colors(objects=small_objects, pt_db=self.pt_db)
        gfs.randomize_object_states(objects=small_objects, pt_db=self.pt_db)

        return partial_house.to_house()


    def resample_small_objects_of_receptacle(self, 
        target_receptacle_ids: Optional[List[str]] = None,
        partial_house: Optional[PartialHouse] = None,
    ) -> House:

        gfs = self.generation_functions
        
        for receptacle_id in target_receptacle_ids:
            partial_house.reset_receptacle(receptacle_id)

        no_floor_and_wall_objs= len(partial_house.objects)

        gfs.add_small_objects(
            partial_house=partial_house,
            controller=self.controller,
            pt_db=self.pt_db,
            split=self.split,
            rooms=partial_house.rooms,
            target_receptacle_ids=target_receptacle_ids
        )
        small_objects = [
            # *partial_house.objects[len(floor_objects) + len(wall_objects) :]
            *partial_house.objects[no_floor_and_wall_objs :]
        ]
        gfs.randomize_object_colors(objects=small_objects, pt_db=self.pt_db)
        gfs.randomize_object_states(objects=small_objects, pt_db=self.pt_db)

        return partial_house.to_house()
    
    def randomize_room_object_location(self, 
        target_room_ids: Optional[List[str]] = [2],
        partial_house: Optional[PartialHouse] = None,
        sampling_vars: Optional[SamplingVars] = None,
    ) -> House:
        
        pass