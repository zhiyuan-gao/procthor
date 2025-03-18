user_defined_house_settings = {
    "1": {  # 房间 ID
        "type": "bedroom",
        "complete": False,  # False 表示还有额外的随机物品
        "FLOOR_OBJS": ["bed", "desk"],
        "WALL_OBJS": ["painting", "mirror"],
        "SMALL_OBJS": {
            "lamp": {"on": "bed"},
            "book": {"on": "desk"}
        }
    },
    "2": {  # 另一个房间
        "type": "kitchen",
        "complete": True,  # True 表示房间里只有用户指定的物品，ProcTHOR 不会添加额外物品
        "FLOOR_OBJS": ["fridge", "stove"],
        "WALL_OBJS": ["cabinet"],
        "SMALL_OBJS": {
            "plate": {"on": "stove"},
            "cup": {"on": "stove"}
        }
    }
}


# for room_id in user_defined_house_settings.keys():
#     print(room_id)



for room_id, room_data in user_defined_house_settings.items():
    is_complete = room_data.get("complete", False)  # 默认为 False
    print(f"Room {room_id} ({room_data['type']}) - Complete: {is_complete}")

    # 遍历地板物品
    for obj in room_data.get("FLOOR_OBJS", []):
        print(f"  FLOOR_OBJS: {obj}")

    # 遍历墙上物品
    for obj in room_data.get("WALL_OBJS", []):
        print(f"  WALL_OBJS: {obj}")

    # 遍历小物品
    for small_obj, placement in room_data.get("SMALL_OBJS", {}).items():
        print(f"  SMALL_OBJS: {small_obj} on {placement['on']}")
