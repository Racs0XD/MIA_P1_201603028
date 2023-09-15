# Importar módulos necesarios
import os
from Estructuras.SUPER_BLOCK import Superblock
from Estructuras.INODE import Inode
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.FILE_BLOCK import FileBlock
from Admin_Usuario_Grupo.GESTOR_USER_GROUP import parse_users, get_user_if_authenticated

# Función para iniciar sesión en el sistema de archivos EXT2.
def login(parametros, particiones_montadas):
    print("=================================================")
    print("============== Bienvenido al Login ==============")
    print("=================================================")
    # Verificar que existan los parámetros de usuario y contraseña
    try:
        user = parametros['user'].replace(' ', '')
        password = parametros['pass'].replace(' ', '')
        id = parametros['id'].replace(' ', '')
        print(particiones_montadas)
    except:
        print("Error: se requieren el usuario y la contraseña.")
        return None, None

    # Buscar la partición montada por su identificador
    partition = None
    for partition_dict in particiones_montadas:
        if id in partition_dict:
            partition = partition_dict[id]
            break

    if not partition:
        print(f"Error: La partición con id '{id}' no existe.")
        return

    # Obtener detalles de la partición montada
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    full_path= path

    # Verificar que exista el archivo de la partición
    if not os.path.exists(full_path):
        print(f"Error: El archivo en la ruta {full_path} no existe.")
        return

    # Leer los datos del archivo de la partición
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
        texto = ""
        for n in inodo.i_block:
            if n != -1:
                siguiente = n
                file.seek(siguiente)
                fileblock = FileBlock.unpack(file.read(FileBlock.SIZE))
                texto += fileblock.b_content.rstrip('\x00')

    # Autenticar al usuario y realizar el inicio de sesión
    usuarios = parse_users(texto)
    users = get_user_if_authenticated(usuarios, user, password)
    print("=================================================")
    print("Usuario autenticado: ")
    print(users)
    print("=================================================")
    return users,id
