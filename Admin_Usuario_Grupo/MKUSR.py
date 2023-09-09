# Importamos las librerías necesarias.
import os
import struct
from Estructuras.FILE_BLOCK import FileBlock
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.INODE import Inode
from Estructuras.SUPER_BLOCK import Superblock
from Admin_Usuario_Grupo.GESTOR_USER_GROUP import extract_active_groups, parse_users, get_group_id

# Función para crear un nuevo usuario.
def mkusr(params, mounted_partitions, id):
    print("================== MKUSR ==================")
    if id == None:
        print("Error: Se requiere del id.")
        return
    try: 
        user = params['user']
        password = params['pass']
        group = params['grp']
    except:
        print("Error: Se requieren el usuario, la contraseña y el grupo.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: La partición con id {id} no existe.")
        return
    # Obtenemos los detalles de la partición.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    full_path = path
    if not os.path.exists(full_path):
        print(f"Error: El archivo {full_path} no existe.")
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
        grupos = parse_users(texto)
        group_exists = False  # Inicialmente, asumimos que el usuario no existe aún
        for n in grupos:
            # Comprobamos si el usuario ya existe en este objeto
            if user in n:
                print("Error: El usuario ya existe.")
                return
        grupos2 = extract_active_groups(texto)
        group_exists2 = False  # Inicialmente, asumimos que el grupo no existe aún
        for n2 in grupos2:
            # Comprobamos si el grupo ya existe en este objeto
            if n2['groupname'] == group:
                group_exists2 = True
                break
        if group_exists2==False:
            print(f"Error: El grupo {group} no existe.")
            return
        
        #print("ESTE ES EL USUARIO QUE SE VA A CREAR")
        id = get_group_id(group,grupos2 )
        #texto+='2,G,usuarios\n2,U,usuarios,user1,usuario\n'
        texto += f'{id},U,{group},{user},{password}\n'
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
                    
        if fileblocks<=12:
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
            # Reescribimos el inodo.
            file.seek(siguiente)
            file.write(inodo.pack())
            # Reescribimos el mapa de bits.
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return