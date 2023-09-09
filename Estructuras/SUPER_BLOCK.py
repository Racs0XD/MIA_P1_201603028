# Importar módulos necesarios
import struct
import time
from Estructuras.INODE import Inode
from Estructuras.FILE_BLOCK import FileBlock



# Definir clase Superblock
class Superblock:
    FORMAT = 'i i i i i d d i i i i i i i i i i'    # Formato de empaquetado de datos
    SIZE = struct.calcsize(FORMAT)                  # Tamaño en bytes de la estructura empaquetada

    def __init__(self, inicio_particion, size_particion, filesystem_type=2):
        # Calcular la cantidad de cada estructura que se puede almacenar en el tamaño de la partición
        number_of_structures = (size_particion - Superblock.SIZE) // (Inode.SIZE + 4+(3*FileBlock.SIZE))
        number_of_inodes = number_of_structures //4
        number_of_blocks = number_of_inodes * 3
        # Asignar valores a los campos del superbloque
        self.s_filesystem_type = 0xEF53 if filesystem_type == 2 else 0xEF51  # Identificador del tipo de sistema de archivos (0xEF53 ext2, 0xEF51 ext3)
        self.s_inodes_count = number_of_inodes              # Número de inodos que se pueden almacenar
        self.s_blocks_count = number_of_blocks              # Número de bloques que se pueden almacenar
        self.s_free_blocks_count = number_of_blocks         # Número de bloques libres disponibles
        self.s_free_inodes_count = number_of_inodes          # Número de inodos libres disponibles
        self.s_mtime = time.time()                          # Hora de la última modificación del sistema de archivos
        self.s_umtime = 0                                   # Momento en que se desmontó el sistema de archivos por última vez (0 si no se ha desmontado)
        self.s_mnt_count = 0                                 # Número de veces que se ha montado el sistema de archivos
        self.s_magic = 0xEF53 if filesystem_type == 2 else 0xEF51 # Número mágico que identifica al sistema de archivos
        self.s_inode_s = Inode.SIZE                          # Tamaño en bytes de un inodo
        self.s_block_s = FileBlock.SIZE                      # Tamaño en bytes de un bloque
        self.s_firts_ino = 0                                # Primer inodo reservado para almacenar información del sistema de archivos
        self.s_first_blo = 0 if filesystem_type == 2 else 1  # Primer bloque reservado para almacenar información del sistema de archivos (0 ext2, 1 ext3)
        self.s_bm_inode_start = inicio_particion + Superblock.SIZE      # Posición en bytes donde empieza el mapa de bits de inodos
        self.s_bm_block_start = self.s_bm_inode_start + self.s_inodes_count  # Posición en bytes donde empieza el mapa de bits de bloques
        self.s_inode_start = self.s_bm_block_start + (self.s_blocks_count * 4)  # Posición en bytes donde empiezan los inodos
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
        superblock = cls(0,0,0)
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