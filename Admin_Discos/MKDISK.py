# Importando las librerias necesarias
import os
from Discos.MBR import MBR

# Función para crear un disco
def mkdisk(params):
    print("\n💽 creando disco...")
    # Extraer los parámetros con valores predeterminados si no se han proporcionado
    size = params.get('size')
    filename = params.get('path')
    unit = params.get('unit', 'M')
    fit = params.get('fit', 'FF')

    # Verificar que se han proporcionado los parámetros obligatorios
    if not size or not filename:
        print("¡Se requieren los parámetros -size y -path!")
        return

    # Calcular el tamaño total en bytes
    if unit == 'K':
        total_size_bytes = size * 1024
    elif unit == 'M':
        total_size_bytes = size * 1024 * 1024
    else:
        print(f"Unidad inválida: {unit}")
        return

    # Verificar el valor de la política de ajuste
    if fit not in ['BF', 'FF', 'WF']:
        print(f"Valor de política de ajuste inválido: {fit}")
        return

    # Obtener el directorio actual
    current_directory = os.getcwd()
    # Combinar el directorio actual con la carpeta de discos y el nombre del archivo
    full_path = os.path.join(current_directory, 'discos_test', filename)
    # Si el directorio no existe, crearlo
    directory = os.path.dirname(full_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Crear o sobrescribir el archivo binario con el tamaño especificado lleno de ceros
    with open(full_path, "wb") as file:
        file.write(b'\0' * total_size_bytes)

    print(f"** Disco creado con éxito en {full_path} con tamaño de {size}{unit}.")
    
    example = MBR(params)
    
    # Abrir el archivo binario y escribir el registro de MBR
    with open(full_path, "rb+") as file:
        file.seek(0)
        file.write(example.pack())