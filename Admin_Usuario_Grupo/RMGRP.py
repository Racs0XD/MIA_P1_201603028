# Importamos las librerías necesarias.
import os
import struct
from Estructuras.FILE_BLOCK import FileBlock
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.INODE import Inode
from Estructuras.SUPER_BLOCK import Superblock
from Admin_Usuario_Grupo.GESTOR_USER_GROUP import extract_active_groups

# Función para eliminar un grupo.
def rmgrp(parametros, particiones_montadas, id):
    print("=================================================")
    print("===================== RMGRP =====================")
    print("============== Eliminando un grupo ==============")
    print("=================================================")
    if id == None:
        print("Error: Se requiere del id.")
        return
    try: 
        group = parametros['name'].replace(' ', '')
    except:
        print("Error: Se requiere el nombre de el grupo.")
        return
    
    # Busca la partición con el id dado.
    partition = None
    for partition_dict in particiones_montadas:
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
    full_path = path
    if not os.path.exists(full_path):
        print(f"Error: el archivo {full_path} no existe.")
        return

    with open(full_path, "rb+") as file:
        # Se busca el superbloque de la partición.
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        
        # Se busca el inodo de la carpeta "users".
        file.seek(superblock.s_inode_start)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        siguiente = inodo.i_block[0]
        file.seek(siguiente)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        siguiente = folder.b_content[0].b_inodo
        file.seek(siguiente)
        ubicacion_inodo_users = siguiente
        
        # Se busca el bloque donde está almacenado el archivo "groups.txt".
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

        # Se busca el índice del bloque donde se encuentra el archivo "groups.txt".
        indice_a_borrar = (primerbloque- superblock.s_block_start)//64   
        grupos = extract_active_groups(texto)
        group_exists = False  # Se asume inicialmente que el grupo no existe.
        for n in grupos:
            # Se busca el grupo en la lista actual.
            if n['groupname'] == group:
                group_exists = True
                break

        if group_exists==False:
            print(f"Error: el grupo {group} no existe.")
            return

        arreglo = texto.split('\n')
        lineas = []
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
        # Se calculan los bloques necesarios para almacenar el archivo "groups.txt".
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1

        # Se lee el bitmap de bloques para encontrar espacio libre.
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')

        # Se verifica si se pueden usar los primeros 12 bloques del inodo.
        if fileblocks<=12:
            # Se actualiza el bitmap.
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            
            # Se busca el primer bloque libre.
            index = bitmap.find('0'*fileblocks)
            
            # Se actualiza el bitmap y se marca los bloques como usados.
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]

            # Se escribe cada bloque del archivo "groups.txt".
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())

            # Se reescribe el inodo de la carpeta "users".
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())

            # Se actualiza el bitmap de bloques.
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return