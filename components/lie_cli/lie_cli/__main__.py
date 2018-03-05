from twisted.conch.stdio import ConsoleManhole, runWithProtocol as console


class ConsoleWrapper(ConsoleManhole):
    def connectionMade(self):
        super(ConsoleWrapper, self).connectionMade()
        self.interpreter.push(b'from lie_cli import *')
        self.interpreter.push(b'session = connect()')
        self.lineReceived(b'print("welcome")')


if __name__ == '__main__':
    console(ConsoleWrapper)
