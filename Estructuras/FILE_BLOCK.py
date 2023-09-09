# Importar módulos necesarios
import struct

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
        print("Data length:", len(data))
        unpacked_data = struct.unpack(cls.FORMAT, data)
        fileblock = cls()
        fileblock.b_content = unpacked_data[0].decode('utf-8')
        return fileblock
    