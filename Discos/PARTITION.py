# Importando la librería necesaria
import struct

class Partition:
    # Se define la estructura de datos de la partición con un formato predefinido
    FORMAT = 'i 16s c c i c i'
    SIZE = struct.calcsize(FORMAT)

    # Constructor para la clase Partition
    def __init__(self, params):
        # Extraemos el tamaño de la partición de los parámetros
        size_param = params.get('size')
        self.actual_size = int(size_param)

        # Validamos que el tamaño sea un entero positivo mayor a cero
        if self.actual_size < 0:
            raise ValueError("El tamaño debe ser un entero positivo mayor a cero")

        # Extraemos el nombre de la partición de los parámetros y validamos que no esté vacío
        self.name = params.get('name').replace('"', '')
        if not self.name:
            raise ValueError("El nombre de la partición no puede estar vacío")

        # Extraemos la unidad de los parámetros; si no se proporciona, se usa la unidad "K"
        self.unit = params.get('unit', 'K').upper().replace(' ', '')
        if self.unit not in ['B', 'K', 'M']:
            raise ValueError(f"Unidad inválida: {self.unit}")

        # Calculamos el tamaño real de la partición en bytes, según la unidad proporcionada
        if self.unit == 'B':
            self.actual_size = self.actual_size
        elif self.unit == 'K':
            self.actual_size = self.actual_size * 1024
        elif self.unit == 'M':
            self.actual_size = self.actual_size * 1024 * 1024
        
        # Extraemos el tipo de la partición de los parámetros, si no se proporciona, se usa el tipo "P"
        self.type = params.get('type', 'P').upper().replace(' ', '')
        
        # Se inicializa el status en 0, lo que significa que la partición no está ocupada
        self.status = 0
        
        # Se extrae el parámetro fit, que indica el método de ajuste de la partición dentro del disco (por defecto, "FF")
        self.fit = params.get('fit', 'FF').upper().replace(' ', '')
        
        # Para uso interno, se inicializa la variable que indica la posición de la partición dentro del disco en 0
        self.byte_inicio = 0

    # Sobrecarga del método str para imprimir la información de la partición
    def __str__(self):
        # Se devuelve una cadena con información relevante de la partición
        return f"Partición: nombre={self.name}, tamaño={self.actual_size} bytes, unidad={self.unit}"

    # Empaqueta los atributos de la partición en formato binario
    def pack(self):
        fit_char = self.fit[0].encode() 
        packed_partition = struct.pack(self.FORMAT, self.actual_size, self.name.encode('utf-8'), self.unit.encode('utf-8'), self.type.encode('utf-8'), self.status, fit_char, self.byte_inicio)
        return packed_partition

    # Extrae los datos binarios para desempaquetarlos y crear una partición a partir de ellos
    @classmethod
    def unpack(cls, data):
        unpacked_data = struct.unpack(cls.FORMAT, data)
        ex = {'size': 10, 'path': 'path', 'name': 'name'}
        partition = cls(ex)
        partition.actual_size = unpacked_data[0] # se extrae el tamaño
        partition.name = unpacked_data[1].decode('utf-8').strip('\x00') # se extrae el nombre
        partition.unit = unpacked_data[2].decode('utf-8') # se extrae la unidad
        partition.type = unpacked_data[3].decode('utf-8') # se extrae el tipo
        partition.status = unpacked_data[4] # se extrae el status
        fit_char = unpacked_data[5].decode() # se extrae el ajuste
        fit_map = {'B': 'BF', 'F': 'FF', 'W': 'WF', 'N': 'NF'}
        partition.fit = fit_map[fit_char] # se guarda el ajuste en un formato más fácil de leer 
        partition.byte_inicio = unpacked_data[6] # se extrae la posición de inicio
        return partition