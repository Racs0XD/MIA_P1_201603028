import os
import struct
from Admin_Usuario_Grupo.GESTOR_USER_GROUP import load_users_from_content, parse_users, get_user_if_authenticated, get_id_by_group, extract_active_groups,get_group_id
from Sistema_Archivos.EXT2 import Superblock, Inode, FolderBlock, FileBlock, block

# Función para formatear una partición
def mkfs(params, mounted_partitions, users):
    # Obtener el tipo y el id de los parámetros
    tipo = params.get('type', 'full').lower().replace(' ', '')
    id = params.get('id', None).replace(' ', '')

    # Verificar si el id existe en las particiones montadas
    # y recuperar los detalles de la partición
    particion = None
    for particion_dict in mounted_partitions:
        if id in particion_dict:
            particion = particion_dict[id]
            break

    if not particion:
        print(f"Error: La partición con el {id} no existe.")
        return

    path = particion['path']
    inicio = particion['inicio']
    size = particion['size']

    # Paso 3: formatear según el tipo
    if tipo == 'full':
        # Crear un superbloque y reducir la cuenta de inodos y bloques libres
        superblock = Superblock(inicio, size)
        superblock.s_free_inodes_count -= 1
        # para el superbloque y el bitmap de inodos
        superblock.s_free_blocks_count -= 1 
        # Obtener la ruta completa del archivo y verificar si existe
        full_path = path
        if not os.path.exists(full_path):
            print(f"Error: El archivo en la ruta {full_path} no existe.")
            return

        with open(full_path, "rb+") as file:
            # Crear un bitmap de inodos y otro de bloques
            bitmapinodos = ['0']*superblock.s_inodes_count
            bitmapbloques = ['0']*superblock.s_blocks_count
            
            # Crear un inodo 0 y un bloque 0
            i1 = Inode()
            i1.i_type = '0'
            i1.i_block[0] = superblock.s_block_start
            b1 = FolderBlock()
            b1.b_content[0].b_inodo = superblock.s_inode_start+Inode.SIZE
            b1.b_content[0].b_name = 'users.txt'
            bitmapbloques[0] = '1'
            bitmapinodos[0] = '1'

            # Crear un inodo 1 y un bloque 1
            i2 = Inode()
            i2.i_type = '1'
            i2.i_block[0] = superblock.s_block_start+block.SIZE
            b2 = FileBlock()
            b2.b_content = '1,G,root\n1,U,root,root,123\n'
            bitmapbloques[1] = '1'
            bitmapinodos[1] = '1'
            
            # Escribir el superbloque, los bitmaps, los inodos y los bloques en el archivo
            file.seek(inicio)
            file.write(superblock.pack())
            for i in range(superblock.s_inodes_count):
                file.write(bitmapinodos[i].encode('utf-8'))
            for i in range(superblock.s_blocks_count):
                file.write(bitmapbloques[i].encode('utf-8'))
            file.seek(superblock.s_inode_start)
            file.write(i1.pack())
            file.write(i2.pack())
            file.seek(superblock.s_block_start)
            file.write(b1.pack())
            file.write(b2.pack())

        print(f"La partición {id} se ha formateado correctamente.")
                   
#Funcion para crear un nuevo usuario
def makeuser(params, mounted_partitions,id):
    print("ESTE ES EL MAKEUSER*************************************************")
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        user = params['user']
        password = params['pass']
        group = params['grp']
    except:
        print("Error: The user, password and group are required.")
        return
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
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
        group_exists = False  # Initially, we assume the group does not exist
        
        for n in grupos:
            # Check if the group exists in current item
            if user in n:
                print("Error: The user already exists.*********************************************************************")
                return
        #
        grupos22 = extract_active_groups(texto)
        group_exists2 = False  # Initially, we assume the group does not exist
        for n2 in grupos22:
            # Check if the group exists in current item
            if n2['groupname'] == group:
                group_exists2 = True
                break
        if group_exists2==False:
            print(f"Error: The group {group} doesn't exists.")
            return
        
        #print("ESTE ES EL USUARIO QUE SE VA A CREAR")
        id = get_group_id(group,grupos22 )
        #texto+='2,G,usuarios\n2,U,usuarios,user1,usuario\n'
        texto += f'{id},U,{group},{user},{password}\n'
        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1
            
        # Se obtiene el bitmap de bloques y se busca su primer aparición de la cantidad de bloques necesarios
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
            # Se reescribe el inodo
            file.seek(siguiente)
            file.write(inodo.pack())
            # Se reescribe el bitmap
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return
#Funcion para crear un nuevo grupo
def makegroup(params, mounted_partitions,id):
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        group = params['name']
    except:
        print("Error: The group is required.")
        return
    
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
            
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
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
       
        group_exists = False  # Initially, we assume the group does not exist
       
        for n in grupos:
            # Check if the group exists in current item
            if n['groupname'] == group:
                group_exists = True
                break

        if group_exists==True:
            print(f"Error: The group {group} already exist.")
            return

        #print("ESTE ES EL GRUPO QUE SE VA A CREAR")
        #print(group)
        #print(grupos)
        
        max_id = max(g['id'] for g in grupos)
        # The next available ID will be max_id + 1
        next_id = max_id + 1
    
        texto += f'{next_id},G,{group}\n'
        
        length = len(texto)
        fileblocks = length//64
        if length%64 != 0:
            fileblocks += 1
        
        # Se obtiene el bitmap de bloques y se busca su primer aparición de la cantidad de bloques necesarios
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
            
            # Se reescribe el inodo
            file.seek(siguiente)
            file.write(inodo.pack())
            # Se reescribe el bitmap
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return


#Función para eliminar un grupo
def remgroup(params, mounted_partitions,id):
    print("ESTE ES EL REMGROUP*************************************************")
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        group = params['name']
    except:
        print("Error: The user, password and group are required.")
        return
    
    # Busca la partición con el id dado
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
            
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    
    #Lee el contenido del bloque asociado a los grupos y obtiene su ubicación en el disco
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
        
        # Lee los bloques asociados al primer inodo de la carpeta usuarios
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                
                # Lee el contenido del bloque
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
                
        # Calcula el bloque necesario para contener el contenido de los grupos
        indice_a_borrar = (primerbloque - superblock.s_block_start) // 64   
        
        # Parsea los grupos en el contenido de la carpeta usuarios
        grupos = extract_active_groups(texto)
        group_exists = False
        
        # Verifica si el grupo a eliminar existe
        for n in grupos:
            if n['groupname'] == group:
                group_exists = True
                break

        if group_exists==False:
            print(f"Error: The group {group} doesn't exist.")
            return
        
        arreglo = texto.split('\n')
        lineas = []
        
        # Elimina el grupo especificado en los registros del disco
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
        
        # Se obtiene el bitmap de bloques y se busca su primer aparición de la cantidad de bloques necesarios
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
                    
        if fileblocks<=12:
            # Define el nuevo bitmap que indica los bloques ocupados
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            
            # Divide el texto en chunks
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            
            # Escribe los nuevos bloques en el disco
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
                
            # Actualiza el inodo
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())
            
            # Actualiza el bitmap
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return

        
#Función para eliminar un usuario
def remuser(params, mounted_partitions,id):   
    print("ESTE ES EL REMOVE USER*************************************************")
    if id == None:
        print("Error: The id is required.")
        return
    try: 
        user = params['user']
    except:
        print("Error: The user is required required.")
        return
    
    # Busca la partición con el id dado
    partition = None
    for partition_dict in mounted_partitions:
        if id in partition_dict:
            partition = partition_dict[id]
            break
            
    if not partition:
        print(f"Error: The partition with id {id} does not exist.")
        return
    
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    filename = path
    current_directory = os.getcwd()
    full_path= f'{current_directory}/discos_test{filename}'
    if not os.path.exists(full_path):
        print(f"Error: The file {full_path} does not exist.")
        return
    
    with open(full_path, "rb+") as file:
        # Leo bloques de la partición y Ubicación en Disco del archivo users.txt
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
        
        # Leo los bloques asociados al inodo 1
        for i,item in enumerate(inodo.i_block[:12]):
            if item != -1 and i == 0:
                primerbloque = item
            if item != -1:
                cont = i+1
                
                # Leo el bloque asociado al item en curso
                siguiente = item
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')
                
        # Calcula el bloque necesario para contener el contenido del archivo users.txt
        indice_a_borrar = (primerbloque - superblock.s_block_start) // 64   
        
        # Parsea los registros de usuarios en el contenido del archivo users.txt
        grupos = parse_users(texto)

        # Verifica si el usuario a eliminar existe
        bandera = False
        for n in grupos:
            if n['username'] == user:
                bandera = True
                break
        if bandera == False:
            print(f"Error: The user doesn´t exists.")
            return
        
        arreglo = texto.split('\n')
        lineas = []
        
        # Elimina del contenido del archivo users.txt el registro de usuario especificado
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
        
        # Se obtiene el bitmap de bloques y se busca su primer aparición de la cantidad de bloques necesarios
        bitmap_bloques_inicio = superblock.s_bm_block_start
        cantidad_bloques = superblock.s_blocks_count
        FORMAT = f'{cantidad_bloques}s'
        SIZE = struct.calcsize(FORMAT)
        file.seek(bitmap_bloques_inicio)
        bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))
        bitmap=bitmap_bloques[0].decode('utf-8')
                    
        if fileblocks<=12:
            # Define el nuevo bitmap que indica los bloques ocupados
            bitmap = bitmap[:indice_a_borrar] + '0'*cont + bitmap[indice_a_borrar+cont:]
            index = bitmap.find('0'*fileblocks)
            a = bitmap[:index] + '1'*fileblocks + bitmap[index+fileblocks:]
            
            # Divide el texto en chunks
            chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
            
            # Escribe los nuevos bloques en el disco
            for i,n in enumerate(chunks):
                new_fileblock = FileBlock()
                new_fileblock.b_content = n
                inodo.i_block[i] = primerbloque+i*64
                file.seek(primerbloque+i*64)
                file.write(new_fileblock.pack())
                
            # Actualiza el inodo
            file.seek(ubicacion_inodo_users)
            file.write(inodo.pack())
            
            # Actualiza el bitmap
            file.seek(bitmap_bloques_inicio)
            file.write(a.encode('utf-8'))
            return