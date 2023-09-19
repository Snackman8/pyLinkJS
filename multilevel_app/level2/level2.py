def button_clicked(jsc):
    """ simple example of a button click """
    print('LEVEL2')


def ready(jsc, *args):
    """ called when a webpage creates a new connection the first time on load """
    print('LEVEL2 CONNECT')


def reconnect(jsc, *args):
    print('LEVEL2 RECONNECT')
