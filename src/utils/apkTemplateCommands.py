
class TemplateCommand(object):
    command = None
    
    def isIn(self, text):
        return self.command in text
    
    def format(self, text, args):
        return text


class ReplaceCommand(TemplateCommand):
    command = '/* REPLACE('
    
    def format(self, text, args):
        commandData = text[text.index(self.command) + len(self.command):]
        paramEndIndex = commandData.find(')')
        indexes = [int(index.strip()) - 1 for index in
                   commandData[:paramEndIndex].split(',')]
        key = commandData[commandData.find(':', paramEndIndex) + 1:].strip()
        key = key[:key.find(' ')]
        return text[:indexes[0]] + args[key] + text[indexes[1]:]

_commands = [
    ReplaceCommand(),
]

def runTemplateCommands(text, formatArgs):
    for command in _commands:
        if (command.isIn(text)):
            return command.format(text, formatArgs)
    return text
