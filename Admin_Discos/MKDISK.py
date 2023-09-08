# Importando las librerias necesarias
import os
from Discos.MBR import MBR

# Función para crear un disco
def mkdisk(params):
    # Extraer los parámetros con valores predeterminados si no se han proporcionado
    size_param = params.get('size').replace(' ', '')
    size = int(size_param)
    path_param = params.get('path').replace('"', '').replace('.dsk ', '.dsk')
    unit = params.get('unit', 'M').replace(' ', '')
    fit = params.get('fit', 'FF').replace(' ', '')

    # Calcular el tamaño total en bytes
    if unit == 'M':
        total_size_bytes = size * 1024 * 1024
    elif unit == 'K':
        total_size_bytes = size * 1024        
    else:
        print("Error: El parámetro 'unit' debe ser 'M' o 'K'")
        return

    # Verificar el tipo de ajuste
    if fit not in ['BF', 'FF', 'WF']:
        print(f"El tipo de ajuste es inválido: {fit}")
        return

    # Obtener el path completo del archivo
    full_path = os.path.join(path_param)
    # Si el directorio no existe, crearlo
    directory = os.path.dirname(full_path)    
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Crear o sobrescribir el archivo binario con el tamaño especificado lleno de ceros
    with open(full_path, "wb") as file:
        file.write(b'\0' * total_size_bytes)

    print(f"Disco creado en {full_path} con tamaño de {size}{unit}.")

    
    example = MBR(params)
    
    # Abrir el archivo binario y escribir el registro de MBR
    with open(full_path, "rb+") as file:
        file.seek(0)
        file.write(example.pack())
    