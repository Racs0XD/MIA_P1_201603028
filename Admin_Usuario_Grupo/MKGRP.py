# Importamos las librerías necesarias.
import os
import struct
from Estructuras.SUPER_BLOCK import Superblock
from Estructuras.INODE import Inode
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.FILE_BLOCK import FileBlock
from Admin_Usuario_Grupo.GESTOR_USER_GROUP import extract_active_groups

# Función para crear un nuevo grupo
def mkgrp(params, mounted_partitions, id):
    print("================== MKGRP ==================")
    if id == None:
        print("Error: Se requiere del id.")
        return
    try: 
        group = params['name']
    except:
        print("Error: Se requiere el nombre del grupo.")
        return
    
    partition = None
    for partition_dict in mounted_partitions:
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
    if not os.path.exists(full_path):
        print(f"Error: El archivo en la ruta {full_path} no existe.")
        return
        
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
        inodo = Inode.unpack(file.read(Inode.SIZE))
        primerbloque = -1
        cont = 0
        texto = ""
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
        indice_a_borrar = (primerbloque- superblock.s_block_start)//64   
        grupos = extract_active_groups(texto)
       
        group_exists = False  # Inicialmente, asumimos que el grupo no existe aún
       
        for n in grupos:
            # Comprobamos si el grupo ya existe en este objeto
            if n['groupname'] == group:
                group_exists = True
                break

        if group_exists==True:
            print(f"Error: El grupo {group} ya existe.")
            return

        #print("ESTE ES EL GRUPO QUE SE VA A CREAR")
        #print(group)
        #print(grupos)
        
        max_id = max(g['id'] for g in grupos)
        # El siguiente ID disponible será max_id + 1
        next_id = max_id + 1
    
        texto += f'{next_id},G,{group}\n'
        
        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1
        
        # Obtenemos el mapa de bits de bloques y buscamos su primer aparición de la cantidad de bloques requerida
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
        
        if fileblocks <= 12:
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            #print(bitmap)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            #print(a)
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
            
            # Reescribimos el inodo
            file.seek(siguiente)
            file.write(inodo.pack())
            # Reescribimos el mapa de bits
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return