import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from procthor.generation import PROCTHOR10K_ROOM_SPEC_SAMPLER, HouseGenerator
from procthor.generation.room_specs import *
from procthor.generation.house import House, HouseStructure, NextSamplingStage, PartialHouse
import re
from typing import List, Union, Optional

# 假设你已有的类定义如下（例如使用 @define 或 dataclass 定义）：
# RoomSpec, LeafRoom, MetaRoom, OUTDOOR_ROOM_ID

import re
from typing import List, Union, Optional

# 假设你已有的类定义如下（例如使用 @define 或 dataclass 定义）：
# RoomSpec, LeafRoom, MetaRoom, OUTDOOR_ROOM_ID

def structure_to_roomspec(structure: dict) -> RoomSpec:
    """
    将来自 GUI 的结构字典转换为 RoomSpec 对象。
    
    规则：
      - 如果节点的 type 为 "Group"（不区分大小写）：
            - 若 children 为空，则忽略该节点（返回 None）；
            - 若只有一个子节点，则直接返回该子节点；
            - 否则，将处理后的子节点列表包装成一个 MetaRoom，
              ratio 使用 node 中的值（若为空则默认 1）。
      - 如果节点的 type 为 "Root"，则处理其 children 后返回展开的列表；
      - 对于其他节点（叶子节点）：
            - 如果没有 children，则生成一个 LeafRoom，
              从 name 中提取 room_id，并以 node["ratio"]（转换为 int，默认 1）赋值；
            - 如果有 children，则将其包装为 MetaRoom，使用节点中的 ratio（默认 1）。
      - 最后根据所有叶子节点的 room_type 拼接生成 room_spec_id，sampling_weight 固定为 1。
    """
    def process_node(node: dict, parent_is_group: bool = False) -> Optional[Union[LeafRoom, MetaRoom, List[Union[LeafRoom, MetaRoom]]]]:
        node_type = (node.get("type") or "").strip().lower()
        children = node.get("children", [])
        
        if node_type == "group":
            # 对于 Group 节点：如果 children 为空，则返回 None；
            # 如果只有一个子节点，则直接返回该子节点；
            # 否则，使用节点中 ratio（若为空则默认 1）包装成一个 MetaRoom。
            if not children:
                return None
            processed = []
            for child in children:
                res = process_node(child, parent_is_group=True)
                if res is None:
                    continue
                if isinstance(res, list):
                    processed.extend(res)
                else:
                    processed.append(res)
            if not processed:
                return None
            if len(processed) == 1:
                return processed[0]
            try:
                ratio = int(node.get("ratio") or 1)
            except Exception:
                ratio = 1
            return MetaRoom(ratio=ratio, children=processed)
        
        elif node_type == "root":
            # Root 节点直接返回其 children 的处理结果（展开为列表）
            processed = []
            for child in children:
                res = process_node(child, parent_is_group=False)
                if res is None:
                    continue
                if isinstance(res, list):
                    processed.extend(res)
                else:
                    processed.append(res)
            return processed
        
        else:
            # 其他节点
            if children:
                processed = []
                for child in children:
                    res = process_node(child, parent_is_group=parent_is_group)
                    if res is None:
                        continue
                    if isinstance(res, list):
                        processed.extend(res)
                    else:
                        processed.append(res)
                try:
                    ratio = int(node.get("ratio") or 1)
                except Exception:
                    ratio = 1
                return MetaRoom(ratio=ratio, children=processed)
            else:
                # 叶子节点：从 name 中提取 room_id，ratio 取节点值（默认 1）
                m = re.search(r'\d+', node.get("name", "0"))
                room_id = int(m.group()) if m else 0
                try:
                    ratio = int(node.get("ratio") or 1)
                except Exception:
                    ratio = 1
                room_type_val = node.get("type") or "Unknown"
                # 如果叶子节点在 group 内且房间类型为 Bathroom，则设置 avoid_doors_from_metarooms=True
                avoid = True if room_type_val.strip().lower() == "bathroom" and parent_is_group else False
                return LeafRoom(room_id=room_id, ratio=ratio, room_type=room_type_val, avoid_doors_from_metarooms=avoid)
    
    processed = process_node(structure, parent_is_group=False)
    if processed is None:
        spec_list = []
    elif isinstance(processed, list):
        spec_list = processed
    else:
        spec_list = [processed]
    
    # 生成 room_spec_id：收集所有叶子节点的 room_type，连接后加上后缀 "-room"
    def collect_leaf_types(item: Union[LeafRoom, MetaRoom]) -> List[str]:
        if isinstance(item, LeafRoom):
            return [item.room_type.strip().lower()]
        elif isinstance(item, MetaRoom):
            types = []
            for child in item.children:
                types.extend(collect_leaf_types(child))
            return types
        else:
            return []
    
    collected_types = []
    for item in spec_list:
        collected_types.extend(collect_leaf_types(item))
    room_spec_id = "-".join(collected_types) + "-room" if collected_types else "default-room"
    
    return RoomSpec(room_spec_id=room_spec_id, sampling_weight=1, spec=spec_list)


if __name__ == "__main__":
    data = {
    "structure": {
        "name": "Root",
        "type": "Root",
        "ratio": "",
        "children": [
            {
                "name": "Room 2",
                "type": "Bedroom",
                "ratio": "3",
                "children": []
            },
            {
                "name": "Room 3",
                "type": "Bathroom",
                "ratio": "1",
                "children": []
            },
        ]
    },
    "floor_wall_objects": {
        "floor_objects": [
            {
                "room": "2",
                "object_type": "Floor Object",
                "asset": "Bed"
            },
            {
                "room": "2",
                "object_type": "Floor Object",
                "asset": "Desk"
            },

        ],
        "wall_objects": []
    },
    "small_objects": [
    {
        "room": "2",
        "small_object": "Book",
        "placed_on": "Bed_1(Room 2 (Bedroom))",
        "receptacle_type": "Bed"
    },
    {
        "room": "random",
        "small_object": "Book",
        "placed_on": "random",
        "receptacle_type": "random"
    }]
    }


    def process_house_settings(house_settings):
        rs = structure_to_roomspec(house_settings['structure'])

        room_spec_sampler =RoomSpecSampler([rs])
        # print(rs)

        house_generator = HouseGenerator(
            split="train", seed=50, room_spec_sampler=room_spec_sampler,
            user_defined_params = house_settings)

        house, _ = house_generator.sample(return_partial_houses=False)
        house.to_json("temp4.json")
        print("House saved to temp4.json")

    process_house_settings(data)




    # rs = structure_to_roomspec(data['structure'])

    # room_spec_sampler =RoomSpecSampler([rs])
    # # print(rs)

    # house_generator = HouseGenerator(
    #     split="train", seed=50, room_spec_sampler=room_spec_sampler,
    #      user_defined_params = data)

    # house, _ = house_generator.sample(return_partial_houses=False)
    # house.to_json("temp4.json")
