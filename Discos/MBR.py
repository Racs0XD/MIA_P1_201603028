# Importando las librerias necesarias 
import struct
import time
import random
from Discos.PARTITION import Partition

class MBR:
    # Definición del formato de la estructura MBR
    FORMAT = 'i d i c'
    # Cálculo del tamaño de la estructura MBR en bytes
    SIZE = struct.calcsize(FORMAT)+Partition.SIZE*4

    # Constructor de la clase MBR
    def __init__(self, params):
        # Obtiene la unidad de medida y tamaño del disco
        unit = params.get('unit', 'M').upper().replace(' ', '')
        size = int(params['size'])

        # Convierte el tamaño a bytes dependiendo de la unidad de medida
        if unit == 'K':
            self.mbr_tamano = size * 1024
        elif unit == 'M':
            self.mbr_tamano = size * 1024 * 1024
        else:
            raise ValueError(f"Parametro de unidad invalido: {unit}")

        # Obtiene la fecha y hora de creación del disco, firma y política de ajuste
        self.mbr_fecha_creacion = time.time()
        self.mbr_dsk_signature = random.randint(1, 1000000)
        self.fit = params.get('fit', 'FF').upper()
        
        # Crea un diccionario con valores aleatorios para crear las particiones
        ex = {'size': 10, 'path': 'path', 'name': 'empty'}
        # Crea una lista con 4 particiones vacias
        self.particiones = [Partition(ex), Partition(ex), Partition(ex), Partition(ex)]
        
        # Imprime la información del disco recién creado usando la librería prettytable
        print("\n---------------- MBR CREADO CORRECTAMENTE ----------------\n")
        from prettytable import PrettyTable
        table = PrettyTable()
        table.field_names = ["Size", "Date", "Sig.", "Fit"]
        table.add_row([self.mbr_tamano, self.mbr_fecha_creacion, self.mbr_dsk_signature, self.fit])
        print(table)
        print("-------------------------------------------------------------\n")
        
        # Verifica que el tipo de ajuste sea válida
        if self.fit not in ['BF', 'FF', 'WF']:
            raise ValueError(f"Tipo de ajuste invalido: {self.fit}")
        
        
    # Sobrecarga del método str para imprimir la información del MBR
    def __str__(self):
        return f"MBR: size={self.mbr_tamano}, date={self.mbr_fecha_creacion}, signature={self.mbr_dsk_signature}, fit={self.fit}, partitions={self.particiones[0]}, {self.particiones[1]}, {self.particiones[2]}, {self.particiones[3]}"

    # Empaqueta los datos del MBR en la estructura definida en el atributo FORMAT y en las particiones
    def pack(self):
        # Obtiene el primer caracter de la política de ajuste y lo codifica
        fit_char = self.fit[0].encode()
        
        # Empaqueta la información del MBR
        packed_mbr = struct.pack(self.FORMAT, self.mbr_tamano, self.mbr_fecha_creacion, self.mbr_dsk_signature, fit_char)
        
        # Empaqueta la información de las particiones
        packed_objetos = b''.join([obj.pack() for obj in self.particiones])
        
        return packed_mbr+packed_objetos

    # Desempaqueta los datos del MBR y las particiones de una cadena de bytes
    @classmethod
    def unpack(cls, data):
        print("Desempaquetando MBR")
        # Desempaqueta los datos del MBR de la estructura y los almacena en una tupla
        unpacked_data = struct.unpack(cls.FORMAT, data[:struct.calcsize(cls.FORMAT)])
        
        ex = {'size': 5, 'path': 'path', 'name': 'name'}
        # Crea un MBR vacio con los valores predeterminados del diccionario ex
        mbr = cls(ex)
        # Asigna los valores del MBR extraidos de la tupla desempaquetada
        mbr.mbr_fecha_creacion = 0
        mbr.mbr_tamano = unpacked_data[0]
        mbr.mbr_fecha_creacion = unpacked_data[1]
        mbr.mbr_dsk_signature = unpacked_data[2]
        fit_char = unpacked_data[3].decode()  # Decodifica el caracter de la política de ajuste
        fit_map = {'B': 'BF', 'F': 'FF', 'W': 'WF', 'N': 'NF'}
        mbr.fit = fit_map[fit_char]
        
        ex = {'size': 10, 'path': 'path', 'name': 'name'}
        # Crea una lista vacia para las particiones
        mbr.particiones = [Partition(ex), Partition(ex), Partition(ex), Partition(ex)]

        # Desempaqueta cada partición de la cadena de bytes y la asigna a la lista de particiones
        temp = Partition.unpack(data[struct.calcsize(cls.FORMAT):struct.calcsize(cls.FORMAT) + Partition.SIZE])
        temp2 = Partition.unpack(data[struct.calcsize(cls.FORMAT)+Partition.SIZE:struct.calcsize(cls.FORMAT)+Partition.SIZE*2])
        temp3 = Partition.unpack(data[struct.calcsize(cls.FORMAT)+Partition.SIZE*2:struct.calcsize(cls.FORMAT)+Partition.SIZE*3])
        temp4 = Partition.unpack(data[struct.calcsize(cls.FORMAT)+Partition.SIZE*3:struct.calcsize(cls.FORMAT)+Partition.SIZE*4])
        mbr.particiones[0] = temp
        mbr.particiones[1] = temp2
        mbr.particiones[2] = temp3
        mbr.particiones[3] = temp4
        
        
        return mbr