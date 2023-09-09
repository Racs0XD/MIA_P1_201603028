# Importar módulos necesarios
import struct

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