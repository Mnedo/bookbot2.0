class Test:
    def __init__(self, n):
        self.n = n

    def __eq__(self, other):
        print(self, other)


a = Test(1)
mn = [Test(2), Test(1)]
if a in mn:
    print(a)
