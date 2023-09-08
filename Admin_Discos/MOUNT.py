# Importando las librerías necesarias
import os
import struct
from Discos.MBR import MBR
from Discos.PARTITION import Partition

# Define la función para montar una partición
def mount(params, mounted_partitions):
    # Obtiene la ruta del archivo de disco
    size_param = params.get('path').replace('"', '').replace('.dsk ', '.dsk')
    # Obtiene el directorio actual
    # Obtiene la ruta completa del archivo
    full_path = size_param
    # Verifica si la ruta existe y si es así, abre el archivo y lee las particiones en el MBR, de lo contrario retorna un error
    if not os.path.exists(full_path):
        print(f"Error: El archivo en la ruta {full_path} no existe.")
        return
    partitions = []
    with open(full_path, "rb+") as file:
        for i in range(4):
            # Lee la partición en la posición correspondiente y la añade a la lista de particiones
            file.seek(struct.calcsize(MBR.FORMAT)+(i*Partition.SIZE))
            data = file.read(Partition.SIZE)
            particion_temporal = Partition.unpack(data)
            partitions.append(particion_temporal)

    # Obtiene el nombre de la partición a montar
    name = params.get('name').replace('"', '')
    # Verifica si la partición existe en la lista de particiones, si no existe, retorna un error
    bandera = False
    index = -50
    for i,item in enumerate(partitions):
        if item.name == name:
            bandera = True
            index = i
    if bandera == False:
        print(f"Error: La partición {name} no existe.")
        return
    
    # Crea un ID único para la partición y lo añade a la lista de particiones montadas
    mycarne = 53
    diskname = size_param.split('/')[-1]
    diskname = diskname.split('.')[0]
    # El ID tiene la siguiente estructura: *Últimos dos dígitos del Carnet + Número Partición + NombreDisco 
    # Ejemplo: para el carnet -> 201404106 Id´s -> 061Disco1, 062Disco1, 061Disco2, 062Disco2
    id = f'{mycarne}{(index+1)}{diskname}'
    # Se añade un diccionario con la información de la partición a la lista de particiones montadas
    mounted_partitions.append({
        id: {
            'path':size_param, 
            'partition': partitions[index],
            'name': name,
            'index': index,
            'id': id,
            'inicio': partitions[index].byte_inicio,
            'size': partitions[index].actual_size,
        }
    })

