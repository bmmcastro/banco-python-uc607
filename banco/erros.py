#erros próprios do sistema

class UtilizadorJaExisteError(Exception):
    pass

class UtilizadorInexistenteError(Exception):
    pass

class SaldoInsuficienteError(Exception):
    pass

class ContaBloqueadaError(Exception):
    pass
