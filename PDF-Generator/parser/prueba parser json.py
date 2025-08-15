import json
import time
#imprimir la hora de inicio
print("Hora de inicio:", time.strftime("%Y-%m-%d %H:%M:%S"))
def recursive_replace(obj, old, new):
    if isinstance(obj, dict):
        return {k: recursive_replace(v, old, new) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recursive_replace(elem, old, new) for elem in obj]
    elif isinstance(obj, str):
        return obj.replace(old, new)
    else:
        return obj  # no cambia nada si es int, float, bool, None, etc.

start = time.perf_counter()
json_path = "\\\\Cad-fsx-eks.cadena.com.co\\c$\\trident_pvc_75f19d79_8dc5_4cdb_9aa1_67e850e1425d\\Inputs\\20250721\\54287E3F_6006_4E52_AABB_225D1EB3FB41\PE_54287E3F_6006_4E52_AABB_225D1EB3FB41_Parte1.json"
with open(json_path, 'r', encoding="UTF-8") as f:
    json_data = json.load(f)
#imprimir la hora de fin lectura
print("Hora de fin lectura:", time.strftime("%Y-%m-%d %H:%M:%S"))
json_data_replaced = recursive_replace(json_data, "b", "2")
#Imprimir la hora de fin reemplazo
print("Hora de fin reemplazo:", time.strftime("%Y-%m-%d %H:%M:%S"))
#Escribir el JSON modificado a un nuevo archivo
output_path = "D:\output.json"
with open(output_path, 'w', encoding="UTF-8") as f:
    json.dump(json_data_replaced, f, ensure_ascii=False, indent=4)
end = time.perf_counter()
print(f"Tiempo de ejecución: {end - start:.2f} segundos")