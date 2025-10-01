# versao do pacote
__version__ = "0.0.2" 

# Indica quais módulos exportar com "from meu_pacote import *"
__all__ = ['splash_screen', 'tela_principal', 'procura_B8']

# Importações dos módulos
from . import tela_principal as _core    
from . import splash_screen as _splash
from . import tela_principal as _gui