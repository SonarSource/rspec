from click import ClickException

class RuleNotFoundError(ClickException):
    def __init__(self, id):
        super().__init__(f'No rule has ID {id}')

class InvalidArgumentError(ClickException):
    '''Exception raised when an invalid argument is given to a CLI command.'''
    def __init__(self, message):
        super().__init__(message)

class GitError(ClickException):
    '''Exception raised when some error happened with git commands.'''
    def __init__(self, message):
        super().__init__(message)

class RuleValidationError(ClickException):
    '''Exception raised when a rule did not pass validation.'''
    def __init__(self, message):
        super().__init__(message)
