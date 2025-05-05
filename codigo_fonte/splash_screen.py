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

    # Precisa de um label para exibir a imagem
    label = tkinter.Label(janela, image=photo, bg='white')
    label.pack()

    # Calcular a posição para centralizar a janela
    window_width = photo.width()
    window_height = photo.height()
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
