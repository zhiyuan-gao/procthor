import numpy as np

def sort_rectangle_vertices(points):
    """
    Sorts vertices into two rectangles, with specific ordering:
    Index 0-3: Large rectangle (0: bottom-left, 1: top-left, 2: top-right, 3: bottom-right)
    Index 4-7: Small rectangle (4: bottom-left, 5: top-left, 6: top-right, 7: bottom-right)

    :param points: List of 8 points (x, y) representing two rectangles.
    :return: np.array of sorted points.
    """
    # Convert points to numpy array for easy manipulation
    points = np.array(points)
    
    # Determine the bounding box for the entire set of points
    xmin, xmax = points[:, 0].min(), points[:, 0].max()
    ymin, ymax = points[:, 1].min(), points[:, 1].max()
    
    # Find the center of the whole set of points
    xmid, ymid = (xmin + xmax) / 2, (ymin + ymax) / 2
    
    # Separate points into large and small rectangles
    large_rect_points = []
    small_rect_points = []
    
    for point in points:
        if abs(point[0] - xmid) > abs(xmax - xmid) / 2 or abs(point[1] - ymid) > abs(ymax - ymid) / 2:
            large_rect_points.append(point)
        else:
            small_rect_points.append(point)
    
    # Function to sort points in the order: bottom-left, top-left, top-right, bottom-right
    def sort_rectangle(pts):
        pts = sorted(pts, key=lambda p: (p[0], p[1]))  # First sort by x, then by y
        return [pts[0], pts[2], pts[3], pts[1]]  # Rearrange to bottom-left, top-left, top-right, bottom-right

    # Sort points within each rectangle
    large_rect_points = sort_rectangle(large_rect_points)
    small_rect_points = sort_rectangle(small_rect_points)
    
    # Combine results into a single np.array
    sorted_points = np.array(large_rect_points + small_rect_points)
    return sorted_points

# Example usage
points = [(-1.5, -1.5), (-1.5, 1.5), (1.5, -1.5), (1.5, 1.5),
          (-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5), (0.5, 0.5)]

sorted_points = sort_rectangle_vertices(points)

# Output the sorted np.array
print("Sorted points array:")
print(sorted_points)
