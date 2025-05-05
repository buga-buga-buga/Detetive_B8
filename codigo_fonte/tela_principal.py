# pyinstaller --windowed --name "Procura_B8" --icon="logo.ico" --add-data "logo.png;." --version-file="version.rc" --upx-dir=. tela_principal.py
#
#
#

import splash_screen
import Procura_B8

import tkinter 
from tkinter import filedialog, messagebox, Button, Entry, Checkbutton

import os, shutil
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



def remove_pycache():
    pycache_path = os.path.join(os.getcwd(), "__pycache__") 
    if os.path.exists(pycache_path):  
        try:
            shutil.rmtree(pycache_path) 
        except Exception as e:
            pass


def main_window():

    def sai_programa():
        print("Tchau...")
        remove_pycache() 
        root.quit()
        root.destroy()    


    global root
    root = tkinter.Tk()
    root.title("Investigador de B8")
    root.geometry("400x230")  

    # Adiciona o protocolo para interceptar o fechamento da janela
    root.protocol("WM_DELETE_WINDOW", sai_programa)

    def open_folder_selection():
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder_var.set(folder_path)

    def continue_program():
        selected_folder = folder_var.get()
        if selected_folder:
            args = []
            if debug_var.get():
                args.append("-d")
            if sound_var.get():
                args.append("-s")
            args_str = " ".join(args)

            # Desabilitar apenas widgets que suportam a propriedade 'state'
            for widget in root.winfo_children():
                if isinstance(widget, (Button, Entry, Checkbutton)):
                    widget.config(state='disabled')
            #Procura_B8.main(args_str, selected_folder)
            try:
                Procura_B8.main(args_str, selected_folder)
            except SystemExit as e:
                print(f"Programa principal encerrou com código de erro: {e.code}")
                sys.exit(e.code)
        else:
            messagebox.showwarning("Presta atenção!", "Selecione uma pasta com os pdfs a serem analisados.")


    def exit_program():
        root.destroy()

    def show_help():
        help_window = tkinter.Toplevel(root)
        help_window.title("Ajuda")
        help_window.geometry("1000x400")
        help_text = tkinter.Text(help_window, wrap=tkinter.WORD)
        help_text.pack(expand=True, fill='both', padx=1, pady=1)

        texto_ajuda = """                                      Investigador de B8

Esse programa executa uma busca em todos os arquivos 'pdf' de um diretório à procura de itens proibidos.

Uma janela para acompanhamento da execução é aberta e caso seja fechada o programa é encerrado. Evite rolar as paginas porque o negócio é sensivel, pode ficar sem responder, mas nao ta travado nao, depois ele volta!

Ao final do processamento sao gerados 3 arquivos (log, texto e tabela), analise-os com sabedoria.

Pode-se optar por ligar debug e som. 
Checando em Debug incluira informações adicionais durante o processamento.
Habilitar som faz com que um bip seja emitido a cada item proibido encontrado.
       
As tipagens abaixo, por serem suscetíveis à corrosão sob tensão não são permitidos:

        ASTM A193: B8, B8N, B8T, B8LN, B8SH
        ASTM A453: 660
        ASTM A564: 630, 631, 635, 17-4PH, 17-7PH, 17-6PH
        ASTM F593: F593A, F593B, F593C, F593D, 1, 3, 4, 5, 6, 7
        ASTM 3506: A1, A2, A3, C1, C3, C4, F1
        ISO 4017: A1, A2, A3
        AISI: 303, 304, 321

        Referência: I-ET-3010.00-1200-251-P4X-001
        """
        help_text.insert(tkinter.END,texto_ajuda)
        help_text.config(state='disabled')

    folder_var = tkinter.StringVar()
    debug_var = tkinter.BooleanVar()
    sound_var = tkinter.BooleanVar()

    # Frame principal
    main_frame = tkinter.Frame(root)
    main_frame.pack(expand=True, fill='both', padx=10, pady=10)

    # Botão de ajuda no topo
    help_button = tkinter.Button(main_frame, text="?", command=show_help, width=2)
    help_button.pack(anchor='ne')

    # Título e botão de ajuda
    label = tkinter.Label(main_frame, text="Escolha o diretorio que contem os arquivos a serem analisados:")
    label.pack(anchor='w')

    # Seleção de pasta
    folder_frame = tkinter.Frame(main_frame)
    folder_frame.pack(fill='x', pady=(5, 0))
    folder_button = tkinter.Button(folder_frame, text="Selecionar Pasta", command=open_folder_selection)
    folder_button.pack(side='left')
    folder_label = tkinter.Label(folder_frame, textvariable=folder_var, anchor='w')
    folder_label.pack(side='left', padx=(5, 0), fill='x', expand=True)

    # Checkboxes
    check_frame = tkinter.Frame(main_frame)
    check_frame.pack(fill='x', pady=10)
    debug_check = tkinter.Checkbutton(check_frame, text="Debug", variable=debug_var)
    debug_check.pack(side='left', expand=True)
    sound_check = tkinter.Checkbutton(check_frame, text="Som", variable=sound_var)
    sound_check.pack(side='left', expand=True)

    # Botão Processar centralizado
    process_button_frame = tkinter.Frame(main_frame)
    process_button_frame.pack(pady=(5, 0))  # Reduzi o espaçamento acima para subir o botão
    continue_button = tkinter.Button(process_button_frame, text="Processar", command=continue_program)
    continue_button.pack()

    # Botão Sair alinhado totalmente à direita
    exit_button_frame = tkinter.Frame(main_frame)
    exit_button_frame.pack(fill='x', pady=(5, 10))  # Espaçamento ajustado
    exit_button = tkinter.Button(exit_button_frame, text="Sair", command=sai_programa)
    exit_button.pack(side='right', padx=(0, 10))  # Alinhamento total à direita com padding

    # Versão alinhada com os botões
    version_label = tkinter.Label(main_frame, text="Versão 0.01", anchor='w')
    version_label.pack(fill='x', padx=1, pady=(5, 0))

    root.mainloop()

# No início do seu programa principal
splash_screen.show_splash(duration=3000)

# Iniciando a janela principal diretamente
main_window()
