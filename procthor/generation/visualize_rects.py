import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Rectangle as MplRectangle

class RectangleMerger:
    def __init__(self, points):
        """
        参数:
          points: 多边形的顶点（所有内角均为直角），例如 L 形
                  [(0, 0), (4, 0), (4, 1), (2, 1), (2, 3), (0, 3)]
        """
        self.points = points
        # 直接从顶点获取唯一的 x 和 y 值，不对边进行额外分割
        self.unique_xs = sorted(list(set(p[0] for p in points)))
        self.unique_ys = sorted(list(set(p[1] for p in points)))
        # 记录多边形的边界
        self.min_x = min(self.unique_xs)
        self.max_x = max(self.unique_xs)
        self.min_y = min(self.unique_ys)
        self.max_y = max(self.unique_ys)

    def is_point_inside(self, point):
        """利用射线法判断点是否在多边形内"""
        x, y = point
        inside = False
        n = len(self.points)
        j = n - 1
        for i in range(n):
            xi, yi = self.points[i]
            xj, yj = self.points[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
                inside = not inside
            j = i
        return inside

    def get_neighboring_rectangles(self):
        """
        遍历由多边形顶点确定的网格单元格，
        若单元格中心在多边形内部，则认为该单元格属于多边形，
        并以 (x0, y0, x1, y1) 的形式保存。
        """
        out = set()
        for x0, x1 in zip(self.unique_xs, self.unique_xs[1:]):
            for y0, y1 in zip(self.unique_ys, self.unique_ys[1:]):
                mid_x = (x0 + x1) / 2.0
                mid_y = (y0 + y1) / 2.0
                if self.is_point_inside((mid_x, mid_y)):
                    out.add((x0, y0, x1, y1))
        return out

    def _join_neighboring_rectangles(self, rects):
        """
        对于当前矩形集合中的每一对矩形，
        若两矩形共享两个角点（即共享一条完整的边），则合并成一个新的矩形，
        返回所有新生成的矩形（不包括原有矩形）。
        """
        orig_rects = rects.copy()
        out = set()
        for rect1 in rects.copy():
            x0_0, y0_0, x1_0, y1_0 = rect1
            points1 = {(x0_0, y0_0), (x0_0, y1_0), (x1_0, y0_0), (x1_0, y1_0)}
            for rect2 in rects - {rect1}:
                x0_1, y0_1, x1_1, y1_1 = rect2
                points2 = {(x0_1, y0_1), (x0_1, y1_1), (x1_1, y0_1), (x1_1, y1_1)}
                if len(points1 & points2) == 2:
                    new_rect = (min(x0_0, x0_1), min(y0_0, y0_1),
                                max(x1_0, x1_1), max(y1_0, y1_1))
                    out.add(new_rect)
        return out - orig_rects

    def get_all_rectangles(self):
        """
        先获取初始矩形集合（单元格），然后不断合并相邻矩形，
        直到不能再产生新的合并矩形为止，返回最终矩形集合。
        """
        neighboring_rectangles = self.get_neighboring_rectangles().copy()
        curr_rects = neighboring_rectangles
        while True:
            rect_candidates = self._join_neighboring_rectangles(curr_rects)
            rects = curr_rects | rect_candidates
            if len(rects) == len(curr_rects):
                return curr_rects
            curr_rects = rects

if __name__ == "__main__":
    # 定义一个由多个矩形组成的凹多边形（所有内角为直角），例如 L 形多边形
    # points = [(0, 0), (4, 0), (4, 1), (2, 1), (2, 3), (0, 3)]

    points = [(0, 0), (0, 5.279), (3.519, 5.279), (3.519, 1.76), (1.76, 1.76), (1.76, 0)]
    # 0 0, 0 5.279, 3.519 5.279, 3.519 1.76, 1.76 1.76, 1.76 0, 0 0
    
    merger = RectangleMerger(points)
    final_rects = merger.get_all_rectangles()
    
    print("最终合并得到的矩形:")
    for rect in sorted(final_rects):
        print(rect)
    
    # 绘制多边形和最终合并的矩形，每个矩形使用不同的颜色
    fig, ax = plt.subplots(figsize=(6,6))
    
    # 绘制初始多边形轮廓
    poly_patch = MplPolygon(points, closed=True, fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(poly_patch)
    
    # 定义颜色列表
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta']
    
    for i, rect in enumerate(sorted(final_rects)):
        x0, y0, x1, y1 = rect
        color = colors[i % len(colors)]
        rect_patch = MplRectangle((x0, y0), x1 - x0, y1 - y0,
                                  facecolor=color, edgecolor='black', alpha=0.5)
        ax.add_patch(rect_patch)
        # 在矩形中心标注编号
        ax.text(x0 + (x1 - x0) / 2, y0 + (y1 - y0) / 2, str(i+1),
                color='white', weight='bold', ha='center', va='center', fontsize=12)
    
    ax.set_xlim(merger.min_x - 1, merger.max_x + 1)
    ax.set_ylim(merger.min_y - 1, merger.max_y + 1)
    ax.set_aspect('equal', adjustable='box')
    ax.set_title("由多边形顶点构成的凹多边形与合并结果")
    ax.set_xlabel("X 轴")
    ax.set_ylabel("Y 轴")
    plt.show()
