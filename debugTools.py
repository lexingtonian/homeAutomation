
ECHO = True
FORCE = True

#tools for debuggin etc
#mainly to echo stuff on terminal

def printOnTerminal(txt):
    if ECHO:
        print(txt)

def forceOnTerminal(txt):
    if FORCE:
        print(txt)