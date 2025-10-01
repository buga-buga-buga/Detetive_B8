# Detetive_B8

> Vasculha arquivos PDFs em busca de **materiais de fixação não permitidos** de
acordo com a especificacao técnica REQUIREMENTS FOR BOLTING MATERIALS -> 
I-ET-3010.00-1200-251-P4X-001.

Gera arquivos de saida para acompanhar o processamento, **log**, **relatório**
e uma **planilha.csv**.

# Programas

1. **procura_B8.py**: Faz a leitura de cada PDF do diretorio, extrai texto, 
procura por combinações **norma + padrão** (com variações de grafia),
anota **página/linha**, marca páginas **não pesquisáveis** e salva saídas. 
Abre uma janela com console rolável durante a execução. 

2. **tela_principal.py**: Janela/Tela principal do programa.

3. **splash_screen.py**: Mostra o **logotipo do IEEI** por 3 segundos antes da
janela principal.


## Uso
### Pré-requisitos
- Python 3.x
- Bibliotecas: diversas, dependencias disponiveis em requirements.txt

### Instalação
1. Clone o repositório.
2. Navegue até o diretório do projeto.
3. Instale as dependências -> pip install -r requirements.txt

### Execução
1. Execute o script `tela_principal.py`, o funcionamento é intuitivo.

### Licença
Este projeto não tem licença alguma e pode ser usado como voce bem entender.