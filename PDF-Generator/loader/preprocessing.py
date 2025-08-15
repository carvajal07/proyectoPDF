import xml.etree.ElementTree as ET
from collections import defaultdict, deque

def topological_sort(connections: ET.Element) -> list:
    '''Realiza un ordenamiento topológico de los nodos basándose en las conexiones.
    Args:
        connections (ET.Element): Elemento XML que contiene las conexiones entre nodos.
    Returns:
        list: Lista de nodos ordenados topológicamente.
    Raises:
        ValueError: Si el grafo tiene un ciclo y no se puede ordenar topológicamente.        
    '''
    graph = defaultdict(set)
    in_degree = defaultdict(int)
    nodes = set()

    for conn in connections:
        source = conn.find("From").text
        target = conn.find("To").text
        graph[source].add(target)
        in_degree[target] += 1
        nodes.update([source, target])

    # Asegurar que todos los nodos estén en in_degree (aunque tengan 0)
    for node in nodes:
        in_degree.setdefault(node, 0)

    # Paso 2: Ordenamiento topológico (Kahn's algorithm)
    queue = deque([node for node in nodes if in_degree[node] == 0])
    sorted_nodes = []

    while queue:
        current = queue.popleft()
        sorted_nodes.append(current)
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Verificar si hubo ciclo
    if len(sorted_nodes) != len(nodes):
        print("⚠️ Error: El grafo tiene un ciclo y no se puede ordenar topológicamente.")

    return sorted_nodes
