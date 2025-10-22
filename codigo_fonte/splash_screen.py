"""
splash_screen.py

Descrição:
Exibe uma splash screen com a imagem do logotipo da gerencia ("logo.png") 
centralizada na tela por 3 segundos. 
Utilizada antes da abertura da interface principal.

Orientações:
- A imagem "logo.png" deve estar no mesmo diretório do script ou incluída no pacote.
- Compatível com empacotamento via PyInstaller (usa sys._MEIPASS para localizar recursos).

Sobre a saída:
- Apenas exibe a imagem temporariamente; não gera arquivos.

Histórico de alterações:
- 2025 04 17 Versão 0.0.1: Implantação.
- 2025 10 01 Versão 0.0.2: Inclui cabeçalho na imagem com o nome do "programa".
- 2025 10 22 Versão 0.0.3: Ajustes para montar pacote executavel.
"""

from PIL import Image, ImageTk
import tkinter, ctypes, os, sys


def resource_path(relative_path):
    try:
        # precisa pro PyInstaller quando monta o pacote
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Vamos mostrar a imagem por 3 segundos
def show_splash(duration=3000):
    # Obter as dimensões da tela
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    # Criar a janela principal
    janela = tkinter.Tk()
    # Remove a barra de título e bordas, afinal de contas é uma splash screen
    janela.overrideredirect(True)  

    # Carregar e redimensionar a imagem
    image = Image.open(resource_path("logo.png"))
    image = image.resize((300, 300))  
    photo = ImageTk.PhotoImage(image)

    # Fala qual programa esta rodando 
    texto_label = tkinter.Label(janela, text="Detetive B8", font=("Arial", 8, "bold"), fg="black")
    texto_label.pack(anchor="nw", padx=1, pady=1)  # Posiciona no canto superior esquerdo com margem

    # Precisa de um label para exibir a imagem
    label = tkinter.Label(janela, image=photo, bg='white')
    label.pack()

    # Calcular a posição para centralizar a janela
    window_width = photo.width()
    window_height = photo.height() + texto_label.winfo_reqheight()  # Inclui a altura do texto
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    # Posicionar a janela no centro da tela
    janela.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Função para fechar a janela 
    def close_window():
        janela.destroy()

    janela.after(duration, close_window)
    janela.mainloop()

######################## Main ################################
if __name__ == "__main__":
    show_splash()