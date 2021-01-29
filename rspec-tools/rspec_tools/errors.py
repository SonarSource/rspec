from click import ClickException

class RuleNotFoundError(ClickException):
    def __init__(self, id):
        super().__init__(f'No rule has ID {id}')
