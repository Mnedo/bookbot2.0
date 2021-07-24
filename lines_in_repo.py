import os

name = os.getcwd()


def analyze(path):
    size = 0
    for elem in os.listdir(path):
        elem = os.path.join(path, elem)
        if os.path.isfile(elem):
            try:
                size += len(open(elem, 'r', encoding='UTF-8').read().split('\n'))
            except Exception:
                pass
        elif os.path.isdir(elem):
            size += analyze(elem)
    return size


print(analyze(name), 'строк')
