from pxr import Usd, UsdGeom
import numpy as np

def get_unique_vertices_and_indices(usd_file_path, mesh_path):
    """
    Extracts unique vertex indices and corresponding vertex coordinates from a given Mesh in a USD file.

    :param usd_file_path: Path to the USD file
    :param mesh_path: Path to the target Mesh in the USD file
    :return: (unique_indices, unique_points, remapped_face_indices)
             - unique_indices: Array of unique vertex indices
             - unique_points: Array of vertex coordinates corresponding to unique_indices
             - remapped_face_indices: Remapped face vertex indices array
    """
    # Load the USD Stage
    stage = Usd.Stage.Open(usd_file_path)

    # Find the specific Mesh
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath(mesh_path))

    # Get vertex indices and vertex coordinates
    face_vertex_indices = np.array(mesh.GetFaceVertexIndicesAttr().Get())
    points = np.array(mesh.GetPointsAttr().Get())

    # Remove duplicate vertex indices
    unique_indices, unique_inverse = np.unique(face_vertex_indices, return_inverse=True)

    # Get the unique vertex coordinates
    unique_points = points[unique_indices]

    # Return the results
    return unique_indices, unique_points, unique_inverse


def process_multiple_meshes(usd_file_path, base_path):
    """
    Applies the unique vertex extraction function to all meshes under a specific path in the USD file.

    :param usd_file_path: Path to the USD file
    :param base_path: Base path in the USD file where meshes are located
    :return: Dictionary containing results for each mesh
    """
    # Load the USD Stage
    stage = Usd.Stage.Open(usd_file_path)
    
    # Initialize a dictionary to store results
    mesh_data = {}

    # Iterate over all the prims under the base path
    for prim in stage.Traverse():
        if prim.GetPath().HasPrefix(base_path):
            # Check if the prim is a Mesh
            if prim.IsA(UsdGeom.Mesh):
                mesh_path = prim.GetPath().pathString
                unique_indices, unique_points, remapped_face_indices = get_unique_vertices_and_indices(usd_file_path, mesh_path)
                mesh_data[mesh_path] = {
                    "unique_indices": unique_indices,
                    "unique_points": unique_points,
                    "remapped_face_indices": remapped_face_indices
                }

    return mesh_data


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


# # Example usage
# usd_file_path = "path_to_your_file.usd"
# base_path = "/path/to/your/meshes"

# mesh_results = process_multiple_meshes(usd_file_path, base_path)

# for mesh_path, data in mesh_results.items():
#     print(f"Mesh: {mesh_path}")
#     print("Unique Vertex Indices:", data["unique_indices"])
#     print("Unique Points (Vertices):", data["unique_points"])
#     print("Remapped Face Vertex Indices:", data["remapped_face_indices"])
