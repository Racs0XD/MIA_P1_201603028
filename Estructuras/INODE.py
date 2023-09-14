# Importar módulos necesarios
import time
import struct

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

