import struct

# Definir clase PointerBlock
class PointerBlock:
    FORMAT = '16i'                                 # Formato de empaquetado de datos
    SIZE = struct.calcsize(FORMAT)                  # Tamaño en bytes de la estructura empaquetada

    def __init__(self):
        self.b_pointers = [-1] * 16                 # Punteros a otras estructuras
    
