# Importar módulos necesarios
import struct
from Estructuras.CONTENT import Content

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