"""
procura_B8.py

Descrição:
Este script processa arquivos PDF em um diretório, buscando materiais de fixação
proibidos conforme especificacao Petrobras.

Gera relatórios em texto e CSV, além de exibir uma janela com console rolável
para acompanhamento da execução.

Orientações sobre a entrada:
- O diretório informado deve conter os arquivos PDF que se queira investigar.
- Caso nenhum diretório seja informado, será usado o diretório atual.
- Argumentos opcionais:
    -d ou --debug : ativa mensagens detalhadas de depuração.
    -s ou --som   : emite um beep a cada ocorrência de item proibido encontrada.

Sobre a saída:
- Gera três arquivos no diretório atual:
    - log_<data_hora>.txt       : log completo da execução.
    - relatorio_<data_hora>.txt : resumo por arquivo, normas e padrões encontrados.
    - relatorio_execucao_<data_hora>.csv : planilha com status e detalhes.

Melhorias em versões futuras:
- Implementar OCR automático para PDFs não pesquisáveis.
- Barra de progresso na interface gráfica.

Ideias para novas funcionalidades:
- Opção de rodar em modo silencioso (sem interface gráfica).

Referências:
       REQUIREMENTS FOR BOLTING MATERIALS -> I-ET-3010.00-1200-251-P4X-001
Disponivel em:
       https://canalfornecedor.petrobras.com.br/en/regras-de-contratacao/catalogo-de-padronizacao
Navegue na pagina por:   
  FPSO -> Own EEP - Basic Project All Electric 225kbpd / Own EEP - Basic Project for Revitalization -> Static Equipment 
ou download direto aqui:
       https://webserver-petrobrasecossistemaint-prod1.lfr.cloud/documents/10591749/32979894/I-ET-3010.00-1200-251-P4X-001_F.pdf


Histórico de alterações:
- 2025 04 17 Versão 0.0.1: Implantação.
- 2025 09 30 Versão 0.0.2: Ajustes finos.
"""

import PyPDF2
import argparse
import datetime
import os
import pathlib
import pkg_resources
import platform
import psutil
import re
import socket
import sys
import time
import tkinter
import traceback
import winsound
from tkinter import scrolledtext
from tkinter import messagebox

#
# O grande barato é deixar a tela aberta sempre quando o programa estiver 
# processando os arquivos.
# Isso é feito com a variável janela_ativa, que é setada como True quando o 
# programa é iniciado.
# Isso garante que a janela só feche quando o processamento terminar, mesmo 
# que o energumeno clique no botão de fechar.
#
janela_ativa = True

#
class RedirectText:
    """
    Redirecionar os comandos 'print' pra uma janela e para um arquivo 
        (opcional, se informado, gravarei)
    """
    
    def __init__(self, text_widget, filename=None):
        self.text_widget = text_widget
        self.filename = filename
        self.file = None
        # quer que grava em arquivo tambem ?
        if filename:
            self.file = open(filename, "w", encoding="utf-8")

    def write(self, string):
        global janela_ativa
        #  Aqui é o pulo do gato, só da pra mandar o texto pra tela se ela
        #  estiver ativa!
        if janela_ativa:
            try:
        # Insere o texto na janela se ele ainda existir (sempre bom garantir)
                if self.text_widget.winfo_exists():
                    self.text_widget.insert(tkinter.END, string)
                    self.text_widget.see(tkinter.END)
                    self.text_widget.update()
            except tkinter.TclError:
                return  # Ignora erros se o widget/janela não existir mais

        # Escreve o texto que acabamos de colocar na janela pro arquivo, 
        # quer dizer, se ele estiver aberto
        if self.file and not self.file.closed:
            self.file.write(string)

    def force_write(self, string):
        """
        Escreve uma string no arquivo e força a gravação imediata.

        :param string: Texto a ser escrito.
        """
        if self.file and not self.file.closed:
            self.file.write(string + "\n")
            self.file.flush()

    def flush(self):
        """
        Força a gravação de qualquer texto pendente no arquivo.
        """
        if self.file and not self.file.closed:
            try:
                self.file.flush()
            except ValueError:
                return  # Ignora o erro se o arquivo já estiver fechado

    def close(self):
        """
        Fecha o arquivo se ele estiver aberto.
        """
        if self.file and not self.file.closed:
            self.file.close()

    def __del__(self):
        """
        Garante que o arquivo seja fechado quando o objeto for destruído.
        """
        self.close()


# Bibliotecas importadas e utilizadas no programa
bibliotecas = [
    "PyPDF2",
    "argparse",
    "bs4",
    "datetime",
    "getpass",
    "logging",
    "os",
    "pathlib",
    "pkg_resources",
    "platform",
    "psutil",
    "re",
    "requests",
    "socket",
    "subprocess",
    "sys",
    "time",
    "tkinter",
    "traceback",
    "urllib3",
    "warnings",
    "winsound",
]
#
#  Especificacao "REQUIREMENTS FOR BOLTING MATERIALS" disponivel em:
#
#  https://canalfornecedor.petrobras.com.br/en/regras-de-contratacao/catalogo-de-padronizacao
#  
#  FPSO -> Own EEP - Basic Project All Electric 225kbpd / Own EEP - Basic Project for Revitalization -> Static Equipment 
#
#  Download direto aqui:
#  https://webserver-petrobrasecossistemaint-prod1.lfr.cloud/documents/10591749/32979894/I-ET-3010.00-1200-251-P4X-001_F.pdf?download=true
#

# Definição dos materiais proibidos => norma:padrao
normas = {
    "A193": ["B8 ", "B8N", "B8T", "B8LN", "B8SH"],
    "A453": ["660"],
    "A564": ["630", "631", "635", "17-4PH", "17-7PH", "17-6PH"],
    "F593": ["F593A", "F593B", "F593C", "F593D", "1", "3", "4",
              "5", "6", "7"],
    "AISI": ["303", "304", "321"],
    "3506": ["A1", "A2", "A3", "C1", "C3", "C4", "F1"],
    "4017": ["A1", "A2", "A3"],
    "A540": ["630", "631", "635"],
    "A 193": ["B8 ", "B8N", "B8T", "B8LN", "B8SH"],
    "A 453": ["660"],
    "A 564": ["630", "631", "635", "17-4PH", "17-7PH", "17-6PH"],
    "F 593": ["F593A", "F593B", "F593C", "F593D", "1", "3", "4",
               "5", "6", "7"],
    "A 540": ["630", "631", "635"],
    "A-193": ["B8 ", "B8N", "B8T", "B8LN", "B8SH"],
    "A-453": ["660"],
    "A-564": ["630", "631", "635", "17-4PH", "17-7PH", "17-6PH"],
    "F-593": ["F593A", "F593B", "F593C", "F593D", "1", "3", "4", 
              "5", "6", "7"],
    "A-540": ["630", "631", "635"],
}
# Pra dar um confere => norma nem sera usada, só o 'padrao'
strings_especificas = {
    "A193": ["B8 ", "B8N", "B8T", "B8LN", "B8SH", "B8 N", "B8 T", 
             "B8 LN", "B8 SH"],
    "A564": [
        "17-4PH",
        "17-7PH",
        "17-6PH",
        "17-4 PH",
        "17-7 PH",
        "17-6 PH",
        "S17400",
        "S17600",
        "S17700",
    ],
    "F593": [
        "F593A",
        "F593B",
        "F593C",
        "F593D",
        "F593 A",
        "F593 B",
        "F593 C",
        "F593 D",
        "F593-A",
        "F593-B",
        "F593-C",
        "F593-D",
    ],
}

def criar_janela():
    global janela_ativa
    janela = tkinter.Tk()  # Cria a janela principal do Tkinter
    janela.title("Investigador de B8")  # Define o título da janela
    janela.geometry("800x500")  # Define o tamanho da janela
    janela.aspect(16, 9, 16, 9)  # Define a proporção da janela

    # Cria um widget ScrolledText para exibir texto com barra de rolagem
    texto_saida = tkinter.scrolledtext.ScrolledText(
        janela, wrap=tkinter.WORD, width=120, height=30, font=("Courier", 10)
    )
    texto_saida.pack(padx=10, pady=10, fill=tkinter.BOTH, expand=True)

    def on_closing():
        global janela_ativa

        # janela_ativa ta com false se ja terminou, o usuario pode fechar a
        # janela depois de finalizado o processamento ou resolver que ta 
        # demorando muito e encerrar a porra toda.

        if janela_ativa == False:
            if tkinter.messagebox.askokcancel(
                "Fechar essa janela ? ",
                "O resultado apresentado aqui pode ser consultado no log do" \
                " processamento.",
            ):
                janela.destroy()
            return
        else:
            if tkinter.messagebox.askokcancel(
                "Fechar janela",
                "Confirma que deseja fechar? O processamento será" \
                " interrompido.",
            ):
                sys.stdout.force_write(
                    "\n000 - Erro - Usuario interrompeu a execução do" \
                    " programa."
                )
                janela.quit()
                janela.destroy()

                if isinstance(sys.stdout, RedirectText):
                    sys.stdout.close()

                os._exit(1)
                # só pra garantir
                sys.exit(1)

        # Atualiza a geometria da janela para centralizá-la na tela
        
        janela.update_idletasks()
        width = janela.winfo_width()
        height = janela.winfo_height()
        x = janela.winfo_screenwidth() // 2 - width // 2
        y = janela.winfo_screenheight() // 2 - height // 2
        janela.geometry(f"+{x}+{y}")

    janela.protocol(
        "WM_DELETE_WINDOW", on_closing
    )  # Usuario clicou no x pra fechar a janela ? MALDITO!!!!!
    return janela, texto_saida


def parse_arguments():
    """
    Processa os argumentos da linha de comando.

    Argumentos:
    Nenhum

    Retorna:
    Um objeto Namespace contendo os seguintes atributos:
    - debug (bool): Se o modo de depuração está ativado
    - som (bool): Se os avisos sonoros estão ativados
    - diretorio (str): O diretório a ser processado (padrão é o atual)

    Uso na linha de comando:
    python script.py [-d] [-s] [diretorio]
    """
    parser = argparse.ArgumentParser(
        description="Processador de PDFs para busca de materiais proibidos"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Ativar modo de depuração"
    )
    parser.add_argument(
        "-s", "--som", action="store_true", help="Ativar avisos sonoros"
    )
    parser.add_argument(
        "diretorio", nargs="?", default=".", help="Diretório a ser processado"
    )

    return parser.parse_args()


def exibir_versoes_bibliotecas(bibliotecas):
    """
    Exibe as versões das bibliotecas especificadas e lista as que não foram
      encontradas.

    :param bibliotecas: Lista de nomes de bibliotecas a serem verificadas.
    """
    # Lista para armazenar bibliotecas não encontradas
    nao_encontradas = []

    for biblioteca in bibliotecas:
        try:
    # Tenta obter a versão da biblioteca usando pkg_resources
            versao = pkg_resources.get_distribution(biblioteca).version
            print(f" - {biblioteca}: {versao}")
        except pkg_resources.DistributionNotFound:
    # Adiciona a biblioteca à lista de não encontradas se não for encontrada
            nao_encontradas.append(biblioteca)

    if nao_encontradas:
    # Converte a lista de não encontradas em uma string separada por vírgulas
        nao_encontradas_str = ", ".join(nao_encontradas)
        print()
        print(
             "  Bibliotecas não encontradas ou embutidas no Python: "
            f"{nao_encontradas_str}"
        )


def dados_sistema():
    """
    Coleta e exibe informações detalhadas sobre o sistema, incluindo
    sistema operacional, arquitetura, processador, memória, espaço em disco,
    domínio, hostname, IP, versão do Python e versões das bibliotecas.
    """
    # Coleta informações do sistema operacional
    sistema_operacional = platform.system()
    versao_sistema_operacional = platform.release()
    arquitetura = platform.machine()
    processador = platform.processor()
    hostname = socket.gethostname()
    IP = socket.gethostbyname(hostname)
    dominio = os.environ.get("USERDOMAIN")  # Obtém o domínio do usuário

    # Memória (em Gibas) RAM total e livre 
    memoria_total = psutil.virtual_memory().total / (1024 * 1024 * 1024)  
    memoria_livre = psutil.virtual_memory().available / (1024 * 1024 * 1024) 

    # Espaço total e livre no drive
    drive_total = psutil.disk_usage("/").total / (1024 * 1024 * 1024)  # em GB
    drive_livre = psutil.disk_usage("/").free / (1024 * 1024 * 1024)  # em GB

    # Exibe as informações coletadas
    print()
    print(f"Sistema Operacional: {sistema_operacional} "
          f"{versao_sistema_operacional}")
    print(f"Arquitetura: {arquitetura} Processador: {processador}")
    print(f"Memória RAM Total: {memoria_total:.2f} GB Livre: "
          f"{memoria_livre:.2f} GB")
    print(f"Espaço total em disco: {drive_total:.2f} GB Livre:"
          f"{drive_livre:.2f} GB")
    print()
    print(f"Domínio: {dominio} Hostname: {hostname} IP: {IP} ")
    print()
    print(f"Dados do Python: ")
    print(f"  Versão: {sys.version.split()[0]}")
    print(f"  Compilação: {' '.join(sys.version.split()[1:])}")
    print(f"  Executável: {sys.executable}")
    print("  Caminhos de pesquisa do módulo:")
    for path in sys.path:
        print(f"    {path}")

    print()
    print(f"Versão das bibliotecas: ")
    exibir_versoes_bibliotecas(bibliotecas)

    print()
    return

def buscar_parafusos(texto, page_num, linha_num):
    """
    Busca por normas e padrões específicos em um texto e retorna os resultados 
    encontrados.

    :param texto: O texto onde a busca será realizada.
    :param page_num: O número da página onde o texto está localizado.
    :param linha_num: O número da linha onde o texto está localizado.
    :return: Um dicionário com as normas encontradas e seus respectivos
      padrões, páginas e linhas.
    """
    # Dicionário para armazenar os resultados da busca
    resultados = {}

    # Roda tudo, tem que procurar se nao nao acha!
    for norma, padroes in normas.items():
        # Verifica se a norma está presente no texto (busca case-insensitive)
        if re.search(r"\b" + re.escape(norma) + r"\b", texto, re.IGNORECASE):
            for padrao in padroes:
                # Verifica se o padrão está presente no texto
                if re.search(r"\b" + re.escape(padrao) + r"\b", texto,
                              re.IGNORECASE):
                    # Se não estiver nos resultados, adiciona
                    if norma not in resultados:
                        resultados[norma] = []
                    # Adiciona o padrão, número da página e número da linha
                    #  aos resultados
                    resultados[norma].append((padrao, page_num, linha_num))
    return resultados  # Retorna o dicionário de resultados


def buscar_parafusos_perdidos(texto, page_num, linha_num, 
                              resultados_existentes):
    """
    Busca por strings específicas em um texto e retorna os resultados 
    encontrados, evitando duplicatas.
    Deve ser sempre executada após a execucao da buscar_parafusos
    :param texto: O texto onde a busca será realizada.
    :param page_num: O número da página onde o texto está localizado.
    :param linha_num: O número da linha onde o texto está localizado.
    :param resultados_existentes: Dicionário com resultados já existentes 
    para evitar duplicatas.
    :return: Um dicionário com as normas encontradas e suas respectivas 
    strings, páginas e linhas.
    """
    # Dicionário para armazenar os resultados da busca
    resultados = {}
    # Conjunto para rastrear combinações já adicionadas
    combinacoes_ja_adicionadas = set()

    for norma, strings in strings_especificas.items():
        for string in strings:
            # Cria um padrão de busca que permite espaços opcionais entre
            #  as palavras
            pattern = r"\b" + re.escape(string).replace(r"\ ", r"\s*") + r"\b"
            # Verifica se a string está presente no texto
            if re.search(pattern, texto, re.IGNORECASE):
                duplicado = False
                # Verifica se a string já foi encontrada nos resultados 
                # existentes
                for norma_existente, padroes in resultados_existentes.items():
                    for padrao in padroes:
                        if (
                            string == padrao[0]
                            and page_num == padrao[1]
                            and linha_num == padrao[2]
                        ):
                            if d_on:
                                print(
                                    f"Opa, aqui eu já tinha achado..."
                                    f" Padrão: {padrao[0]}, Página: "
                                    f"{padrao[1]}, Linha: {padrao[2]}"
                                )
                            duplicado = True
                            break
                    if duplicado:
                        break
                # Se a string não for duplicada, adiciona aos resultados
                if not duplicado:
                    if norma not in resultados:
                        resultados[norma] = []
                    resultados[norma].append((string, page_num, linha_num))
                    combinacoes_ja_adicionadas.add((string, page_num, 
                                                    linha_num))
                    print(
                        f"** Localizado proibido !** Norma: {norma}, "
                        f"Padrão: {string}, Página: {page_num}, Linha: "
                        f"{linha_num}"
                    )
                    print(f"**Conteudo da linha** {texto}")
                    if som:
                        winsound.Beep(1000, 500)
    return resultados  # Retorna o dicionário de resultados


def processar_pdfs_no_diretorio(diretorio):
    """
    Processa todos os arquivos PDF no diretório especificado, buscando por 
    normas e padrões específicos, gera um relatório e uma tabela CSV com os
      resultados.

    :param diretorio: Caminho do diretório onde os arquivos PDF estão 
    localizados.
    :return: 'Tuple' contendo o relatório, a tabela CSV e o contador de 
    PDFs processados.
    """
    # Lista para armazenar o relatório
    relatorio = []
    # Lista para armazenar a tabela CSV
    tabela_csv = []
    # Flag para indicar se encontrou arquivos PDF
    encontrou_pdf = False
    # Contador de arquivos PDF processados
    contador_pdfs = 0

    # Lista todos os arquivos PDF no diretório
    arquivos_pdf = [
        nome_arquivo
        for nome_arquivo in os.listdir(diretorio)
        if nome_arquivo.lower().endswith(".pdf")
    ]
    total_arquivos = len(arquivos_pdf)  # Total de arquivos PDF encontrados

    for nome_arquivo in arquivos_pdf:
        # Obtém o caminho completo do arquivo PDF
        caminho_completo = os.path.normpath(os.path.join(diretorio,
                                                          nome_arquivo))

        # Aquele confere só pra garantir
        if nome_arquivo.lower().endswith(".pdf"):
            # Indica que pelo menos um arquivo PDF foi encontrado
            encontrou_pdf = True
            # Incrementa o contador de arquivos PDF processados
            contador_pdfs += 1
            # Marca o tempo de início do processamento
            start_time = time.time()
            # Calcula o tamanho do arquivo em MB
            tamanho_arquivo_bytes = os.path.getsize(caminho_completo)
            tamanho_arquivo_mb = tamanho_arquivo_bytes / (1024 * 1024)
            print(
                f"**Processando o arquivo: {contador_pdfs} de {total_arquivos}"
                 f"** {nome_arquivo}"
            )
            # força envio da mensagem pra tela, pro usuario saber que mudou 
            # de arquivo e nao ficar desesperado achando que travou
            tkinter.Tk.update(tkinter._default_root)

            # Flag para indicar se o PDF é pesquisável
            pdf_pesquisavel = False
            # Lista para páginas em branco ou não pesquisáveis
            paginas_em_branco_ou_nao_pesquisaveis = []

            try:
                # Abre o arquivo PDF para leitura
                with open(caminho_completo, "rb") as pdf_file:
                    # Aqui a verdadeira magia acontece! Cria o leitor de PDF
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    # Obtém o total de páginas no PDF
                    total_paginas = len(pdf_reader.pages)

                    if d_on:
                        print(f"Arquivo possui {total_paginas} paginas.")

                    # Dicionário para armazenar os resultados da busca
                    resultados = {}

                    # Roda o pdf todo
                    for page_num in range(len(pdf_reader.pages)):
                        # Obtém o objeto da página corrente
                        page_obj = pdf_reader.pages[page_num]
                        if d_on:
                            print(f"** Lendo página {page_num+1} de"
                                  f"{total_paginas} **")
                        try:
                            # Extrai o texto da página
                            text = page_obj.extract_text()
                            # tinha texto ? Marca que o PDF é pesquisável
                            if text:
                                pdf_pesquisavel = True
                                # Divide o texto da pagina em linhas
                                linhas = text.splitlines()
                                # Roda cada linha dessa pagina
                                for linha_num, linha in enumerate(linhas, start=1):
                                    if d_on:
                                        print(f"**Linha {linha_num}:** {linha}")
                                    # print(f"Texto da linha: {repr(linha)}")
                                    # if "B8 " in linha:
                                    #    print(f"'B8' encontrado em: {linha}")

                                    # Vamos procurar pra ver se acha alguma coisa
                                    resultados_paragrafo = buscar_parafusos(
                                        linha, page_num + 1, linha_num
                                    )
                                    # Bateu preguiça aqui, vai ultrapassar a coluna 79
                                    for norma, padroes in resultados_paragrafo.items():
                                        for padrao in padroes:
                                            print(
                                                f"**Achei um proibido!** Página {padrao[1]}, Linha {padrao[2]}: {norma} - {padrao[0]}"
                                            )
                                            print(f"**Conteudo da linha** {linha}")
                                            if som:
                                                winsound.Beep(1000, 500)
                                            if norma not in resultados:
                                                resultados[norma] = []
                                            resultados[norma].append(padrao)

                                    # Vai la e da um confere antes, vai que passou algo
                                    resultados_especificas = buscar_parafusos_perdidos(
                                        linha, page_num + 1, linha_num, resultados
                                    )

                                    for (
                                        norma,
                                        padroes,
                                    ) in resultados_especificas.items():
                                        if norma not in resultados:
                                            resultados[norma] = []
                                        # pulo do gato, afinal aqui é a repescagem
                                        resultados[norma].extend(padroes)
                            # Nao tinha texto na pagina
                            else:
                                paginas_em_branco_ou_nao_pesquisaveis.append(
                                    page_num + 1
                                )
                                if d_on:
                                    print(f"** Pagina não pesquisavel ou em branco.**")
                        except Exception as e:
                            print(f"**Erro ao ler o PDF:** {e}")
                            # Exibe o traceback do erro, seila, vai que...
                            traceback.print_exc()

                    # Prepara as informações para o CSV

                    # Verifica se há páginas em branco ou não pesquisáveis
                    if paginas_em_branco_ou_nao_pesquisaveis:
                        # Converte cada número de página em uma string e 
                        # converte o resultado do map em uma lista.
                        paginas_str_list = list(
                            map(str, paginas_em_branco_ou_nao_pesquisaveis)
                        )
                        # Junta as strings em uma única, separadas por ", "
                        paginas_str = ", ".join(paginas_str_list)
                    # Se não houver páginas em branco ou não pesquisáveis, 
                    # define a string como vazia
                    else:
                        paginas_str = ""

                    # Se houver resultados, prepara a linha CSV indicando que 
                    # o arquivo contém materiais proibidos
                    if resultados:
                        linha_csv = f"{nome_arquivo};SIM;{paginas_str};"
                        # Lista para armazenar os detalhes dos resultados 
                        # encontrados
                        detalhes = []
                        # Deixa bonitinho a norma seguido do que nao pode
                        for norma, padroes in resultados.items():
                            norma_str = (
                                f"ASTM {norma}"
                                if norma in ["A193", "A453", "A564", "F593", 
                                             "A540"]
                                else norma
                            )

                            for padrao in padroes:
                                detalhes.append(
                                    f"{norma_str} - {padrao[0]} (Página"
                                     f"{padrao[1]}, Linha {padrao[2]})"
                                )

                        # Junta todos os detalhes em uma única string separada
                        #  por ponto e vírgula e adiciona à linha CSV
                        linha_csv += ";".join(detalhes)

                    # Se não houver resultados, prepara a linha CSV indicando 
                    # que o arquivo não contém materiais proibidos
                    else:
                        linha_csv = f"{nome_arquivo};NAO;{paginas_str};"

                    # Adiciona a linha à tabela
                    tabela_csv.append(linha_csv)

                    # Adiciona informações ao relatório
                    relatorio.append("")
                    relatorio.append(
                    "/////////////////////////////////////////////////////////"
                    )
                    relatorio.append(f"Processado.....: {nome_arquivo}")

                    if resultados:
                        for norma, padroes in resultados.items():
                            #
                            # Se a norma estiver na lista abaixo prefixe com
                            #  "ASTM"
                            #
                            if norma in ["A193", "A453", "A564", "F593", 
                                         "A540"]:
                                norma_str = f"ASTM {norma}"
                            else:
                                # Caso contrário, usa a norma como está
                                norma_str = norma

                            relatorio.append(f"{norma_str}:")

                            for padrao in padroes:
                                relatorio.append(
                                    f" - {padrao[0]} (Página {padrao[1]},"
                                     f" Linha {padrao[2]})"
                                )
                    else:
                        relatorio.append(
                            "Não localizado nenhum BOLTING MATERIALS proibido "
                            "no documento."
                        )

                    if paginas_em_branco_ou_nao_pesquisaveis:
                        relatorio.append(f"A T E N Ç Ã O")
                        relatorio.append(
                             "Páginas em branco ou não pesquisáveis: "
                            f"{paginas_str}"
                        )

                end_time = time.time()
                elapsed_time = end_time - start_time
                msg_analisado = (
                    f"Analisadas {total_paginas} paginas, arquivo com "
                    f"{tamanho_arquivo_mb:.3f} MB decorridos "
                    f"{elapsed_time:.2f} segundos." )
                print(f"**{msg_analisado}")
                relatorio.append(msg_analisado)
                print()

            except Exception as e:
                print(f"**Erro ao abrir o arquivo:** {e}")
                continue

            if not pdf_pesquisavel:
                print(f"A T E N Ç Ã O")
                print(
                    f"O arquivo '{nome_arquivo}' não é pesquisável. Por favor,"
                     " realize a validação manualmente."
                )
                print()

    if not encontrou_pdf:
        print(f"**Diretorio nao contem arquivos pdf**")
        print()

    return relatorio, tabela_csv, contador_pdfs


def main(args_str=None, selected_folder=None):
    global d_on, som, janela_ativa
    janela_ativa = True
    janela = None  # Inicialize aqui

    while janela_ativa:
        # janela.update()
        # Se os argumentos não forem fornecidos, use parse_arguments()
        if args_str is None or selected_folder is None:
            args = parse_arguments()
            d_on = args.debug
            som = args.som
            diretorio_processamento = args.diretorio
        else:
            # Parse os argumentos manualmente
            d_on = "-d" in args_str
            som = "-s" in args_str
            diretorio_processamento = selected_folder

        # Crie a janela e o widget de texto
        janela, texto_saida = criar_janela()

        # Redirecione os displays pra janela e grave em arquivo
        log_filename = (
            f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        sys.stdout = RedirectText(texto_saida, log_filename)

        janela.update()

        # Mensagem de início do programa
        print( "****** Início do programa ******* Data: "
            f"{datetime.datetime.now().strftime('%Y-%m-%d')}  Hora: "
            f"{datetime.datetime.now().strftime('%H:%M:%S')}" )

        # Exibir os argumentos recebidos
        print("Argumentos recebidos:")
        print(f"Modo de depuração (debug): {'Ativado' if d_on else 'Desativado'}")
        print(f"Aviso sonoro: {'Ativado' if som else 'Desativado'}")
        print(f"Diretório a ser processado: {diretorio_processamento}")

        # Verifique se o diretório existe
        if not os.path.isdir(diretorio_processamento):
            mensagem_erro = (
                f"007 - Erro: O diretório '{diretorio_processamento}' não existe."
            )
            print(mensagem_erro)
            tkinter.messagebox.showerror("Erro no processamento...", mensagem_erro)
            return

        dados_sistema()

        print("Iniciando o processamento...")

        caminho_atual = pathlib.Path.cwd()
        print(f"O diretório atual é: {caminho_atual}")
        if not os.access(caminho_atual, os.W_OK):
            print(f"Atenção: Sem acesso para gravação no diretório atual '{caminho_atual}', logs podem não ser disponibilizados.")
            return
        print(f"O diretório a ser processado é: {diretorio_processamento}")

        # Executa o programa propriamente dito.
        relatorio_final, linhas_csv, contador_pdfs = processar_pdfs_no_diretorio(
            diretorio_processamento
        )

        print(f"Foram processados {contador_pdfs} arquivos pdf nessa execução.")

        if relatorio_final:
            nome_relatorio = (
                f"relatorio_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            relatorio_final.append("")
            relatorio_final.append(
                "/////////////////////////////////////////////////////////"
            )
            with open(nome_relatorio, "w", encoding="utf-8") as arquivo:
                for linha in relatorio_final:
                    arquivo.write(f"{linha}\n")

        print("/////////////////////////////////////////////////////////")

        if linhas_csv is None or not linhas_csv:
            pass
        else:
            nome_arquivo_csv = f"relatorio_execucao_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            cabecalho = "Nome Arquivo;Localizado item proibido;Páginas em branco ou não pesquisáveis;Detalhes"

            with open(nome_arquivo_csv, "w", encoding="utf-8-sig") as planilha:
                planilha.write(cabecalho + "\n")
                for linha in linhas_csv:
                    columns = linha.split(";")
                    if columns[2] == "1":
                        columns[2] = "Documento não pesquisável"
                    linha_atualizada = ";".join(columns)
                    planilha.write(linha_atualizada + "\n")

            print()
            print("Relatorios de processamento gerados com sucesso!")
            print(f"{log_filename}")
            print(f"{nome_relatorio}")
            print(f"{nome_arquivo_csv}")
            print()

        if not janela_ativa:
            break

        # Mensagem de fim de processamento
        print(
            f"Data: {datetime.datetime.now().strftime('%Y-%m-%d')} Hora:"
            f"  {datetime.datetime.now().strftime('%H:%M:%S')} "
            " ****** Fim do programa ******* " )
        # sys.exit(0)
        #
        janela_ativa = False

    if not janela_ativa:
        tkinter.messagebox.showinfo(
            "Processo finalizado", "Verifique os arquivos gerados."
        )

    if isinstance(sys.stdout, RedirectText):
        sys.stdout.close()

    # Inicie o loop da interface gráfica
    janela.mainloop()


if __name__ == "__main__":
    main()
