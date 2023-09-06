# Importando las librerias necesarias 
import os
import struct
from Discos.MBR import MBR
from Discos.EBR import EBR
from Discos.PARTITION import Partition

# Define la función fdisk que crea una partición en un archivo de disco
def fdisk(params):
    print("\n📁 creando partición...")
    # Obtiene la ruta del archivo de disco
    filename = params.get('path')
    current_directory = os.getcwd()
    full_path = os.path.join(current_directory, 'discos_test', filename)
    
    # Verifica si la ruta existe y si es así abre el archivo y lee el MBR, de lo contrario retorna un error
    if not os.path.exists(full_path):
        print(f"Error: El archivo {full_path} no existe.")
        return
    
    # Crea una partición temporal y se verifica si se desea eliminar o agregar una partición
    ex = {'size': 10, 'path': 'path', 'name': 'empty'}
    nueva_particion = None
    if 'delete' in params or 'add' in params:
        nueva_particion = Partition(ex)
    else:
        nueva_particion = Partition(params)
    # Asigna un valor de 1 al atributo status de la partición y se crea una partición temporal
    nueva_particion.status = 1
    particion_temporal = nueva_particion
    
    # Lee las 4 particiones del archivo de disco y las almacena en una lista
    partitions = []
    with open(full_path, "rb+") as file:
        file.seek(0)
        data = file.read(MBR.SIZE)
        x = MBR.unpack(data[:MBR.SIZE])
        disk_size = x.mbr_tamano
        disk_fit = x.fit
        print("tamaño del disco ",disk_size)
        space = disk_size - MBR.SIZE
        for i in range(4):
            file.seek(struct.calcsize(MBR.FORMAT)+(i*Partition.SIZE))
            data = file.read(Partition.SIZE)
            particion_temporal = Partition.unpack(data)
            partitions.append(particion_temporal)
        
        realizar = True
        # Verifica si se desea eliminar o agregar una partición, en caso contrario revisa si es posible añadir otra partición
        if 'delete' in params or 'add' in params:
            realizar = False
        elif all(item.status == 1 for item in partitions) and 'type' in params and nueva_particion.type != 'L':
            realizar = False
            print("No se puede crear la particion, ya que todas las particiones estan ocupadas")
            return
        count_E = sum(1 for item in partitions if item.type == 'E')
        if count_E == 1 and nueva_particion.type == 'E':
            realizar = False
            print("No se puede crear la particion, ya que ya existe una particion extendida")
            return
        
        partitions2 = partitions
        nueva_particion.fit = disk_fit
        byteinicio = MBR.SIZE
        if nueva_particion.type == 'L' and realizar:
            #busca una partición extendida en la lista de particiones y obtiene el byte_inicio
            for i, item in enumerate(partitions):
                if item.type == 'E':
                    tamano_de_e = item.actual_size
                    inicio_de_e = item.byte_inicio
                    byteinicio = item.byte_inicio
                    limite_final_de_e = item.byte_inicio+item.actual_size
                    file.seek(byteinicio)
                    ebr = EBR.unpack(file.read(EBR.SIZE))
                    if ebr.next == -1:
                        #crea el EBR si es necesario
                        ebr = EBR(params, byteinicio)
                        ebr.next= byteinicio+EBR.SIZE+ebr.actual_size
                        #verifica si hay espacio para crear la partición
                        if ebr.next > limite_final_de_e:
                            print("No hay espacio para crear la particion")
                            return
                        file.seek(byteinicio)
                        file.write(ebr.pack())
                        nuevo_ebr = EBR(ex, ebr.next)
                        file.seek(ebr.next)
                        file.write(nuevo_ebr.pack())
                        return
                    else :
                        while ebr.next != -1:
                            file.seek(ebr.next)
                            ebr = EBR.unpack(file.read(EBR.SIZE))
                        #crea el EBR si es necesario
                        nuevo_ebr = EBR(params, ebr.start)
                        nuevo_ebr.next = nuevo_ebr.start+EBR.SIZE+nuevo_ebr.actual_size
                        if nuevo_ebr.next > limite_final_de_e:
                            print("No hay espacio para crear la particion")
                            return
                        file.seek(ebr.start)
                        file.write(nuevo_ebr.pack())
                        nuevo_nuevo_ebr = EBR(ex, nuevo_ebr.next)
                        file.seek(nuevo_ebr.next)
                        file.write(nuevo_nuevo_ebr.pack())
                        return
            print(f'no existe particion extendida, error al agregar la particion logica{params.get("name") }')            
            return
        
        # Verifica si se puede agregar una partición usando la política de ajuste FF
        if nueva_particion.fit == 'FF' and realizar:
            nueva_particion.fit = params.get('fit', 'FF').upper()
            for i, item in enumerate(partitions):   
                if (item.status == 0 and item.name == "empty") or (item.status ==0 and space >= nueva_particion.actual_size):   
                    if i == 0:
                        byteinicio = MBR.SIZE
                    else :
                        byteinicio = partitions[i-1].byte_inicio+partitions[i-1].actual_size
                    probable = byteinicio+nueva_particion.actual_size
                    permiso = True
                    for j, item2 in enumerate(partitions2[(i+1):]):
                        if probable > item2.byte_inicio and item2.byte_inicio != 0:
                            permiso = False
                        
                    if permiso == True:        
                        nueva_particion.byte_inicio = byteinicio
                        partitions[i] = nueva_particion
                        item = nueva_particion
                        print(f"La partición {partitions[i]} fue creada satisfactoriamente.")
                        break 
            packed_objetos = b''.join([obj.pack() for obj in partitions])
            file.seek(struct.calcsize(MBR.FORMAT))
            file.write(packed_objetos)
            if nueva_particion.type == 'E':
                #crea el EBR si es necesario
                ebr = EBR(ex, nueva_particion.byte_inicio)
                file.seek(nueva_particion.byte_inicio)
                file.write(ebr.pack())
            return 
        # Verifica si se puede agregar una partición usando la política de ajuste BF
        elif nueva_particion.fit == 'BF' and realizar:
            nueva_particion.fit = params.get('fit', 'FF').upper()
            sale = space+1
            indice = -1
            for i,n in enumerate(partitions):
                if (n.status == 0 and n.name == "empty") and (i==0 or partitions[i-1].status == 1):
                    if i == 0:
                        anterior = MBR.SIZE
                    else :
                        anterior = partitions[i-1].byte_inicio+partitions[i-1].actual_size
                        
                    siguiente = -1    
                    
                    if i == 3 and n.status == 0:
                        siguiente = disk_size
                    for j, n2 in enumerate(partitions2[(i+1):]):
                        if n2.status == 1:
                            siguiente = n2.byte_inicio
                            break
                        elif j ==len(partitions2[(i+1):])-1 and n2.status == 0:
                            siguiente = disk_size
                            
                    espacio = siguiente-anterior
                    
                    if nueva_particion.actual_size <= espacio and espacio < sale:
                        sale = espacio
                        indice = i
                        byteinicio = anterior
                
            nueva_particion.byte_inicio = byteinicio
            partitions[indice] = nueva_particion
            print("Tamaño de particiones ", len(partitions))
            print(f"La partición se escribió en el índice {indice}")
            packed_objetos = b''.join([obj.pack() for obj in partitions])
            file.seek(struct.calcsize(MBR.FORMAT))
            file.write(packed_objetos)
            if nueva_particion.type == 'E':
                #crea el EBR si es necesario
                ebr = EBR(ex, nueva_particion.byte_inicio)
                file.seek(nueva_particion.byte_inicio)
                file.write(ebr.pack())
            return
        # Verifica si se puede agregar una partición usando la política de ajuste WF
        elif nueva_particion.fit == 'WF' and realizar:
            nueva_particion.fit = params.get('fit', 'FF').upper()
            max_space = -1  # Comienza con un valor negativo como centinela
            indice = -1
            for i, n in enumerate(partitions):
                if (n.status == 0 and n.name == "empty") and (i == 0 or partitions[i - 1].status == 1):
                    if i == 0:
                        anterior = MBR.SIZE
                    else:
                        anterior = partitions[i - 1].byte_inicio + partitions[i - 1].actual_size

                    siguiente = -1

                    if i == 3 and n.status == 0:
                        siguiente = disk_size
                    for j, n2 in enumerate(partitions2[(i + 1):]):
                        if n2.status == 1:
                            siguiente = n2.byte_inicio
                            break
                        elif j == len(partitions2[(i + 1):]) - 1 and n2.status == 0:
                            siguiente = disk_size

                    espacio = siguiente - anterior

                    if nueva_particion.actual_size <= espacio and espacio > max_space:
                        max_space = espacio
                        indice = i
                        byteinicio = anterior

            if indice != -1:
                nueva_particion.byte_inicio = byteinicio
                partitions[indice] = nueva_particion
                print("Tamaño de particiones ", len(partitions))
                print(f"La partición se escribió en el índice {indice}")
                packed_objetos = b''.join([obj.pack() for obj in partitions])
                file.seek(struct.calcsize(MBR.FORMAT))
                file.write(packed_objetos)
                if nueva_particion.type == 'E':
                    #crea el EBR si es necesario
                    ebr = EBR(ex, nueva_particion.byte_inicio)
                    file.seek(nueva_particion.byte_inicio)
                    file.write(ebr.pack())
                return
            else:
                print("No hay espacio disponible para la partición usando el algoritmo WF")
        # Verifica si se desea eliminar una partición
        elif 'delete' in params:
            partition_name_to_delete = params.get('name')
            if not partition_name_to_delete:
                print("Error: No se proporcionó el nombre de la partición a eliminar.")
                return
            partition_found = False
            for i, partition in enumerate(partitions):
                if partition.name == partition_name_to_delete:
                    # solicita confirmación antes de eliminar la partición
                    user_input = input(f"¿Está seguro de que desea eliminar la partición {partition_name_to_delete}? (sí/no): ")
                    if user_input.lower() != "sí":
                        print("Eliminación cancelada por el usuario.")
                        return

                    partition_found = True
                    # Actualiza los detalles de la partición
                    partition.status = 0
                    partition.name = "empty"
                    partition.type = "P"

                    # Si es una eliminación completa, llena el espacio de la partición con el caracter \0
                    #start_byte = partition.byte_inicio
                    #end_byte = start_byte + partition.actual_size
                    #file.seek(start_byte)
                    #file.write(b'\0' * (end_byte - start_byte))

                    # Actualiza la tabla de particiones en el archivo de disco
                    packed_objetos = b''.join([obj.pack() for obj in partitions])
                    file.seek(struct.calcsize(MBR.FORMAT))
                    file.write(packed_objetos)
                    print(f"La partición {partition_name_to_delete} ha sido eliminada satisfactoriamente.")
                    return

            if not partition_found:
                print(f"Error: La partición {partition_name_to_delete} no existe.")
                return
        # Verifica si se desea añadir espacio a una partición
        elif 'add' in params:
            # Obtiene el nombre de la partición a redimensionar
            partition_name_to_resize = params.get('name')
            if not partition_name_to_resize:
                print("Error: No se proporcionó el nombre de la partición para cambiar su tamaño.")
                return

            # Obtiene el tamaño a añadir a la partición
            try:
                additional_size = int(params['add'])
                unit = params.get('unit', 'K').upper()  # Se establece Kilobytes como valor predeterminado si no se proporciona ninguna unidad
                if unit == 'B':
                    multiplier = 1
                elif unit == 'K':
                    multiplier = 1024
                elif unit == 'M':
                    multiplier = 1024 * 1024
                
                additional_size = additional_size * multiplier
            except ValueError:
                print("Error: valor inválido para el tamaño adicional.")
                return

            partition_found = False
            for i, partition in enumerate(partitions):
                if partition.name == partition_name_to_resize:
                    partition_found = True
                    
                    # Calcula el espacio después de la partición actual
                    if i == len(partitions) - 1:
                        free_space = disk_size - (partition.byte_inicio + partition.actual_size)
                    else:
                        free_space = partitions[i+1].byte_inicio - (partition.byte_inicio + partition.actual_size)

                    # Comprueba si hay suficiente espacio para agregar el tamaño adicional
                    if additional_size <= free_space:
                        # Actualiza el tamaño de la partición
                        partition.actual_size += additional_size
                        print(f"La partición {partition_name_to_resize} ha sido redimensionada satisfactoriamente.")
                        
                        # Actualiza la tabla de particiones en el archivo de disco
                        packed_objetos = b''.join([obj.pack() for obj in partitions])
                        file.seek(struct.calcsize(MBR.FORMAT))
                        file.write(packed_objetos)
                    else:
                        print(f"Error: No hay suficiente espacio para extender la partición {partition_name_to_resize}.")
                    return

            if not partition_found:
                print(f"Error: La partición {partition_name_to_resize} no existe.")
                return