import matplotlib.pyplot as plt

# 给定点的列表
# points = [
#     (-3.073, -1.5854203, 0),
#     (-3.073, 1.5854203, 0),
#     (-1.20612, -0.5436654, 0),
#     (-1.20612, 0.36767626, 0),
#     (3.073, 1.5854203, 0),
#     (-0.2969494, 0.36767626, 0),
#     (3.073, -1.5854203, 0),
#     (-0.2969494, -0.5436654, 0)
# ]
# Example usage
points = [(-1.5, -1.5), (-1.5, 1.5), (1.5, -1.5), (1.5, 1.5),
          (-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5), (0.5, 0.5)]
# 提取点的x, y坐标
x_coords = [point[0] for point in points]
y_coords = [point[1] for point in points]

# 创建二维图形对象
plt.figure(figsize=(8, 6))

# 绘制点
plt.scatter(x_coords, y_coords, c='r', marker='o')

# 给每个点添加索引作为标签
for i, point in enumerate(points):
    plt.text(point[0], point[1], f'{i}', fontsize=10, color='blue', ha='right')

# 设置轴标签
plt.xlabel('X')
plt.ylabel('Y')

# 显示图形
plt.grid(True)
plt.axhline(0, color='black',linewidth=0.5)
plt.axvline(0, color='black',linewidth=0.5)

plt.show()
