# Importamos las librerías necesarias.
import os
import struct
from Estructuras.FILE_BLOCK import FileBlock
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.INODE import Inode
from Estructuras.SUPER_BLOCK import Superblock
from Admin_Usuario_Grupo.GESTOR_USER_GROUP import parse_users

# Función para eliminar un usuario.
def rmusr(params, mounted_partitions,id):   
    print("================== RMUSR ==================")
    if id == None:
        print("Error: Se requiere del id.")
        return
    try: 
        user = params['user']
    except:
        print("Error: Se requiere el nombre de el usuario.")
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
    full_path = path
    if not os.path.exists(full_path):
        print(f"Error: El archivo en la ruta {full_path} no existe.")
        return
    
    with open(full_path, "rb+") as file:
        # Leo bloques de la partición y Ubicación en Disco del archivo users.txt.
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
        
        # Leo los bloques asociados al inodo 1.
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                
                # Leo el bloque asociado al item en curso.
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
                
        # Calcula el bloque necesario para contener el contenido del archivo users.txt.
        indice_a_borrar = (primerbloque - superblock.s_block_start) // 64   
        
        # Parsea los registros de usuarios en el contenido del archivo users.txt.
        grupos = parse_users(texto)

        # Verifica si el usuario a eliminar existe.
        bandera = False
        for n in grupos:
            if n['username'] == user:
                bandera = True
                break
        if bandera == False:
            print(f"Error: El usuario no existe.")
            return
        
        arreglo = texto.split('\n')
        lineas = []
        
        # Elimina del contenido del archivo users.txt el registro de usuario especificado.
        for i,n in enumerate(arreglo):
            if n == '':
                continue
            linea = n.split(',')
            if linea[1] == 'U' and linea[3] == user:
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