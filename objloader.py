# ============================================================
# УЛУЧШЕННЫЙ ЗАГРУЗЧИК OBJ С ПОДДЕРЖКОЙ MTL
# ============================================================
import os

class MeshData:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "unnamed")
        self.vertex_format = [
            (b'v_pos', 3, 'float'),
            (b'v_normal', 3, 'float'),
            (b'v_tc0', 2, 'float')
        ]
        self.vertices = []
        self.indices = []
        self.material = kwargs.get("material", None)

class ObjLoader:
    def __init__(self, filename):
        self.objects = {}
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self._current_object = "default"
        self._current_material = None
        self.materials = {}
        
        # Загружаем MTL если есть
        mtl_path = filename.replace('.obj', '.mtl')
        if os.path.exists(mtl_path):
            self._load_mtl(mtl_path)
        
        # Загружаем OBJ
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                self._parse_line(line.strip())
        
        self._finish_object()
        print(f"Загружено {len(self.objects)} объектов")
    
    def _load_mtl(self, mtl_path):
        """Парсит MTL файл"""
        current_mat = None
        base_dir = os.path.dirname(mtl_path)
        
        with open(mtl_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                values = line.strip().split()
                if not values:
                    continue
                
                if values[0] == 'newmtl':
                    current_mat = values[1]
                    self.materials[current_mat] = {}
                elif values[0] == 'map_Kd' and current_mat:
                    tex_path = values[1]
                    # Пробуем разные пути
                    for try_path in [
                        os.path.join(base_dir, tex_path),
                        os.path.join('model', tex_path),
                        tex_path
                    ]:
                        if os.path.exists(try_path):
                            self.materials[current_mat]['texture'] = try_path
                            break
                elif values[0] == 'Kd' and current_mat:
                    self.materials[current_mat]['color'] = tuple(map(float, values[1:4]))
    
    def _parse_line(self, line):
        values = line.split()
        if not values:
            return
        
        cmd = values[0]
        
        if cmd == 'o':
            self._finish_object()
            self._current_object = values[1] if len(values) > 1 else "object"
        
        elif cmd == 'v':
            self.vertices.append(tuple(map(float, values[1:4])))
        
        elif cmd == 'vt':
            self.texcoords.append(tuple(map(float, values[1:3])))
        
        elif cmd == 'vn':
            self.normals.append(tuple(map(float, values[1:4])))
        
        elif cmd == 'usemtl':
            self._current_material = values[1] if len(values) > 1 else None
        
        elif cmd == 'f':
            face_verts = []
            face_tex = []
            face_norms = []
            
            for v in values[1:]:
                parts = v.split('/')
                face_verts.append(int(parts[0]))
                if len(parts) > 1 and parts[1]:
                    face_tex.append(int(parts[1]))
                else:
                    face_tex.append(-1)
                if len(parts) > 2 and parts[2]:
                    face_norms.append(int(parts[2]))
                else:
                    face_norms.append(-1)
            
            self.faces.append({
                'verts': face_verts,
                'tex': face_tex,
                'norms': face_norms,
                'material': self._current_material
            })
    
    def _finish_object(self):
        if not self.faces:
            return
        
        mesh = MeshData(name=self._current_object)
        
        # Определяем материал
        if self._current_object in self.materials:
            mesh.material = self.materials[self._current_object]
        
        idx = 0
        for face in self.faces:
            verts = face['verts']
            texs = face['tex']
            norms = face['norms']
            
            # Триангуляция (поддерживает quads)
            indices = list(range(idx, idx + len(verts)))
            for i in range(1, len(verts) - 1):
                mesh.indices.extend([indices[0], indices[i], indices[i + 1]])
            
            for i, v_idx in enumerate(verts):
                v = self.vertices[v_idx - 1] if v_idx <= len(self.vertices) else (0, 0, 0)
                
                n_idx = norms[i] if i < len(norms) else -1
                n = self.normals[n_idx - 1] if n_idx > 0 and n_idx <= len(self.normals) else (0, 1, 0)
                
                t_idx = texs[i] if i < len(texs) else -1
                t = self.texcoords[t_idx - 1] if t_idx > 0 and t_idx <= len(self.texcoords) else (0, 0)
                
                mesh.vertices.extend([v[0], v[1], v[2], n[0], n[1], n[2], t[0], t[1]])
            
            idx += len(verts)
        
        self.objects[self._current_object] = mesh
        self.faces = []
