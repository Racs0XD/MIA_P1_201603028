# Importando las librerias necesarias 
import struct

class EBR:
    # Definición del formato de la estructura EBR
    FORMAT = 'i c c i i 16s i'
    # Cálculo del tamaño en bytes de la estructura EBR
    SIZE = struct.calcsize(FORMAT)
    
    # Constructor de la clase EBR
    def __init__(self, params, start):
        # Obtiene la unidad de medida y el tamaño de la partición
        unit = params.get('unit', 'M').upper().replace(' ', '')
        self.actual_size = int(params.get('size'))

        
        # Verifica que el tamaño sea un entero positivo mayor que cero
        if self.actual_size < 0:
            raise ValueError("El tamaño debe ser un número entero positivo mayor que 0")

        # Convierte el tamaño a bytes dependiendo de la unidad de medida
        if unit == 'B':
            self.actual_size = self.actual_size
        elif unit == 'K':
            self.actual_size = self.actual_size * 1024
        elif unit == 'M':
            self.actual_size = self.actual_size * 1024 * 1024
        else:
            raise ValueError(f"Parametro de unidad invalido: {unit}")
        
        # Obtiene la política de ajuste, estado, tipo, inicio, nombre y siguiente de la partición
        self.fit = params.get('fit', 'FF').upper().replace(' ', '')
        self.status = 0
        self.type = params.get('type','L').upper().replace(' ', '')
        self.start = start
        self.name = params.get('name').replace('"', '')
        
        # Verifica que el nombre no esté vacío
        if not self.name:
            raise ValueError("El cambo name no debe estar vacío")
        
        self.next = -1
        
    # Sobrecarga del método str para imprimir la información de la partición EBR
    def __str__(self):
        return f"EBR: nombre={self.name}, tamaño={self.actual_size} bytes, siguiente={self.next}"
    
    # Empaqueta los datos de la partición EBR en la estructura definida en el atributo FORMAT
    def pack(self):
        # Obtiene el primer caracter de la política de ajuste y lo codifica
        fit_char = self.fit[0].encode()
        
        # Empaqueta las información de la partición EBR
        packed_mbr = struct.pack(self.FORMAT, self.status,fit_char, self.type.encode('utf-8'), self.start, self.actual_size, self.name.encode('utf-8'), self.next)
        return packed_mbr
    
    # Desempaqueta los datos de la partición EBR de una cadena de bytes
    @classmethod
    def unpack(cls, data):
        print("desempaquetando EBR")
        # Desempaqueta los datos de la estructura y los almacena en una tupla
        unpacked_data = struct.unpack(cls.FORMAT, data)
        
        # Crea un diccionario para los parámetros necesarios para la creación de la partición EBR
        ex = {'size': 1, 'path': 'path', 'name': 'empty'}
        # Crea una partición EBR con los parámetros predeterminados y un valor de -1 para el atributo next
        ebr = cls(ex,-1)
        
        # Obtiene la información de la partición EBR desde la tupla desempaquetada
        ebr.status = unpacked_data[0]
        fit_char = unpacked_data[1].decode()  # Decodifica el caracter de la política de ajuste
        fit_map = {'B': 'BF', 'F': 'FF', 'W': 'WF', 'N': 'NF'}
        ebr.fit = fit_map[fit_char]
        ebr.type = unpacked_data[2].decode('utf-8')
        ebr.start = unpacked_data[3]
        ebr.actual_size = unpacked_data[4]
        ebr.name = unpacked_data[5].decode('utf-8').strip('\x00')
        ebr.next = unpacked_data[6]
        return ebr