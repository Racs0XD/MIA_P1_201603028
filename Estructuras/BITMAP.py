import os
import math
import struct
from Estructuras.SUPER_BLOCK import Superblock

# Método para obtener el tamaño en bytes de la estructura empaquetada
bytesMapD = []
bytesMap = 0

def bitMap(parametros, particiones_montadas, id):
    partition = None
    # Buscar la partición con el ID indicado en el diccionario de particiones montadas.
    for partition_dict in particiones_montadas:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: La partición con ID {id} no existe.")
        return
    
    # Obtener información de la partición.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    full_path= path
    
    # Verificar que el archivo de la partición exista.
    if not os.path.exists(full_path):
        print(f"Error: El archivo en la ruta no existe {full_path} no existe.")
        return
    
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        
        # Ver los bitmaps de inodos y bloques.
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap_bloques=bitmap_bloques[0].decode('utf-8')
        bitmap_inodos_inicio = superblock.s_bm_inode_start
        cantidad_inodos = superblock.s_inodes_count
        FORMAT = f'{cantidad_inodos}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_inodos_inicio)
        bitmap_inodos = struct.unpack(FORMAT, file.read(SIZE))
        bitmap_inodos=bitmap_inodos[0].decode('utf-8')
        
        # Generar texto con la información de los bitmaps
        texto =f'\nInstrucción: {parametros.upper()}'
        texto +="\n================================================="
        texto +="\n===================  BITMAPS ===================="
        texto +="\n================================================="
        texto +="\n===================  bloques ===================="
        texto +="\n================================================="
        texto +="\n"+bitmap_bloques
        texto +="\n================================================="
        texto +="\n===================  inodos ====================="
        texto +="\n================================================="
        texto +="\n"+bitmap_inodos
        texto +="\n================================================="
        texto +="\n============= FIN ESTADO BITMAPS ================"
        texto +="\n================================================="
        

        # Generar un diagrama DOT con el estado de los bitmaps.
        global bytesMap
        inodo_dot = genDot(parametros,bitmap_inodos, "inodo", bytesMap)
        bloque_dot = genDot(parametros,bitmap_bloques, "bloque", bytesMap)

        # Agregar el diagrama DOT al historial de mapas de bytes.
        global bytesMapD
        bytesMapD.append((inodo_dot, bloque_dot))
        bytesMap += 1



def genDot(parametros, bitmap, label, contador):
    length = len(bitmap)
    rows = math.ceil(math.sqrt(length))
    
    # Dividir el bitmap en filas
    split_bitmap = [bitmap[i:i+rows] for i in range(0, length, rows)]
    
    # Unir las filas divididas con etiquetas de salto de línea (<br>)
    formatted_bitmap = '\\n'.join(split_bitmap)
    
    # Agregar el bitmap formateado a la etiqueta del nodo.
    dot_string = f'{label}_{contador} [shape=box,  label="{parametros}\n{formatted_bitmap}"];\n'
    
    return dot_string