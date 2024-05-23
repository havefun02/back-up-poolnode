def read_block():
    block=None
    with open('mining.txt', 'r') as file:
        lines = file.readlines()
        if (len(lines)>0):
            block = lines[0].strip()
    return block

def write_block(block):
    lines=[]
    with open('mining.txt', 'r') as file:
        lines=file.readlines()
    with open('mining.txt', 'w') as file:
        if (len(lines)>0):
                lines[0]=str(block)+'\n'
                file.writelines(lines)
                return True
        else:
            lines.insert(0,str(block)+'\n')
            file.writelines(lines)
            return True

    return False
    

def read_counter():
    counter=None
    with open('mining.txt', 'r') as file:
        lines = file.readlines()
        if (len(lines)>1):
            counter = lines[1].strip()
    return counter

def write_counter(counter):
    lines=[]
    with open('mining.txt', 'r') as file:
        lines=file.readlines()
    with open('mining.txt', 'w') as file:
        if (len(lines)>1):
                lines[1]=str(counter)+'\n'
                file.writelines(lines)
                return True
        else:
            lines.insert(1,str(counter)+'\n')
            file.writelines(lines)
            return True
    return False
        
