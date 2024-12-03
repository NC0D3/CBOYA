# Umbral para segmentar la cebolla del fondo
threshold = 50
scale=34.3

# Función para verificar si un punto está dentro de los límites de la imagen
def in_bounds(x, y, image):
    return 0 <= x < image.shape[0] and 0 <= y < image.shape[1]

def trace_all_paths_from_point_optimized(start_point, skeleton):
  x, y = start_point
  stack = deque([(x, y, 0, [(x, y)], set([(x, y)]))])  # (x, y, distancia, camino recorrido, puntos visitados localmente)
  distances = []
  # Direcciones con costo precalculado
  directions = [
      (1, 0, 1),           # Abajo
      (1, -1, 1.414),      # Diagonal abajo izquierda (aproximación a sqrt(2))
      (1, 1, 1.414),       # Diagonal abajo derecha
      (0, -1, 1),          # Izquierda
      (0, 1, 1)            # Derecha
  ]
  while stack:
      x, y, distance, path, visited_local = stack.pop()
      is_end = True
      for dx, dy, d_cost in directions:
          nx, ny = x + dx, y + dy
          if in_bounds(nx, ny, skeleton) and skeleton[nx, ny] == 1 and (nx, ny) not in visited_local:
              is_end = False
              new_path = path + [(nx, ny)]
              new_visited_local = visited_local | {(nx, ny)}  # Crear un nuevo conjunto con el nuevo punto visitado
              stack.append((nx, ny, distance + d_cost, new_path, new_visited_local))
      # Si es un punto final, almacenar el camino
      if is_end:
          distances.append(distance)
  return distances

def rooteador(frame):
    img = Image.fromarray(frame).convert('L')
    width, height = img.size
    binarized = np.array(img.point(lambda p: 1 if p > threshold else 0, mode='1')).astype(np.uint8)
    smoothed = cv2.GaussianBlur(binarized, (5, 5), 0)
    row_sums = np.sum(smoothed, axis=1)
    row_sums = np.convolve(row_sums, np.ones(5) / 5, mode='same')
    max_img = np.argmax(row_sums)
    row_sums = row_sums[max_img + 300:]
    smoothed = smoothed[max_img + 300:, :]
    img = img.crop((0, max_img + 300, width, height))
    row_sums_derivative = np.abs(np.diff(row_sums)[2:])
    row_sums_derivative = np.convolve(row_sums_derivative, np.ones(10) / 10, mode='same')
    row_sums_derivative = (row_sums_derivative - np.min(row_sums_derivative)) / (np.max(row_sums_derivative) - np.min(row_sums_derivative))
    color_changes = np.sum(np.diff(smoothed, axis=1) != 0, axis=1)
    MaxICC = np.argmax(color_changes)
    AboveI = np.where(row_sums_derivative > 0.5)[0]
    CI = AboveI[np.argmin(np.abs(AboveI - MaxICC))] if len(AboveI) > 0 else None
    if CI is not None:
        Fimg = smoothed[CI:, :]
        skeleton = morphology.skeletonize(Fimg)
        white_pixels = np.argwhere(skeleton)
        top_left = white_pixels.min(axis=0)
        bottom_right = white_pixels.max(axis=0)
        skeleton = skeleton[top_left[0]:bottom_right[0] + 1, top_left[1]:bottom_right[1] + 1]
        skeleton = skeleton[5:, :]
        skeleton[0, :] = skeleton[-1, :] = skeleton[:, 0] = skeleton[:, -1] = 0
        kernel = np.array([[1, 1, 1], [1, 10, 1], [1, 1, 1]])
        neighbor_count = cv2.filter2D(skeleton.astype(np.uint8), -1, kernel)
        tail_points = np.argwhere(neighbor_count == 11)
        begin_points = tail_points[tail_points[:, 0] < 15]
        distances = []
        visited_global = set()
        for start_point in begin_points:
            start_tuple = tuple(start_point)
            if start_tuple not in visited_global:
                distance = trace_all_paths_from_point_optimized(start_tuple, skeleton)
                distances.append(distance)
                visited_global.add(start_tuple)
        distances = [elemento for sublista in distances for elemento in sublista]
        distances=np.array(distances)
        distances=np.sort(distances)
        distances=distances/scale
        rounded=np.round(distances).astype(int)
        # Obtener los índices donde cambia el valor redondeado
        _, index = np.unique(rounded, return_index=True)    
        # Dividir el array flotante usando los índices
        groups = np.split(distances, index[1:])
        # Calcular la media de cada grupo
        means = np.array([np.mean(group) for group in groups])

        return means, skeleton, begin_points
    else:
        print("No hay puntos de inicio.")
        return None
