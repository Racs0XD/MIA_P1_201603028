import os
from Estructuras.SUPER_BLOCK import Superblock
from Estructuras.INODE import Inode
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.FILE_BLOCK import FileBlock

# Función para formatear una partición
def mkfs(params, mounted_partitions, users):
    # Obtener el tipo y el id de los parámetros
    tipo = params.get('type', 'full').lower().replace(' ', '')
    id = params.get('id', None).replace(' ', '')
    fs = params.get('fs', '2fs').lower().replace(' ', '') # Valor por defecto 2fs (EXT2)

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
        if fs == '2fs':
            formato = "EXT2"
            superblock = Superblock(inicio, size, 0)  # Formato EXT2
        elif fs == '3fs':
            formato = "EXT3"
            superblock = Superblock(inicio, size, 1)  # Formato EXT3
        else:
            print("Error: el valor para el argumento fs debe ser 2fs o 3fs (por defecto se crea en formato EXT2)")
            return
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
            i2.i_block[0] = superblock.s_block_start+FileBlock.SIZE
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

        print(f"La partición {id} se ha formateado correctamente en formato {formato}.")