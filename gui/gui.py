import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QStackedWidget,
    QTreeWidget, QTreeWidgetItem, QComboBox, QHBoxLayout, QSpinBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt,QEvent,pyqtSignal,QThread
import json
import re
import multiprocessing
from procthor.databases import DEFAULT_PROCTHOR_DATABASE
from procthor.generation import PROCTHOR10K_ROOM_SPEC_SAMPLER, HouseGenerator
from procthor.generation.room_specs import RoomSpec,RoomSpecSampler,LeafRoom,MetaRoom
from typing import List, Optional, Union
from PyQt6.QtWidgets import QCheckBox

pt_db = DEFAULT_PROCTHOR_DATABASE

WALL_OBJS = ["Window", "Painting", "Television"]
ROOM_TYPES = ["Bedroom", "Bathroom", "Kitchen", "LivingRoom"]

floor_types, spawnable_assets = pt_db.FLOOR_ASSET_DICT[
    ("Bedroom", "train")
]
# print(list(floor_types.index))
LIV_FLOOR = list(pt_db.FLOOR_ASSET_DICT[("LivingRoom", "train")][0].index)
BED_FLOOR = list(pt_db.FLOOR_ASSET_DICT[("Bedroom", "train")][0].index)
KIT_FLOOR =  list(pt_db.FLOOR_ASSET_DICT[("Kitchen", "train")][0].index)
BAT_FLOOR =  list(pt_db.FLOOR_ASSET_DICT[("Bathroom", "train")][0].index)

# small obj = all obj - floor obj - wall obj.  109 types in total
all_obj_types = list(pt_db.PLACEMENT_ANNOTATIONS.index)
short_set = set(WALL_OBJS + LIV_FLOOR + BED_FLOOR + KIT_FLOOR + BAT_FLOOR)
SMALL_OBJECTS = [item for item in all_obj_types if item not in short_set]


RECEPTACLES = list(pt_db.OBJECTS_IN_RECEPTACLES.keys())

# TODO: for each receptacle, small objects are different

# TODO: mechanism to deal with random user input

def structure_to_roomspec(structure: dict) -> RoomSpec:
    """
    Convert the structure dictionary from the GUI into a RoomSpec object.
    
    Rules:
      - If the node type is "Group" (case insensitive):
            - If children is empty, ignore this node (return None);
            - If there is only one child node, return that child directly;
            - Otherwise, wrap the processed child node list into a MetaRoom,
              using the value from the node's ratio (defaulting to 1 if empty).
      - If the node type is "Root", process its children and return the expanded list;
      - For other nodes (leaf nodes):
            - If there are no children, generate a LeafRoom,
              extract room_id from the name, and assign node["ratio"] (converted to int, default 1);
            - If there are children, wrap them into a MetaRoom using the node's ratio (default 1).
      - Finally, generate room_spec_id by concatenating all leaf node room_types, with a fixed sampling_weight of 1.
    """
    def process_node(node: dict, parent_is_group: bool = False) -> Optional[Union[LeafRoom, MetaRoom, List[Union[LeafRoom, MetaRoom]]]]:
        node_type = (node.get("type") or "").strip().lower()
        children = node.get("children", [])
        
        if node_type == "group":
            # For Group nodes: if children is empty, return None;
            # If there is only one child node, return that child directly;
            # Otherwise, wrap it into a MetaRoom using the ratio from the node (default 1).
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
            # Root nodes directly return the processed results of their children (expanded as a list)
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
            # Other nodes
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
                # Leaf node: extract room_id from the name, ratio defaults to node value (default 1)
                m = re.search(r'\d+', node.get("name", "0"))
                room_id = int(m.group()) if m else 0
                try:
                    ratio = int(node.get("ratio") or 1)
                except Exception:
                    ratio = 1
                room_type_val = node.get("type") or "Unknown"
                # If a leaf node is inside a group and the room type is Bathroom, set avoid_doors_from_metarooms=True
                avoid = True if room_type_val.strip().lower() == "bathroom" and parent_is_group else False
                return LeafRoom(room_id=room_id, ratio=ratio, room_type=room_type_val, avoid_doors_from_metarooms=avoid)
    
    processed = process_node(structure, parent_is_group=False)
    if processed is None:
        spec_list = []
    elif isinstance(processed, list):
        spec_list = processed
    else:
        spec_list = [processed]
    
    # Generate room_spec_id: collect all leaf node room_types, concatenate them, and append "-room"
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


class ProcessWorker(QThread):
    finished_signal = pyqtSignal()

    def __init__(self, house_settings, parent=None):
        super().__init__(parent)
        self.house_settings = house_settings

    def run(self):
        process_house_settings(self.house_settings)
        self.finished_signal.emit()

class HouseDesigner(QWidget):

    floorWallChanged = pyqtSignal()
    structureChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.room_list = [("Random", "Random")]

        self.setWindowTitle("House Designer")
        self.setGeometry(100, 100, 800, 600)

        self.floorWallChanged.connect(self.update_small_objs_page)
        self.structureChanged.connect(self.update_room_comboboxes)

        # ✅ 主布局
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # ✅ 页面管理器
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # ✅ 添加三个页面
        self.page1 = self.create_structure_page()
        self.page2 = self.create_floor_wall_page()
        self.page3 = self.create_small_objs_page()

        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)

        # 连接页面切换信号
        self.stacked_widget.currentChanged.connect(self.on_page_changed)

        # ✅ 控制按钮
        self.button_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.confirm_button = QPushButton("Confirm")

        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)
        self.confirm_button.clicked.connect(self.confirm_selection)

        # ✅ add “Randomize Remaining” checkbox
        self.randomize_checkbox = QCheckBox("Randomize Remaining")
        self.randomize_checkbox.setChecked(False)
        self.button_layout.addWidget(self.randomize_checkbox)


        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.next_button)
        self.button_layout.addWidget(self.confirm_button)

        self.layout.addLayout(self.button_layout)

        # ✅ 页面索引
        self.current_page = 0

        self.next_room_id = 2  # ✅ Room ID 从 2 开始
        self.available_room_ids = set()  # ✅ 存储已删除的 Room ID
        self.next_group_id = 1  # ✅ Group ID 从 1 开始
        self.available_group_ids = set()  # ✅ 存储已删除的 Group ID

        self.update_buttons()


    def on_page_changed(self, index):
        if index in (1, 2):
            self.update_room_comboboxes()
            if index == 2:
                self.update_small_objs_page()

    ## **🏠 创建房屋结构选择页面（第一步）**
    def create_structure_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", "Ratio", "Max Floor Objs"])
        self.tree.setColumnCount(4)

        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)  # ✅ 允许内部拖拽
        self.tree.setDefaultDropAction(Qt.DropAction.MoveAction)  # ✅ 确保 Qt 被正确导入
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)  # ✅ 只允许选一个拖动

        layout.addWidget(self.tree)

        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(1, 120)
        self.tree.setColumnWidth(2, 60)
        self.tree.setColumnWidth(3, 100)

        self.root = QTreeWidgetItem(self.tree, ["Root", "Root", "", ""])
        self.tree.addTopLevelItem(self.root)

        # ✅ **默认展开 Root 结点**
        self.tree.expandItem(self.root)

        # ✅ 启用 itemChanged 信号，以便用户可以修改房间的 Ratio
        self.tree.itemChanged.connect(self.handle_item_changed)

        # ✅ 按钮区域（添加 & 删除）
        button_layout = QHBoxLayout()
        self.add_group_button = QPushButton("➕ Add Group")
        self.add_room_button = QPushButton("➕ Add Room")
        self.delete_button = QPushButton("🗑 Delete")

        self.add_group_button.clicked.connect(self.add_group)
        self.add_room_button.clicked.connect(self.add_room)
        self.delete_button.clicked.connect(self.delete_node)

        button_layout.addWidget(self.add_group_button)
        button_layout.addWidget(self.add_room_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        page.setLayout(layout)
        return page
    
    def add_group(self):
        """添加 Group，确保 ID 复用"""
        # ✅ **分配 Group ID**
        if self.available_group_ids:
            group_id = min(self.available_group_ids)  # ✅ 复用最小的 ID
            self.available_group_ids.remove(group_id)
        else:
            group_id = self.next_group_id
            self.next_group_id += 1  # ✅ 只在没有可用 ID 时递增

        group_name = f"Group {group_id}"  # ✅ 生成 Group 名称
        new_group = QTreeWidgetItem([group_name, "Group", ""])
        
        selected_item = self.tree.currentItem()

        # ✅ 如果选中了 Group，就作为它的子分组，否则放入 Root
        if selected_item and selected_item.text(1) == "Group":
            selected_item.addChild(new_group)
        else:
            self.root.addChild(new_group)
        
        # ✅ **默认展开新创建的 Group**
        self.tree.expandItem(new_group)
        self.structureChanged.emit()

    def add_room(self):
        selected_item = self.tree.currentItem()
        if selected_item and selected_item.text(1) not in ["Root", "Group"]:
            QMessageBox.warning(self, "Error", "Please select Root or a Group to add a Room.")
            return

        type_selector = QComboBox()
        type_selector.addItems(ROOM_TYPES)

        ratio_input = QSpinBox()
        ratio_input.setRange(1, 100)
        ratio_input.setValue(1)

        max_floor_input = QSpinBox()
        max_floor_input.setRange(0, 7)
        max_floor_input.setValue(7)

        msg_box = QMessageBox()
        msg_box.setWindowTitle("Add Room")
        msg_box.setText("Select room type, ratio and max floor-objs.")
        msg_box.layout().addWidget(type_selector)
        msg_box.layout().addWidget(ratio_input)
        msg_box.layout().addWidget(max_floor_input)

        add_button = msg_box.addButton("Add", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg_box.exec()

        if msg_box.clickedButton() == cancel_button:
            return

        selected_type = type_selector.currentText()
        ratio_value = str(ratio_input.value())
        max_floor_value = str(max_floor_input.value())

        if self.available_room_ids:
            room_id = min(self.available_room_ids)
            self.available_room_ids.remove(room_id)
        else:
            room_id = self.next_room_id
            self.next_room_id += 1

        room_name = f"Room {room_id}"
        new_room = QTreeWidgetItem([room_name, selected_type, ratio_value, max_floor_value])
        new_room.setFlags(new_room.flags() | Qt.ItemFlag.ItemIsEditable)

        if selected_item and selected_item.text(1) == "Group":
            selected_item.addChild(new_room)
        else:
            self.root.addChild(new_room)

        self.update_room_list()
        self.structureChanged.emit()


    ## **🎛️ 允许修改房间的 Ratio**
    def handle_item_changed(self, item, column):
        if column == 2:  # 只处理 Ratio 列的修改
            if item.text(1) == "Group":
                item.setText(2, "")  # ✅ Group 不应该有 Ratio，强制清空
            else:
                try:
                    ratio = int(item.text(2))
                    if ratio < 1 or ratio > 100:
                        raise ValueError
                except ValueError:
                    item.setText(2, "1")  # ✅ 如果输入非法值，恢复默认值 1
        self.structureChanged.emit()
    

    def delete_node(self):
        """删除 Room 或 Group，并确保 ID 复用"""
        selected_item = self.tree.currentItem()
        if selected_item and selected_item != self.root:  # ✅ Root 不能被删除
            parent = selected_item.parent()
            if parent:
                parent.removeChild(selected_item)
            else:
                index = self.tree.indexOfTopLevelItem(selected_item)
                self.tree.takeTopLevelItem(index)

            # ✅ 解析房间 ID
            node_name = selected_item.text(0)  # 例如："Room 2" 或 "Group 3"
            
            if node_name.startswith("Room "):
                room_id = int(node_name.split(" ")[1])
                self.available_room_ids.add(room_id)  # ✅ 释放 Room ID
            elif node_name.startswith("Group "):
                group_id = int(node_name.split(" ")[1])
                self.available_group_ids.add(group_id)  # ✅ 释放 Group ID
            self.structureChanged.emit()

    def dropEvent(self, event):
        target_item = self.tree.itemAt(event.pos())
        selected_item = self.tree.selectedItems()[0] if self.tree.selectedItems() else None

        if not target_item or not selected_item:
            return

        target_type = target_item.text(1)
        selected_type = selected_item.text(1)

        # ✅ Room 只能拖到 Root 或 Group
        if selected_type == "Room" and target_type not in ["Root", "Group"]:
            return  

        # ✅ Group 可以自由拖动
        event.accept()

        super(HouseDesigner, self).dropEvent(event)

    def create_floor_wall_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        # ✅ 只有 3 列：Room (ID + Type)、Object Type、Asset Type
        self.table_floor_wall = QTableWidget(0, 3)
        self.table_floor_wall.setHorizontalHeaderLabels(["Room", "Object Type", "Asset Type"])
        self.table_floor_wall.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # ✅ 允许整行选中 + 交替行颜色
        self.table_floor_wall.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_floor_wall.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_floor_wall.setAlternatingRowColors(True)  # ✅ 交替行颜色

        # ✅ 调整列宽
        self.table_floor_wall.setColumnWidth(0, 200)
        self.table_floor_wall.setColumnWidth(1, 120)
        self.table_floor_wall.setColumnWidth(2, 150)
        self.table_floor_wall.horizontalHeader().setStretchLastSection(True)

        # ✅ 按钮布局
        button_layout = QHBoxLayout()
        self.add_object_button = QPushButton("➕ Add Object")
        self.add_object_button.clicked.connect(self.add_floor_wall_object)

        self.delete_object_button = QPushButton("🗑 Delete Object")
        self.delete_object_button.clicked.connect(self.delete_selected_object)

        button_layout.addWidget(self.add_object_button)
        button_layout.addWidget(self.delete_object_button)

        layout.addWidget(self.table_floor_wall)
        layout.addLayout(button_layout)

        page.setLayout(layout)

        return page


    def add_floor_wall_object(self):
        if not hasattr(self, "room_list") or not self.room_list:
            self.update_floor_wall_page()

        row = self.table_floor_wall.rowCount()
        self.table_floor_wall.insertRow(row)

        # 第一列：Room 选择
        if self.room_list == [("Random", "Random")]:
            room_combo = QComboBox()
            room_combo.addItem("Random")
            room_combo.setEnabled(False)
        else:
            room_combo = QComboBox()
            room_options = [f"{rid} ({rtype})" for rid, rtype in self.room_list]
            room_combo.addItems(room_options)
            room_combo.installEventFilter(self)
        self.table_floor_wall.setCellWidget(row, 0, room_combo)

        # 第二列：Object Type
        object_type_combo = QComboBox()
        object_type_combo.addItems(["Floor Object", "Wall Object"])
        object_type_combo.installEventFilter(self)
        self.table_floor_wall.setCellWidget(row, 1, object_type_combo)

        # 第三列：Asset Type
        asset_combo = QComboBox()
        asset_combo.installEventFilter(self)
        self.table_floor_wall.setCellWidget(row, 2, asset_combo)

        # 动态更新 asset 列
        object_type_combo.currentIndexChanged.connect(lambda _: self.update_asset_options(row, object_type_combo))
        room_combo.currentIndexChanged.connect(lambda _: self.update_asset_options(row, object_type_combo))

        # 初始化 asset 列
        self.update_asset_options(row, object_type_combo)

        # 生成唯一 object_id
        existing = [
            w.property("object_id")
            for r in range(row)
            if (w := self.table_floor_wall.cellWidget(r, 2))
        ]
        default_asset = asset_combo.currentText()
        same_type_count = sum(1 for oid in existing if oid and oid.startswith(default_asset))
        room_text = room_combo.currentText().split(" (")[0]
        object_id = f"{default_asset}_{same_type_count + 1}({room_text})"
        asset_combo.setProperty("object_id", object_id)

        self.update_small_objs_page()
        self.floorWallChanged.emit()

    def update_object_options(self, row):
        room_combo = self.table_floor_wall.cellWidget(row, 0)
        if not room_combo:
            return
        selected_room = room_combo.currentText()
        # 提取括号内的房间类型，例如 "1 (Bedroom)" 提取 "Bedroom"
        m = re.search(r'\((.*?)\)', selected_room)
        room_type = m.group(1) if m else selected_room
        object_types_by_room = {
            "Bedroom": ["Floor Object", "Wall Object"],
            "Bathroom": ["Floor Object", "Wall Object"],
            "Kitchen": ["Floor Object", "Wall Object"],
            "LivingRoom": ["Floor Object", "Wall Object"],
            "Random": ["Floor Object", "Wall Object"]
        }
        object_type_options = object_types_by_room.get(room_type, ["Floor Object", "Wall Object"])
        object_type_combo = self.table_floor_wall.cellWidget(row, 1)
        if object_type_combo:
            try:
                object_type_combo.currentIndexChanged.disconnect()
            except Exception:
                pass
            object_type_combo.clear()
            object_type_combo.addItems(object_type_options)
            object_type_combo.currentIndexChanged.connect(lambda: self.update_asset_options(row, object_type_combo))
        self.update_asset_options(row, object_type_combo)


    def update_room_list(self):
        self.room_list = []
        self.room_max_floor_obj = {}
        def extract_rooms(item):
            if item.text(1) in ["Bedroom", "Bathroom", "Kitchen", "LivingRoom"]:
                name = item.text(0)
                self.room_list.append((name, item.text(1)))
                try:
                    mf = int(item.text(3))
                except ValueError:
                    mf = 7
                self.room_max_floor_obj[name] = mf
            for i in range(item.childCount()):
                extract_rooms(item.child(i))
        extract_rooms(self.root)
        if not self.room_list:
            self.room_list = [("Random", "Random")]
            self.room_max_floor_obj = {"Random": float("inf")}
        print(f"Rooms: {self.room_list}, max floors: {self.room_max_floor_obj}")



    def update_floor_wall_page(self):
        """更新第二页房间列表，确保 room_list 为空时，默认填充 Random"""
        self.room_list = []  # ✅ 确保 room_list 存在
        self.table_floor_wall.setRowCount(0)  # ✅ 清空表格

        # ✅ 遍历 Root 及其子节点，提取房间信息
        def extract_rooms(item):
            if item.text(1) in ["Bedroom", "Bathroom", "Kitchen", "LivingRoom"]:
                self.room_list.append((item.text(0), item.text(1)))  # ✅ (room_id, room_type)
            for i in range(item.childCount()):
                extract_rooms(item.child(i))

        extract_rooms(self.root)  # ✅ 递归查找所有房间

        # ✅ **如果 room_list 为空，默认填充 Random**
        if not self.room_list:
            self.room_list = [("Random", "Random")]

        print(f"Updated Room List: {self.room_list}")  # ✅ 调试信息
        self.structureChanged.emit()

    def update_room_comboboxes(self):
        """
        更新 Floor/Wall 页（第二页）和 Small Objects 页（第三页）的房间下拉菜单：
        - 对于每一行，先读取现有下拉框当前选项（old_value）。
        - 用 self.room_list 生成新的有效选项列表 new_items（格式为 "room_id (room_type)"，同时包含 "Random"）。
        - 如果 old_value 存在于 new_items 中，则更新该下拉框的选项（保留 old_value 作为当前选中项）。
        - 如果 old_value 不在 new_items 中，则删除该行（认为该条目引用了已删除的房间）。
        """
        # 生成新的房间选项列表，格式统一为 "room_id (room_type)"（如果存在真实房间），否则只有 "Random"
        if self.room_list != [("Random", "Random")]:
            new_items = ["Random"] + [f"{room_id} ({room_type})" for room_id, room_type in self.room_list]
        else:
            new_items = ["Random"]

        valid_set = set(new_items)

        # 更新 Floor/Wall 页第一列
        for row in range(self.table_floor_wall.rowCount()-1, -1, -1):
            room_combo = self.table_floor_wall.cellWidget(row, 0)
            if room_combo is not None:
                old_value = room_combo.currentText()
                if old_value in valid_set:
                    room_combo.blockSignals(True)
                    room_combo.clear()
                    room_combo.addItems(new_items)
                    room_combo.setCurrentText(old_value)
                    room_combo.blockSignals(False)
                else:
                    # 如果当前选项已不在新列表中，则删除这一行
                    self.table_floor_wall.removeRow(row)

        # 更新 Small Objects 页第一列
        for row in range(self.table_small_objs.rowCount()-1, -1, -1):
            room_combo = self.table_small_objs.cellWidget(row, 0)
            if room_combo is not None:
                old_value = room_combo.currentText()
                if old_value in valid_set:
                    room_combo.blockSignals(True)
                    room_combo.clear()
                    room_combo.addItems(new_items)
                    room_combo.setCurrentText(old_value)
                    room_combo.blockSignals(False)
                else:
                    self.table_small_objs.removeRow(row)


    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn and isinstance(obj, QComboBox):
            # ✅ 让 QComboBox 被点击时，选中对应的行
            index = self.table_floor_wall.indexAt(obj.pos())
            if index.isValid():
                self.table_floor_wall.selectRow(index.row())  # ✅ 选中该行
        return super().eventFilter(obj, event)


    def delete_selected_object(self):
        """删除选中的 Floor/Wall Object，并更新 `small obj` 选项"""
        selected_indexes = self.table_floor_wall.selectionModel().selectedRows()
        
        if not selected_indexes:
            QMessageBox.warning(self, "Error", "Please select an object to delete!")
            return

        selected_rows = sorted([index.row() for index in selected_indexes], reverse=True)

        for row in selected_rows:
            self.table_floor_wall.removeRow(row)

        self.update_small_objs_page()  # ✅ 删除后更新第三页


    ## **📌 获取用户选中的房间**
    def get_selected_room(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return None

        selected_item = selected_items[0]
        if selected_item.text(1) not in ["Bedroom", "Bathroom", "Kitchen", "LivingRoom"]:
            return None

        return selected_item.text(0), selected_item.text(1)


    def create_small_objs_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        # ✅ 只有 3 列：Room (ID + Type)、Small Object、Placed On (Floor Object)
        self.table_small_objs = QTableWidget(0, 3)  # ✅ 初始为空，后续动态更新
        self.table_small_objs.setHorizontalHeaderLabels(["Room", "Small Object", "Placed On"])
        self.table_small_objs.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # ✅ Room ID & Type 不可编辑

        # ✅ 允许整行选中
        self.table_small_objs.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_small_objs.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # ✅ 调整列宽
        self.table_small_objs.setColumnWidth(0, 200)
        self.table_small_objs.setColumnWidth(1, 120)
        self.table_small_objs.setColumnWidth(2, 150)
        self.table_small_objs.horizontalHeader().setStretchLastSection(True)


        # ✅ 按钮布局
        button_layout = QHBoxLayout()
        self.add_small_obj_button = QPushButton("➕ Add Small Object")
        self.add_small_obj_button.clicked.connect(self.add_small_object)

        self.delete_small_obj_button = QPushButton("🗑 Delete Small Object")
        self.delete_small_obj_button.clicked.connect(self.delete_selected_small_object)

        button_layout.addWidget(self.add_small_obj_button)
        button_layout.addWidget(self.delete_small_obj_button)

        layout.addWidget(self.table_small_objs)
        layout.addLayout(button_layout)

        page.setLayout(layout)
        return page


    def add_small_object(self):
        """添加 Small Object，确保 Placed On 选项包含 floor obj"""
        row = self.table_small_objs.rowCount()
        self.table_small_objs.insertRow(row)

        # 第一列：Room 选择
        room_combo = QComboBox()
        if self.room_list == [("Random", "Random")]:
            room_combo.addItem("Random")
            room_combo.setEnabled(False)
        else:
            room_options = ["Random"] + [f"{room_id} ({room_type})" for room_id, room_type in self.room_list]
            room_combo.addItems(room_options)
            room_combo.installEventFilter(self)
            # 连接信号更新 Placed On 选项
            room_combo.currentIndexChanged.connect(
                lambda: self.update_floor_object_options(row, room_combo, place_combo)
            )
        self.table_small_objs.setCellWidget(row, 0, room_combo)


        # ✅ **第二列：Small Object 选择框**
        small_combo = QComboBox()
        small_combo.addItems(SMALL_OBJECTS)
        small_combo.installEventFilter(self)
        self.table_small_objs.setCellWidget(row, 1, small_combo)

        # === 第三列：Placed On 选择 ===
        # 先根据第一列当前的选项获取 Floor 对象（调用 get_floor_objects_for_room）
        selected_room = room_combo.currentText()  # 默认取当前选中项
        floor_objects = self.get_floor_objects_for_room(selected_room)
        place_combo = QComboBox()
        place_combo.addItems(["Random"] + floor_objects)
        place_combo.installEventFilter(self)
        self.table_small_objs.setCellWidget(row, 2, place_combo)

        # ✅ 监听房间选择变化，动态更新 Placed On
        if self.room_list != [("Random", "Random")]:
            room_combo.currentIndexChanged.connect(lambda: self.update_floor_object_options(row, room_combo, place_combo))


    def get_floor_objects_for_room(self, selected_room):
        """获取 `floor obj`，支持 `Random` 和 真实房间，确保编号按房间独立"""
        floor_objects = []
        object_count = {}  # 按 `房间` 统计物品编号

        for row in range(self.table_floor_wall.rowCount()):
            room_combo = self.table_floor_wall.cellWidget(row, 0)
            object_type_combo = self.table_floor_wall.cellWidget(row, 1)
            asset_combo = self.table_floor_wall.cellWidget(row, 2)

            if object_type_combo and asset_combo:
                room_text = room_combo.currentText() if room_combo else "Random"
                asset_name = asset_combo.currentText()

                # ✅ 仅收集 Floor Object
                if object_type_combo.currentText() == "Floor Object" and (selected_room == "Random" or room_text == selected_room):
                    # ✅ 计算当前房间的编号
                    if room_text not in object_count:
                        object_count[room_text] = {}  # 按房间存储编号
                    object_count[room_text][asset_name] = object_count[room_text].get(asset_name, 0) + 1
                    
                    object_id = f"{asset_name}_{object_count[room_text][asset_name]}({room_text})"

                    # not every floor object is a receptacle; filter out non-receptacle objects
                    if asset_name in RECEPTACLES:
                        floor_objects.append(object_id)

        return floor_objects


    def update_small_objs_page(self):
        """
        更新 Small Objects 页中所有行的“Placed On”下拉菜单，
        根据每一行第一列（Room）的当前选择，
        从第二页的 Floor/Wall 对象中获取最新数据进行更新。
        """
        for row in range(self.table_small_objs.rowCount()):
            # 始终使用 cellWidget 获取 QComboBox（而不是 item）
            room_combo = self.table_small_objs.cellWidget(row, 0)
            place_combo = self.table_small_objs.cellWidget(row, 2)
            if not room_combo or not place_combo:
                continue  # 如果某行没有正确的控件则跳过

            selected_room = room_combo.currentText()  # 从 QComboBox 获取当前选择
            available_floor_objects = self.get_floor_objects_for_room(selected_room)
            current_selection = place_combo.currentText()

            place_combo.clear()
            place_combo.addItems(["Random"] + available_floor_objects)
            # 如果之前的选项仍存在则保持选中
            if current_selection in available_floor_objects:
                place_combo.setCurrentText(current_selection)


    def update_asset_options(self, row, object_type_combo):
        """根据第一列（房间类型）和第二列（Object Type）动态更新 Asset Type 选项"""
        
        asset_combo = self.table_floor_wall.cellWidget(row, 2)
        if asset_combo is None:
            return
        asset_combo.clear()

        room_combo = self.table_floor_wall.cellWidget(row, 0)
        selected_room = room_combo.currentText() if room_combo else "Random"
        m = re.search(r'\((.*?)\)', selected_room)
        room_type = m.group(1) if m else selected_room

        # ✅ 获取第二列（Object Type）的选择
        selected_type = object_type_combo.currentText()

        # ✅ 根据房间和 Object Type 选择 Asset Type
        asset_options = {
            ("LivingRoom", "Floor Object"): LIV_FLOOR,
            ("LivingRoom", "Wall Object"): WALL_OBJS,

            ("Bedroom", "Floor Object"): BED_FLOOR,
            ("Bedroom", "Wall Object"): WALL_OBJS,

            ("Kitchen", "Floor Object"): KIT_FLOOR,
            ("Kitchen", "Wall Object"): WALL_OBJS,

            ("Bathroom", "Floor Object"): BAT_FLOOR,
            ("Bathroom", "Wall Object"): WALL_OBJS,

            ("Random", "Floor Object"): LIV_FLOOR+BED_FLOOR+KIT_FLOOR+BAT_FLOOR,
            ("Random", "Wall Object"): WALL_OBJS,
        }

        options = asset_options.get((room_type, selected_type), ["Default Item"])

        # ✅ 更新 Asset Type 下拉菜单
        asset_combo.addItems(options)

        # ✅ 生成 object_id，确保唯一性
        new_id = f"{options[0]}_{row+1}({selected_room})"
        asset_combo.setProperty("object_id", new_id)

        print(f"Updated row {row}: Room={selected_room}, Object Type={selected_type}, Assets={options}")
        self.floorWallChanged.emit()


    def next_page(self):
        if self.current_page == 1:
            # 检查每个房间的 Floor Object 是否超限
            violations = []
            for room_name, max_allowed in self.room_max_floor_obj.items():
                if room_name == "Random":
                    continue
                count = 0
                for r in range(self.table_floor_wall.rowCount()):
                    room_combo = self.table_floor_wall.cellWidget(r, 0)
                    obj_type_combo = self.table_floor_wall.cellWidget(r, 1)
                    if room_combo and obj_type_combo:
                        rc = room_combo.currentText().split(" (")[0]
                        if rc == room_name and obj_type_combo.currentText() == "Floor Object":
                            count += 1
                if count > max_allowed:
                    violations.append(f"{room_name}: {count}/{max_allowed}")
            if violations:
                QMessageBox.warning(
                    self,
                    "Limit Exceeded",
                    "The following rooms have exceeded the maximum number of Floor Objects: \n" + "\n".join(violations)
                )
                return
            # 通过检查后再更新第三页
            self.update_small_objs_page()

        self.current_page = min(2, self.current_page + 1)
        self.stacked_widget.setCurrentIndex(self.current_page)
        self.update_buttons()


    def update_floor_object_options(self, row, room_combo, place_combo):
        """当用户更改房间选择时，自动更新 Floor Objects 选项，确保编号唯一"""
        selected_room = room_combo.currentText()
        new_floor_objects = self.get_floor_objects_for_room(selected_room)
        place_combo.clear()
        place_combo.addItems(["Random"] + new_floor_objects)

    def delete_selected_small_object(self):
        selected_indexes = self.table_small_objs.selectionModel().selectedRows()

        if not selected_indexes:
            QMessageBox.warning(self, "Error", "Please select a small object to delete!")
            return

        selected_rows = sorted([index.row() for index in selected_indexes], reverse=True)

        for row in selected_rows:
            self.table_small_objs.removeRow(row)


    ## **📌 切换页面逻辑**
    def prev_page(self):
        self.current_page = max(0, self.current_page - 1)
        self.stacked_widget.setCurrentIndex(self.current_page)
        self.update_buttons()


    def update_buttons(self):
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < 2)
        self.confirm_button.setVisible(self.current_page == 2)


    def extract_structure(self):
        """递归提取树状结构，从 Root 开始"""
        def traverse(item):
            node_data = {
                "name": item.text(0),
                "type": item.text(1),
                "ratio": item.text(2) if item.text(1) not in ["Group", "Root"] else "",
                "children": []
            }
            for i in range(item.childCount()):
                child = item.child(i)
                node_data["children"].append(traverse(child))
            return node_data

        return traverse(self.root)


    def extract_floor_wall_objects(self):
        
        floor_objs = []
        WALL_OBJS = []
        for row in range(self.table_floor_wall.rowCount()):
            # 第一列：获取房间信息
            room_widget = self.table_floor_wall.cellWidget(row, 0)
            if room_widget and isinstance(room_widget, QComboBox):
                room_text = room_widget.currentText()
            else:
                room_item = self.table_floor_wall.item(row, 0)
                room_text = room_item.text() if room_item else "Random"
            
            # 如果 room_text 为 "Random"（忽略大小写），则直接使用 "Random"
            # 否则提取其中的数字
            if room_text.strip().lower() == "random":
                room = "Random"
            else:
                match = re.search(r'\d+', room_text)
                room = match.group() if match else room_text
            
            # 第二列：获取 object type
            object_type_widget = self.table_floor_wall.cellWidget(row, 1)
            object_type = object_type_widget.currentText() if object_type_widget else ""
            
            # 第三列：获取 asset，直接使用 currentText()，避免 property 没有更新
            asset_widget = self.table_floor_wall.cellWidget(row, 2)
            if asset_widget and isinstance(asset_widget, QComboBox):
                asset_id = asset_widget.currentText()
            else:
                asset_id = ""
            
            obj = {
                "room": room,
                "object_type": object_type,
                "asset": asset_id
            }
            
            # 根据 object_type 判断属于哪一类
            if object_type.strip().lower().startswith("wall"):
                WALL_OBJS.append(obj)
            else:
                floor_objs.append(obj)
        
        return {"floor_objects": floor_objs, "wall_objects": WALL_OBJS}



    def extract_small_objects(self):
        """提取第三页（Small Objects）的数据"""
        objects = []
        for row in range(self.table_small_objs.rowCount()):
            # 第一列：房间选择
            room_widget = self.table_small_objs.cellWidget(row, 0)
            if room_widget and isinstance(room_widget, QComboBox):
                room_text = room_widget.currentText()
            else:
                room_item = self.table_small_objs.item(row, 0)
                room_text = room_item.text() if room_item else "Random"

            if room_text.strip().lower() == "random":
                room = "Random"
            else:
                match = re.search(r'\d+', room_text)
                room = match.group() if match else room_text

            # 第二列：Small Object 选择
            small_obj_widget = self.table_small_objs.cellWidget(row, 1)
            small_object = small_obj_widget.currentText() if small_obj_widget else ""

            # 第三列：Placed On 选择
            placed_on_widget = self.table_small_objs.cellWidget(row, 2)
            placed_on = placed_on_widget.currentText() if placed_on_widget else ""

            # fourth column: type of receptacle
            receptacle_type  = placed_on.split("_")[0] if placed_on else ""

            objects.append({
                "room": room,
                "small_object": small_object,
                "placed_on": placed_on,
                "receptacle_type": receptacle_type
            })
        return objects


    def confirm_selection(self):
        self.update_room_list()
        house_settings = {
            "structure": self.extract_structure(),
            "floor_wall_objects": self.extract_floor_wall_objects(),
            "small_objects": self.extract_small_objects(),
            "randomize_rest": self.randomize_checkbox.isChecked(),
            "room_max_floor_obj": self.room_max_floor_obj
        }
        
        json_output = json.dumps(house_settings, indent=4, ensure_ascii=False)
        print(json_output)

        proc = multiprocessing.Process(target=process_house_settings, args=(house_settings,))
        proc.start()

        # 使用 QThread 在后台运行 process_house_settings
        self.worker = ProcessWorker(house_settings)
        self.worker.finished_signal.connect(self.on_process_finished)
        self.worker.start()



    def on_process_finished(self):
        print("process_house_settings Completed")

def process_house_settings(house_settings):
    rs = structure_to_roomspec(house_settings['structure'])

    room_spec_sampler =RoomSpecSampler([rs])
    house_generator = HouseGenerator(
        split="train", seed=50, room_spec_sampler=room_spec_sampler,
         user_defined_params = house_settings)

    house, _ = house_generator.sample(return_partial_houses=False)
    house.to_json("temp4.json")
    print("House saved to temp4.json")

if __name__ == "__main__":
        
    app = QApplication(sys.argv)
    designer = HouseDesigner()
    designer.show()
    sys.exit(app.exec())
