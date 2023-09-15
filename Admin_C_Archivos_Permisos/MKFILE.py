import os
import struct
from Estructuras.SUPER_BLOCK import Superblock
from Estructuras.INODE import Inode
from Estructuras.FILE_BLOCK import FileBlock
from Estructuras.FOLDER_BLOCK import FolderBlock
from Admin_C_Archivos_Permisos.GESTOR_FILES import get_file_content, busca, busca_espacio_libre


def mkfile(parametros, particiones_montadas, id, usuario_actual):
    print("=================================================")
    print("==================== MKFILE =====================")
    print("================ Crear Archivo ==================")
    print("=================================================")
    
    UID = usuario_actual['id']
    GID = UID
    # Verificamos que se hayan ingresado todos los parametros necesarios
    if id == None:
        print("Error: Se requiere el ID.")
        return
    try: 
        insidepath = parametros['path']
        r = parametros.get('r', '/')
        archivosize = parametros.get('size', 0)
        archivocont = parametros.get('cont', '')
        if archivocont != '':
            archivocont = get_file_content(archivocont)
    except:
        print("Error: Se requiere el usuario, la contraseña y el grupo.")
        return
    partition = None
    # Buscamos la particion especificada en las particiones montadas
    for partition_dict in particiones_montadas:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: La partición con ID {id} no existe.")
        return
    # Obtenemos los detalles de la particion
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    full_path = path
    if not os.path.exists(full_path):
        print(f"Error: El archivo en la ruta {full_path} no existe.")
        return
    # Abrimos el archivo de la particion en modo lectura-escritura binario
    with open(full_path, "rb+") as file:
        file.seek(inicio)
        # Obtenemos el superbloque de la particion
        superblock = Superblock.unpack(file.read(Superblock.SIZE))
        # Separamos la direccion en una lista de subdirectorios
        lista_direcciones = insidepath.split('/')[1:]
        PI = superblock.s_inode_start
        newI = -1
        for i, n in enumerate(lista_direcciones):
            esta, v = busca(file, PI, 0, n)
            if esta:
                PI = v
            else:
                if r != '-r':
                    print(f'El archivo {insidepath} no existe.')
                    return
                newI = i
                break
        if newI == -1:
            print(f'El archivo {insidepath} ya existe.')
            return
        else:
            nueva_lista_dirercciones = lista_direcciones[newI:]
            inodo_inicio = superblock.s_inode_start
            inodo_size = Inode.SIZE
            indice = (PI - inodo_inicio) // inodo_size
            folder_a_escribir = nueva_lista_dirercciones[0]
            # Buscamos el primer slot libre en el inodo actual
            file.seek(PI)
            inodo_actual = Inode.unpack(file.read(Inode.SIZE))
            indice = -1
            for i, n in enumerate(inodo_actual.i_block):
                if n == -1:
                    indice = i
                    break
            if indice != -1 and i<=12:
                # Obtenemos los bitmaps de bloques e inodos
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
                # Buscamos un espacio libre para el bloque y el inodo nuevos
                a,b,c,d = busca_espacio_libre(file, PI, 0)
                if c == 0:
                    # Creamos un nuevo bloque de carpeta y actualizamos el inodo actual con la direccion del nuevo bloque
                    index_bloque_inicial = bitmap_bloques.find('0')
                    bitmap_bloques=bitmap_bloques[:index_bloque_inicial] + '1' + bitmap_bloques[index_bloque_inicial+1:]
                    byte_nuevo_bloque = superblock.s_block_start + index_bloque_inicial*FileBlock.SIZE
                    file.seek(b)
                    inodo_presente = Inode.unpack(file.read(Inode.SIZE))
                    inodo_presente.i_block[d] = byte_nuevo_bloque
                    file.seek(b)
                    file.write(inodo_presente.pack())
                    
                    nuevo_bloque = FolderBlock()
                    index_nodo = bitmap_inodos.find('0')
                    bitmap_inodos=bitmap_inodos[:index_nodo] + '1' + bitmap_inodos[index_nodo+1:]
                    byte_nuevo_inodo2 = superblock.s_inode_start + index_nodo*Inode.SIZE
                    nuevo_bloque.b_content[0].b_name = folder_a_escribir
                    nuevo_bloque.b_content[0].b_inodo = byte_nuevo_inodo2
                    file.seek(byte_nuevo_bloque)
                    file.write(nuevo_bloque.pack())
                    # Creamos un nuevo inodo para el archivo
                    nuevo_inodo = Inode()
                    nuevo_inodo.i_uid = int(UID)
                    nuevo_inodo.I_gid = int(GID)    
                    nuevo_inodo.i_s = int(archivosize)
                    nuevo_inodo.i_perm = 664
                    if not folder_a_escribir.endswith('.txt'):
                        # Si es un archivo, creamos un nuevo bloque de archivo y actualizamos el nuevo inodo con la direccion del bloque
                        index_bloque = bitmap_bloques.find('0')
                        bitmap_bloques=bitmap_bloques[:index_bloque] + '1' + bitmap_bloques[index_bloque+1:]
                        byte_nuevo_bloque2 = superblock.s_block_start + index_bloque*FileBlock.SIZE
                        nuevo_inodo.i_block[0] = byte_nuevo_bloque2
                        file.seek(byte_nuevo_inodo2)
                        file.write(nuevo_inodo.pack())
                        nuevo_bloque = FileBlock()
                        file.seek(byte_nuevo_bloque2)
                        file.write(nuevo_bloque.pack())
                        # Actualizamos los bitmaps
                        file.seek(bitmap_bloques_inicio)
                        file.write(bitmap_bloques.encode('utf-8'))
                        file.seek(bitmap_inodos_inicio)
                        file.write(bitmap_inodos.encode('utf-8'))
                        dict = {'path':'/home'}
                    else:
                        # Si es una carpeta, marcamos el inodo como de tipo carpeta y actualizamos los bitmaps
                        nuevo_inodo.i_type = '1'
                        file.seek(byte_nuevo_inodo2)
                        file.write(nuevo_inodo.pack())
                        file.seek(bitmap_bloques_inicio)
                        file.write(bitmap_bloques.encode('utf-8'))
                        file.seek(bitmap_inodos_inicio)
                        file.write(bitmap_inodos.encode('utf-8'))
                        dict = {'path':'/home'}
                        # Ahora escribimos el contenido del archivo si es que archivocont no esta vacio
                        if archivocont!='':
                            length = len(archivocont)
                            fileblocks = length//64
                            if length%64 != 0:
                                fileblocks += 1
                            indice_bloque = bitmap_bloques.find('0'*fileblocks)
                            bitmap_bloques = bitmap_bloques[:indice_bloque] + '1'*fileblocks + bitmap_bloques[indice_bloque+fileblocks:]
                            if fileblocks<=12:
                                texto = archivocont 
                                chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
                                primerbloque = superblock.s_block_start + indice_bloque*FileBlock.SIZE
                                for i,n in enumerate(chunks):
                                    new_fileblock = FileBlock()
                                    new_fileblock.b_content = n
                                    nuevo_inodo.i_block[i] = primerbloque+i*64
                                    file.seek(primerbloque+i*64)
                                    file.write(new_fileblock.pack())
                                nuevo_inodo.i_s = fileblocks*64
                                file.seek(byte_nuevo_inodo2)
                                file.write(nuevo_inodo.pack())
                                file.seek(bitmap_bloques_inicio)
                                file.write(bitmap_bloques.encode('utf-8'))
                        return
                elif c == 1:
                    # Solo se necesita un inodo y un bloque de carpeta nuevos
                    # Creamos el nuevo inodo y el bloque de carpeta en los bitmaps
                    index_nodo = bitmap_inodos.find('0')
                    bitmap_inodos=bitmap_inodos[:index_nodo] + '1' + bitmap_inodos[index_nodo+1:]
                    byte_nuevo_inodo = superblock.s_inode_start + index_nodo*Inode.SIZE
                    file.seek(b)
                    bloque_actual = FolderBlock.unpack(file.read(FileBlock.SIZE))
                    bloque_actual.b_content[d].b_name = folder_a_escribir
                    bloque_actual.b_content[d].b_inodo = byte_nuevo_inodo
                    file.seek(b)
                    file.write(bloque_actual.pack())
                    # Creamos el nuevo inodo para el archivo
                    nuevo_inodo = Inode()
                    nuevo_inodo.i_uid = int(UID)
                    nuevo_inodo.I_gid = int(GID)
                    nuevo_inodo.i_s = int(archivosize)
                    nuevo_inodo.i_perm = 664
                    if not folder_a_escribir.endswith('.txt'):
                        # Si es un archivo, creamos un nuevo bloque de archivo y actualizamos el nuevo inodo con la direccion del bloque
                        index_bloque = bitmap_bloques.find('0')
                        bitmap_bloques=bitmap_bloques[:index_bloque] + '1' + bitmap_bloques[index_bloque+1:]
                        byte_nuevo_bloque = superblock.s_block_start + index_bloque*FileBlock.SIZE
                        nuevo_inodo.i_block[0] = byte_nuevo_bloque
                        file.seek(byte_nuevo_inodo)
                        file.write(nuevo_inodo.pack())
                        nuevo_bloque = FileBlock()
                        file.seek(byte_nuevo_bloque)
                        file.write(nuevo_bloque.pack())
                        # Actualizamos los bitmaps
                        file.seek(bitmap_bloques_inicio)
                        file.write(bitmap_bloques.encode('utf-8'))
                        file.seek(bitmap_inodos_inicio)
                        file.write(bitmap_inodos.encode('utf-8'))
                        dict = {'path':'/home'}
                    else:
                        # Si es una carpeta, marcamos el inodo como de tipo carpeta y actualizamos los bitmaps
                        nuevo_inodo.i_type = '1'
                        file.seek(byte_nuevo_inodo)
                        file.write(nuevo_inodo.pack())
                        file.seek(bitmap_bloques_inicio)
                        file.write(bitmap_bloques.encode('utf-8'))
                        file.seek(bitmap_inodos_inicio)
                        file.write(bitmap_inodos.encode('utf-8'))
                        dict = {'path':'/home'}
                        # Ahora escribimos el contenido del archivo si es que archivocont no esta vacio
                        if archivocont!='':
                            length = len(archivocont)
                            fileblocks = length//64
                            if length%64 != 0:
                                fileblocks += 1
                            indice_bloque = bitmap_bloques.find('0'*fileblocks)
                            bitmap_bloques = bitmap_bloques[:indice_bloque] + '1'*fileblocks + bitmap_bloques[indice_bloque+fileblocks:]
                            if fileblocks<=12:
                                texto = archivocont 
                                chunks = [texto[i:i+64] for i in range(0, len(texto), 64)]
                                primerbloque = superblock.s_block_start + indice_bloque*FileBlock.SIZE
                                for i,n in enumerate(chunks):
                                    new_fileblock = FileBlock()
                                    new_fileblock.b_content = n
                                    nuevo_inodo.i_block[i] = primerbloque+i*64
                                    file.seek(primerbloque+i*64)
                                    file.write(new_fileblock.pack())
                                nuevo_inodo.i_s = fileblocks*64
                                file.seek(byte_nuevo_inodo)
                                file.write(nuevo_inodo.pack())
                                file.seek(bitmap_bloques_inicio)
                                file.write(bitmap_bloques.encode('utf-8'))
                        return
    if newI != -1:    
        # Llamamos a mkfile de nuevo para completar la direccion necesaria
        mkfile(parametros,particiones_montadas,id, usuario_actual)