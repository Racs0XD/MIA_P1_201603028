# Importar módulos necesarios
import struct
import time


# Definir clase Inode
class Inode:
    FORMAT = 'i i i d d d c 15i i'                   # Formato de empaquetado de datos
    SIZE = struct.calcsize(FORMAT)                  # Tamaño en bytes de la estructura empaquetada

    def __init__(self):
        self.i_uid = 0                              # Usuario que creó el archivo
        self.I_gid = 0                              # Grupo del usuario que creó el archivo
        self.i_s = 0                                # Tamaño del archivo
        self.i_atime = time.time()                  # Hora en que se accedió al archivo
        self.i_ctime = time.time()                  # Hora en que se creó el archivo
        self.i_mtime = time.time()                  # Hora en que se modificó el archivo
        self.i_type = '0'                           # Tipo de archivo ('0' para archivo, '1' para carpeta)
        self.i_block = [-1] * 15                     # Bloques que contienen los datos del archivo
        self.i_perm = 0                             # Permisos de acceso al archivo
    
    # Método para convertir la estructura Inode a una cadena
    def __str__(self) -> str:
        return f"Inode: uid={self.i_uid}, gid={self.I_gid}, size={self.i_s}, atime={self.i_atime}, ctime={self.i_ctime}, mtime={self.i_mtime}, type={self.i_type}, FileBlock={self.i_block}, perm={self.i_perm}"
    
    # Método para empaquetar la estructura Inode en una cadena de bytes
    def pack(self):
        packed_inode = struct.pack(self.FORMAT, self.i_uid, self.I_gid, self.i_s, self.i_atime, self.i_ctime, self.i_mtime, self.i_type.encode('utf-8'), *self.i_block, self.i_perm)
        return packed_inode
    
    # Método para desempaquetar una cadena de bytes y construir una estructura Inode
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        inode = cls()
        inode.i_uid = unpacked_data[0]
        inode.I_gid = unpacked_data[1]
        inode.i_s = unpacked_data[2]
        inode.i_atime = unpacked_data[3]
        inode.i_ctime = unpacked_data[4]
        inode.i_mtime = unpacked_data[5]
        inode.i_type = unpacked_data[6].decode('utf-8')
        inode.i_block = list(unpacked_data[7:22])
        inode.i_perm = unpacked_data[22]
        return inode
        

# Definir clase Content
class Content:
    FORMAT = '12s i'                               # Formato de empaquetado de datos
    SIZE = struct.calcsize(FORMAT)                  # Tamaño en bytes de la estructura empaquetada

    def __init__(self, name, inode):
        self.b_name = name                          # Nombre del archivo o carpeta
        self.b_inodo = inode                        # Inodo del archivo o carpeta
    
    # Método para convertir la estructura Content a una cadena
    def __str__(self) -> str:
        return f"Name: {self.b_name}\n Inode: {self.b_inodo}"
    
    # Método para empaquetar la estructura Content en una cadena de bytes
    def pack(self):
        packed_content = struct.pack(self.FORMAT, self.b_name.encode('utf-8'), self.b_inodo)
        return packed_content
    
    # Método para desempaquetar una cadena de bytes y construir una estructura Content
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        content = cls("empty", -1)
        content.b_name = unpacked_data[0].decode('utf-8')
        content.b_inodo = unpacked_data[1]
        return content

# Definir clase FolderBlock
class FolderBlock:
    FORMAT = Content.FORMAT * 4                    # Formato de empaquetado de datos
    SIZE = struct.calcsize(FORMAT)                  # Tamaño en bytes de la estructura empaquetada

    def __init__(self):
        self.b_content = [Content("empty", -1) for _ in range(4)]   # Lista de contenidos (archivos o carpetas)
    
    # Método para convertir la estructura FolderBlock a una cadena
    def __str__(self) -> str:
        text = "FolderBlock: content=["
        for i in range(4):
            text += f"{self.b_content[i]}, "
        text += "]"
        return text
    
    # Método para empaquetar la estructura FolderBlock en una cadena de bytes
    def pack(self):
        packed_objetos = b''.join([obj.pack() for obj in self.b_content])
        return packed_objetos
    
    # Método para desempaquetar una cadena de bytes y construir una estructura FolderBlock
    @classmethod
    def unpack(cls, data):
        folderblock = cls()
        for i in range(4):
            # Extraer los datos binarios para cada objeto Content
            chunk = data[i * Content.SIZE: (i + 1) * Content.SIZE]
            folderblock.b_content[i] = Content.unpack(chunk)
        return folderblock

# Definir clase FileBlock
class FileBlock:
    FORMAT = '64s'                                 # Formato de empaquetado de datos
    SIZE = struct.calcsize(FORMAT)                  # Tamaño en bytes de la estructura empaquetada

    def __init__(self):
        self.b_content = "empty"                    # Contenido del archivo
    
    # Método para convertir la estructura FileBlock a una cadena
    def __str__(self) -> str:
        return f"FileBlock: content={self.b_content}"
    
    # Método para empaquetar la estructura FileBlock en una cadena de bytes
    def pack(self):
        packed_fileblock = struct.pack(self.FORMAT, self.b_content.encode('utf-8'))
        return packed_fileblock
    
    # Método para desempaquetar una cadena de bytes y construir una estructura FileBlock
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        fileblock = cls()
        fileblock.b_content = unpacked_data[0].decode('utf-8')
        return fileblock

# Definir clase PointerBlock
class PointerBlock:
    FORMAT = '16i'                                 # Formato de empaquetado de datos
    SIZE = struct.calcsize(FORMAT)                  # Tamaño en bytes de la estructura empaquetada

    def __init__(self):
        self.b_pointers = [-1] * 16                 # Punteros a otras estructuras
    
# Definir clase Superblock
class Superblock:
    FORMAT = 'i i i i i d d i i i i i i i i i i'    # Formato de empaquetado de datos
    SIZE = struct.calcsize(FORMAT)                  # Tamaño en bytes de la estructura empaquetada

    def __init__(self, inicio_particion, size_particion):
        # Calcular la cantidad de cada estructura que se puede almacenar en el tamaño de la partición
        number_of_structures = (size_particion - Superblock.SIZE) // (Inode.SIZE + 4+(3*FileBlock.SIZE))
        number_of_inodes = number_of_structures //4
        number_of_blocks = number_of_inodes * 3
        # Asignar valores a los campos del superbloque
        self.s_filesystem_type = 0xEF53                    # Identificador del tipo de sistema de archivos
        self.s_inodes_count = number_of_inodes              # Número de inodos que se pueden almacenar
        self.s_blocks_count = number_of_blocks              # Número de bloques que se pueden almacenar
        self.s_free_blocks_count = number_of_blocks         # Número de bloques libres disponibles
        self.s_free_inodes_count = number_of_inodes          # Número de inodos libres disponibles
        self.s_mtime = time.time()                          # Hora de la última modificación del sistema de archivos
        self.s_umtime = 0                                   # Momento en que se desmontó el sistema de archivos por última vez (0 si no se ha desmontado)
        self.s_mnt_count = 0                                 # Número de veces que se ha montado el sistema de archivos
        self.s_magic = 0xEF53                               # Número mágico que identifica al sistema de archivos
        self.s_inode_s = Inode.SIZE                          # Tamaño en bytes de un inodo
        self.s_block_s = FileBlock.SIZE                          # Tamaño en bytes de un bloque
        self.s_firts_ino = 0                                # Primer inodo reservado para almacenar información del sistema de archivos
        self.s_first_blo = 0                                # Primer bloque reservado para almacenar información del sistema de archivos
        self.s_bm_inode_start = inicio_particion + Superblock.SIZE      # Posición en bytes donde empieza el mapa de bits de inodos
        self.s_bm_block_start = self.s_bm_inode_start + self.s_inodes_count  # Posición en bytes donde empieza el mapa de bits de bloques
        self.s_inode_start = self.s_bm_block_start + self.s_blocks_count  # Posición en bytes donde empiezan los inodos
        self.s_block_start = self.s_inode_start + (self.s_inodes_count * Inode.SIZE)  # Posición en bytes donde empiezan los bloques
    
    # Método para convertir la estructura Superblock a una cadena
    def __str__(self) -> str:
        return f"Superblock: filesystem_type={self.s_filesystem_type}, inodes_count={self.s_inodes_count}, blocks_count={self.s_blocks_count}, free_blocks_count={self.s_free_blocks_count}, free_inodes_count={self.s_free_inodes_count}, mtime={self.s_mtime}, umtime={self.s_umtime}, mnt_count={self.s_mnt_count}, magic={self.s_magic}, inode_s={self.s_inode_s}, block_s={self.s_block_s}, firts_ino={self.s_firts_ino}, first_blo={self.s_first_blo}, bm_inode_start={self.s_bm_inode_start}, bm_block_start={self.s_bm_block_start}, inode_start={self.s_inode_start}, block_start={self.s_block_start}"
    
    # Método para empaquetar la estructura Superblock en una cadena de bytes
    def pack(self):
        packed_superblock = struct.pack(self.FORMAT, self.s_filesystem_type, self.s_inodes_count, self.s_blocks_count, self.s_free_blocks_count, self.s_free_inodes_count, self.s_mtime, self.s_umtime, self.s_mnt_count, self.s_magic, self.s_inode_s, self.s_block_s, self.s_firts_ino, self.s_first_blo, self.s_bm_inode_start, self.s_bm_block_start, self.s_inode_start, self.s_block_start)
        return packed_superblock
    
    # Método para desempaquetar una cadena de bytes y construir una estructura Superblock
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        superblock = cls(0,0)
        superblock.s_filesystem_type = unpacked_data[0]
        superblock.s_inodes_count = unpacked_data[1]
        superblock.s_blocks_count = unpacked_data[2]
        superblock.s_free_blocks_count = unpacked_data[3]
        superblock.s_free_inodes_count = unpacked_data[4]
        superblock.s_mtime = unpacked_data[5]
        superblock.s_umtime = unpacked_data[6]
        superblock.s_mnt_count = unpacked_data[7]
        superblock.s_magic = unpacked_data[8]
        superblock.s_inode_s = unpacked_data[9]
        superblock.s_block_s = unpacked_data[10]
        superblock.s_firts_ino = unpacked_data[11]
        superblock.s_first_blo = unpacked_data[12]
        superblock.s_bm_inode_start = unpacked_data[13]
        superblock.s_bm_block_start = unpacked_data[14]
        superblock.s_inode_start = unpacked_data[15]
        superblock.s_block_start = unpacked_data[16]
        return superblock