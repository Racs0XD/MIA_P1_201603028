import os
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.INODE import Inode

# Esta función busca un espacio libre dentro del archivo, en base a los parámetros de byte y tipo que se le entregan.
# Si tipo es 0, busca en el inodo correspondiente al byte entregado. Si tipo es 1, busca en el FolderBlock correspondiente.
# Retorna un booleano que indica si se encontró espacio libre, el byte libre encontrado, el tipo de bloque donde se encontró el espacio libre, y el índice en caso de ser un FolderBlock.

def busca(file,byte,tipo,x):
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        if inodo.i_type == 1:
            return False, None
        esta = False
        v = None
        for n in inodo.i_block:
            if n == -1:
                continue
            esta,v = busca(file,n,1,x)
            if esta:
                break
        return esta,v
    elif tipo == 1:
        file.seek(byte)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        esta = False
        v = None
        for n in folder.b_content:
            if n.b_inodo == -1:
                continue
            if n.b_name.rstrip('\x00') == x:
                esta = True
                v = n.b_inodo
                break
        return esta,v

def busca_espacio_libre(file,byte,tipo):
    x = -1
    if tipo == 0:
        file.seek(byte)
        inodo = Inode.unpack(file.read(Inode.SIZE))
        if inodo.i_type == 1:
            return False, None
        libre = False
        byte_libre = None
        tipo_libre =None
        indice_libre    = None
        for i,n in enumerate(inodo.i_block):
            if n == -1:
                return True,byte,tipo,i
            libre, byte_libre, tipo_libre,indice_libre = busca_espacio_libre(file,n,1)
            if libre:
                break
        return libre, byte_libre, tipo_libre,indice_libre
    elif tipo == 1:
        file.seek(byte)
        folder = FolderBlock.unpack(file.read(FolderBlock.SIZE))
        libre = False
        byte_libre = None
        tipo_libre = 1
        indice_libre    = None
        for i,n in enumerate(folder.b_content):
            #print(f'nombre del nodo {n.b_name} y nombre buscado {x} y numero de inodo {n.b_inodo}')
            if n.b_inodo == -1 and n.b_name.rstrip('\x00') == "empty":
                return True,byte,tipo,i
            
        return False, None, None,None 

# Esta función recupera el contenido de un archivo. Si el archivo no existe en la ruta entregada, se muestra un mensaje de error y se retorna un string vacío.
# En caso contrario, se abre el archivo, se guarda su contenido en una variable, y se retorna.

def get_file_content(partial_path):
    current_directory = os.getcwd()
    full_path = full_path= f'{current_directory}{partial_path}'
    
    if not os.path.exists(full_path):
        print(f"Error: El archivo {full_path} no existe.")
        return ''

    with open(full_path, 'r') as file:
        content = file.read()

    return content