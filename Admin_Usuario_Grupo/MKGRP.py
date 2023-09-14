# Importamos las librerías necesarias.
import os
import struct
from Estructuras.SUPER_BLOCK import Superblock
from Estructuras.INODE import Inode
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.FILE_BLOCK import FileBlock
from Admin_Usuario_Grupo.GESTOR_USER_GROUP import extract_active_groups

# Función para crear un nuevo grupo
def mkgrp(parametros, particiones_montadas, id):
    print("===================== MKGRP =====================")
    print("============ Creando un nuevo grupo =============")
    print("=================================================")
    if id == None:
        print("Error: Se requiere del id.")
        return
    try: 
        group = parametros['name'].replace(' ', '')
    except:
        print("Error: Se requiere el nombre del grupo.")
        return
    
    partition = None
    for partition_dict in particiones_montadas:
        if id in partition_dict:
            partition = partition_dict[id]
            break
            
    if not partition:
        print(f"Error: La partición con el id: {id} no existe.")
        return
    
    # Obtenemos los detalles de la partición.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    full_path = path
    
     # Si el archivo del disco no existe, se devuelve un error.
    if not os.path.exists(full_path):
        print(f"Error: El archivo {full_path} no existe.")
        return

    # Se lee el superbloque e inode para encontrar la ubicación del bloque de grupo
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        file.seek(superblock.s_inode_start)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        siguiente = inodo.i_block[0]
        file.seek(siguiente)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        siguiente = folder.b_content[0].b_inodo
        file.seek(siguiente)
        ubicacion_inodo_users = siguiente
        inodo = Inode.unpack(file.read(Inode.SIZE))
        primerbloque = -1
        cont = 0
        texto = ""

        # Se lee el contenido de los bloques de archivo para obtener la información de los grupos
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')

        # Se extraen los grupos activos del texto
        indice_a_borrar = (primerbloque- superblock.s_block_start)//64   
        grupos = extract_active_groups(texto)
        group_exists = False  # Inicialmente, asumimos que el grupo no existe

        # Se verifica si el grupo existe
        for n in grupos:
            if n['groupname'] == group:
                group_exists = True
                break

        # Si el grupo ya existe, se devuelve un error.
        if group_exists==True:
            print(f"Error: El grupo {group} ya existe.")
            return

        # Se muestra en pantalla el grupo que se va a crear
        print("ESTE ES EL GRUPO QUE SE VA A CREAR")
        print(group)
        print(grupos)

        # Se determina el siguiente ID disponible para el nuevo grupo
        max_id = max(g['id'] for g in grupos)
        next_id = max_id + 1

        # Se agrega el nuevo grupo al contenido del bloque de archivo
        texto += f'{next_id},G,{group}\n'

        # Se establece la cantidad de bloques necesarios para el contenido del archivo
        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1

        # Se actualiza el bitmap y se asignan los bloques necesarios al contenido del archivo
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
                    
        if fileblocks<=12:
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]

            # Se escribe el contenido en los bloques de archivo necesarios
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
            
            # Se actualiza el inode y el bitmap
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return