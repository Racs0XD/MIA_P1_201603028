# Importamos las librerías necesarias.
import os
import struct
from Estructuras.FILE_BLOCK import FileBlock
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.INODE import Inode
from Estructuras.SUPER_BLOCK import Superblock
from Admin_Usuario_Grupo.GESTOR_USER_GROUP import parse_users

# Función para eliminar un usuario.
def rmusr(parametros, particiones_montadas,id):   
    print("=================================================")
    print("===================== RMUSR =====================")
    print("============= Eliminando un usuario =============")
    print("=================================================")
    if id == None:
        print("Error: Se requiere del id.")
        return
    try: 
        user = parametros['user'].replace(' ', '')
    except:
        print("Error: Se requiere el nombre de el usuario.")
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
        print(f"Error: El archivo {full_path} no existe.") # Indica que el archivo de la partición no existe si no se pudo encontrar
        return
    with open(full_path, "rb+") as file: # Abre el archivo de la partición
        file.seek(inicio)
        superblock = Superblock.unpack(file.read(Superblock.SIZE)) # Lee el super bloque
        file.seek(superblock.s_inode_start)
        inodo = Inode.unpack(file.read(Inode.SIZE)) # Lee el primer inodo
        siguiente = inodo.i_block[0]
        file.seek(siguiente)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE)) # Lee el primer bloque de carpeta
        siguiente = folder.b_content[0].b_inodo
        file.seek(siguiente)
        ubicacion_inodo_users = siguiente
        inodo = Inode.unpack(file.read(Inode.SIZE)) # Lee el inodo correspondiente a la carpeta users
        primerbloque = -1
        cont = 0
        texto = ""
        for i,item in enumerate(inodo.i_block[:12]): # Itera sobre los primeros 12 bloques de la carpeta users
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
        indice_a_borrar = (primerbloque- superblock.s_block_start)//64   
        grupos = parse_users(texto)

        group_exists = False  # Se asume inicialmente que el grupo no existe
        bandera = False
        for n in grupos:
            if user in n:
                bandera = True
                break
        if bandera == False:
            print(f"Error: El usuario no existe.") # Indica que el usuario no existe si no se encontró un grupo que lo incluya
            return
        arreglo = texto.split('\n')
        lineas = []
        for i,n in enumerate(arreglo): # Recorre todas las líneas de texto correspondientes a usuarios
            if n == '':
                continue
            linea = n.split(',')
            if linea[1] == 'U' and linea[3] == user:
                linea[0] = '0' # Para desactivar al usuario, se modifica su tipo de usuario a '0'
            lineas.append(','.join(linea))
            #print(lineas)
        texto = '\n'.join(lineas)
        texto+='\n'
        #print(texto)
        #print(texto.split('\n'))
        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
        #print(bitmap)
                    
        if fileblocks<=12:
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            #print(bitmap)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            #print(a)
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            for i,n in enumerate(chunks): # Escribe en los bloques de datos correspondientes
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
            # Reescribe el inodo
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())
            # Reescribe el bitmap de bloques
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            #print(a)
            return