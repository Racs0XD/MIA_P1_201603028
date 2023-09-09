# Importamos las librerías necesarias.
import os
import struct
from Estructuras.FILE_BLOCK import FileBlock
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.INODE import Inode
from Estructuras.SUPER_BLOCK import Superblock
from Admin_Usuario_Grupo.GESTOR_USER_GROUP import extract_active_groups

# Función para eliminar un grupo.
def rmgrp(params, mounted_partitions, id):
    print("================== RMGRP ==================")
    if id == None:
        print("Error: Se requiere del id.")
        return
    try: 
        group = params['name']
    except:
        print("Error: Se requiere el nombre de el grupo.")
        return
    
    # Busca la partición con el id dado.
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
            
    if not partition:
        print(f"Error: La partición con el id: {id} no existe.")
        return
    
    # Obtiene los detalles de la partición.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    full_path= path
    if not os.path.exists(full_path):
        print(f"Error: El archivo en la dirección {full_path} no existe.")
        return
    
    # Lee el contenido del bloque asociado a los grupos y obtiene su ubicación en el disco.
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
        
        # Lee los bloques asociados al primer inodo de la carpeta usuarios.
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                
                # Lee el contenido del bloque.
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
                
        # Calcula el bloque necesario para contener el contenido de los grupos.
        indice_a_borrar = (primerbloque - superblock.s_block_start) // 64   
        
        # Parsea los grupos en el contenido de la carpeta usuarios.
        grupos = extract_active_groups(texto)
        group_exists = False
        
        # Verifica si el grupo a eliminar existe.
        for n in grupos:
            if n['groupname'] == group:
                group_exists = True
                break

        if group_exists==False:
            print(f"Error: El grupo {group} no existe.")
            return
        
        arreglo = texto.split('\n')
        lineas = []
        
        # Elimina el grupo especificado en los registros del disco.
        for i,n in enumerate(arreglo):
            if n == '':
                continue
            linea = n.split(',')
            if linea[1] == 'G' and linea[2] == group:
                linea[0] = '0'
            lineas.append(','.join(linea))
        texto = '\n'.join(lineas)
        texto+='\n'

        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1
        
        # Obtiene el mapa de bits de bloques y busca su primer aparición de la cantidad de bloques necesarios.
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
                    
        if fileblocks<=12:
            # Define el nuevo mapa de bits que indica los bloques ocupados.
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            
            # Divide el texto en chunks.
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            
            # Escribe los nuevos bloques en el disco.
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
                
            # Actualiza el inodo.
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())
            
            # Actualiza el mapa de bits.
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return