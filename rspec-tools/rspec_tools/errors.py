from click import ClickException


class InvalidArgumentError(ClickException):
    '''Exception raised when an invalid argument is given to a CLI command.'''

    def __init__(self, message):
        super().__init__(message)


class RuleValidationError(ClickException):
    '''Exception raised when a rule did not pass validation.'''

    def __init__(self, message):
        super().__init__(message)
