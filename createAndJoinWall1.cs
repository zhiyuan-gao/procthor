        public static GameObject createAndJoinWall(
            int index,
            AssetMap<Material> materialDb,
            Wall toCreate,
            Wall previous = null,
            Wall next = null,
            float visibilityPointInterval = 1 / 3.0f,
            float minimumBoxColliderThickness = 0.1f,
            bool globalVertexPositions = false,
            int layer = 8,
            bool squareTiling = false,
            bool backFaces = false
        ) {
            var wallGO = new GameObject(toCreate.id);

            SetLayer<Transform>(wallGO, layer);

            var meshF = wallGO.AddComponent<MeshFilter>();

            Vector3 boxCenter = Vector3.zero;
            Vector3 boxSize = Vector3.zero;

            var generateBackFaces = backFaces;
            const float zeroThicknessEpsilon = 1e-4f;
            var colliderThickness =
                toCreate.thickness < zeroThicknessEpsilon
                    ? minimumBoxColliderThickness
                    : toCreate.thickness;

            var p0p1 = toCreate.p1 - toCreate.p0;

            var mesh = new Mesh();

            var p0p1_norm = p0p1.normalized;

            var normal = Vector3.Cross(p0p1_norm, Vector3.up);

            var center =
                toCreate.p0
                + p0p1 * 0.5f
                + Vector3.up * toCreate.height * 0.5f
                + normal * toCreate.thickness * 0.5f;
            var width = p0p1.magnitude;

            Vector3 p0;
            Vector3 p1;
            var theta =
                -Mathf.Sign(p0p1_norm.z) * Mathf.Acos(Vector3.Dot(p0p1_norm, Vector3.right));

            if (globalVertexPositions) {
                p0 = toCreate.p0;
                p1 = toCreate.p1;

                boxCenter = center;
            } else {
                p0 =
                    -(width / 2.0f) * Vector3.right
                    - new Vector3(0.0f, toCreate.height / 2.0f, toCreate.thickness / 2.0f);
                p1 =
                    (width / 2.0f) * Vector3.right
                    - new Vector3(0.0f, toCreate.height / 2.0f, toCreate.thickness / 2.0f);

                normal = Vector3.forward;
                p0p1_norm = Vector3.right;

                wallGO.transform.position = center;

                wallGO.transform.rotation = Quaternion.AngleAxis(
                    theta * 180.0f / Mathf.PI,
                    Vector3.up
                );
            }

            var colliderOffset = Vector3.zero; //toCreate.thickness < zeroThicknessEpsilon ? normal * colliderThickness : Vector3.zero;

            boxCenter += colliderOffset;

            boxSize = new Vector3(width, toCreate.height, colliderThickness);

            var vertices = new List<Vector3>();
            var triangles = new List<int>();
            var uv = new List<Vector2>();
            var normals = new List<Vector3>();

            var min = p0;
            var max = p1 + new Vector3(0.0f, toCreate.height, 0.0f);

            IEnumerable<BoundingBox> colliderBoundingBoxes = new List<BoundingBox>();

            if (toCreate.hole != null) {
                if (toCreate.hole.holePolygon != null && toCreate.hole.holePolygon.Count != 2) {
                    Debug.LogWarning(
                        $"Invalid `holePolygon` on object of id '{toCreate.hole.id}', only supported rectangle holes, 4 points in polygon. Using `boundingBox` instead."
                    );
                    if (toCreate.hole.holePolygon.Count < 2) {
                        throw new ArgumentException(
                            "$Invalid `holePolygon` on object of id '{toCreate.hole.id}', only supported rectangle holes, 4 points in polygon, polygon has {toCreate.hole.holePolygon.Count}."
                        );
                    }
                }

                var holeBB = getHoleBoundingBox(toCreate.hole);

                var dims = holeBB.max - holeBB.min;
                var offset = new Vector2(holeBB.min.x, holeBB.min.y);

                if (toCreate.hole.wall1 == toCreate.id) {
                    offset = new Vector2(width - holeBB.max.x, holeBB.min.y);
                }

                colliderBoundingBoxes = new List<BoundingBox>()
                {
                    new BoundingBox()
                    {
                        min = p0,
                        max = p0 + p0p1_norm * offset.x + Vector3.up * (toCreate.height)
                    },
                    new BoundingBox()
                    {
                        min = p0 + p0p1_norm * offset.x + Vector3.up * (offset.y + dims.y),
                        max = p0 + p0p1_norm * (offset.x + dims.x) + Vector3.up * (toCreate.height)
                    },
                    new BoundingBox()
                    {
                        min = p0 + p0p1_norm * (offset.x + dims.x),
                        max = p1 + Vector3.up * (toCreate.height)
                    },
                    new BoundingBox()
                    {
                        min = p0 + p0p1_norm * offset.x,
                        max = p0 + p0p1_norm * (offset.x + dims.x) + Vector3.up * (offset.y)
                    }
                };
                const float areaEps = 0.0001f;
                colliderBoundingBoxes = colliderBoundingBoxes
                    .Where(bb => Math.Abs(GetBBXYArea(bb)) > areaEps)
                    .ToList();

                vertices = new List<Vector3>()
                {
                    p0,
                    p0 + new Vector3(0.0f, toCreate.height, 0.0f),
                    p0 + p0p1_norm * offset.x + Vector3.up * offset.y,
                    p0 + p0p1_norm * offset.x + Vector3.up * (offset.y + dims.y),
                    p1 + new Vector3(0.0f, toCreate.height, 0.0f),
                    p0 + p0p1_norm * (offset.x + dims.x) + Vector3.up * (offset.y + dims.y),
                    p1,
                    p0 + p0p1_norm * (offset.x + dims.x) + Vector3.up * offset.y
                };

                triangles = new List<int>()
                {
                    0,
                    1,
                    2,
                    1,
                    3,
                    2,
                    1,
                    4,
                    3,
                    3,
                    4,
                    5,
                    4,
                    6,
                    5,
                    5,
                    6,
                    7,
                    7,
                    6,
                    0,
                    0,
                    2,
                    7
                };

                // This would be for a left hand local axis space, so front being counter-clockwise of topdown polygon from inside the polygon
                // triangles = new List<int>() {
                //     7, 2, 0, 0, 6, 7, 7, 6, 5, 5, 6, 4, 5, 4, 3, 3, 4, 1, 2, 3, 1, 2, 1, 0
                // };

                var toRemove = new List<int>();
                // const float areaEps = 1e-4f;
                for (int i = 0; i < triangles.Count / 3; i++) {
                    var i0 = triangles[i * 3];
                    var i1 = triangles[i * 3 + 1];
                    var i2 = triangles[i * 3 + 2];
                    var area = TriangleArea(vertices, i0, i1, i2);

                    if (area <= areaEps) {
                        toRemove.AddRange(new List<int>() { i * 3, i * 3 + 1, i * 3 + 2 });
                    }
                }
                var toRemoveSet = new HashSet<int>(toRemove);
                triangles = triangles.Where((t, i) => !toRemoveSet.Contains(i)).ToList();

                if (generateBackFaces) {
                    triangles.AddRange(triangles.AsEnumerable().Reverse().ToList());
                }
            } else {
                vertices = new List<Vector3>()
                {
                    p0,
                    p0 + new Vector3(0.0f, toCreate.height, 0.0f),
                    p1 + new Vector3(0.0f, toCreate.height, 0.0f),
                    p1
                };

                triangles = new List<int>() { 1, 2, 0, 2, 3, 0 };

                // Counter clockwise wall definition left hand rule
                // triangles = new List<int>() { 0, 3, 2, 0, 2, 1 };
                if (generateBackFaces) {
                    triangles.AddRange(triangles.AsEnumerable().Reverse().ToList());
                }
            }

            normals = Enumerable.Repeat(-normal, vertices.Count).ToList();
            // normals = Enumerable.Repeat(normal, vertices.Count).ToList();//.Concat(Enumerable.Repeat(-normal, vertices.Count)).ToList();

            uv = vertices
                .Select(v => new Vector2(
                    Vector3.Dot(p0p1_norm, v - p0) / width,
                    v.y / toCreate.height
                ))
                .ToList();

            mesh.vertices = vertices.ToArray();
            mesh.uv = uv.ToArray();
            mesh.normals = normals.ToArray();
            mesh.triangles = triangles.ToArray();
            meshF.sharedMesh = mesh;
            var meshRenderer = wallGO.AddComponent<MeshRenderer>();

            if (toCreate.hole != null) {
                // var meshCollider  = wallGO.AddComponent<MeshCollider>();
                // meshCollider.sharedMesh = mesh;

                var holeColliders = new GameObject($"Colliders");

                holeColliders.transform.parent = wallGO.transform;
                holeColliders.transform.localPosition = Vector3.zero;
                holeColliders.transform.localRotation = Quaternion.identity;

                var i = 0;
                foreach (var boundingBox in colliderBoundingBoxes) {
                    var colliderObj = new GameObject($"Collider_{i}");
                    colliderObj.transform.parent = holeColliders.transform;
                    colliderObj.transform.localPosition = Vector3.zero;
                    colliderObj.transform.localRotation = Quaternion.identity;
                    colliderObj.tag = "SimObjPhysics";
                    colliderObj.layer = 8;
                    var boxCollider = colliderObj.AddComponent<BoxCollider>();
                    boxCollider.center = boundingBox.center();
                    boxCollider.size = boundingBox.size() + Vector3.forward * colliderThickness;
                }
            } else {
                var boxC = wallGO.AddComponent<BoxCollider>();
                boxC.center = boxCenter;
                boxC.size = boxSize;
            }

            // TODO use a material loader that has this dictionary
            //var mats = ProceduralTools.FindAssetsByType<Material>().ToDictionary(m => m.name, m => m);
            // var mats = ProceduralTools.FindAssetsByType<Material>().GroupBy(m => m.name).ToDictionary(m => m.Key, m => m.First());


            var visibilityPointsGO = CreateVisibilityPointsOnPlane(
                toCreate.p0,
                toCreate.p1 - toCreate.p0,
                (Vector3.up * toCreate.height),
                visibilityPointInterval,
                wallGO.transform,
                toCreate.hole
            );

            setWallSimObjPhysics(wallGO, toCreate.id, visibilityPointsGO, boxCenter, boxSize);
            ProceduralTools.setFloorProperties(wallGO, toCreate);

            visibilityPointsGO.transform.parent = wallGO.transform;
            //if (mats.ContainsKey(wall.materialId)) {
            // meshRenderer.sharedMaterial = materialDb.getAsset(toCreate.materialId);
            var dimensions = new Vector2(p0p1.magnitude, toCreate.height);
            var prev_p0p1 = previous.p1 - previous.p0;

            var prevOffset = getWallMaterialOffset(previous.id).GetValueOrDefault(Vector2.zero);
            var offsetX =
                (prev_p0p1.magnitude / previous.material.tilingDivisorX.GetValueOrDefault(1.0f))
                - Mathf.Floor(
                    prev_p0p1.magnitude / previous.material.tilingDivisorX.GetValueOrDefault(1.0f)
                )
                + prevOffset.x;

            var shaderName =
                toCreate.material == null || string.IsNullOrEmpty(toCreate.material.shader)
                    ? "Standard"
                    : toCreate.material.shader;
            // TODO Offset Y would require to get joining walls from above and below
            var mat =
                toCreate.material == null || string.IsNullOrEmpty(toCreate.material.name)
                    ? new Material(Shader.Find(shaderName))
                    : materialDb.getAsset(toCreate.material.name);
            meshRenderer.material = generatePolygonMaterial(
                mat,
                dimensions,
                toCreate.material,
                offsetX,
                0.0f,
                squareTiling: squareTiling
            );

            meshRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.TwoSided;

            meshF.sharedMesh.RecalculateBounds();

            return wallGO;
        }