import serial
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import serial.tools.list_ports

SERIAL_PORT = 'COM3'
BAUD_RATE = 9600 # mesmo valor do Serial.begin()

arduino_serial = None
leitura_ativa = False


def conectar_arduino():
    global arduino_serial, leitura_ativa

    # lista as portas disponíveis
    print("Portas seriais disponíveis:")
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("Nenhuma porta serial encontrada.")
        status_label.config(text="Erro: Nenhuma porta!", foreground="red")
        messagebox.showerror("Erro de Conexão", "Nenhuma porta serial encontrada. Verifique as conexões do Arduino.")
        return
    
    for p in ports:
        print(f"  - {p.device} ({p.description})")

    # Verifica se a porta configurada existe, se não usa a primeira
    porta_final = SERIAL_PORT
    if not any(p.device == SERIAL_PORT for p in ports):
        messagebox.showwarning("Aviso de Porta", f"A porta '{SERIAL_PORT}' não foi encontrada. Tentando a primeira porta disponível: {ports[0].device}")
        porta_final = ports[0].device

    try:
        arduino_serial = serial.Serial(porta_final, BAUD_RATE, timeout=1)
        time.sleep(2)
        leitura_ativa = True
        
        status_label.config(text=f"Conectado a {porta_final}", foreground="green")
        btn_conectar.config(state=tk.DISABLED)
        btn_desconectar.config(state=tk.NORMAL)
        
        read_thread = threading.Thread(target=ler_dados_arduino, daemon=True)
        read_thread.start()
        print(f"Conexão estabelecida com {porta_final}.")

    except serial.SerialException as e:
        status_label.config(text=f"Erro de Conexão: {e}", foreground="red")
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao Arduino na porta {porta_final}.\n{e}")
        print(f"ERRO DE CONEXÃO: {e}")
    except Exception as e:
        status_label.config(text=f"Erro Inesperado: {e}", foreground="red")
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado ao conectar.\n{e}")
        print(f"ERRO INESPERADO: {e}")

def desconectar_arduino():
    global arduino_serial, leitura_ativa
    leitura_ativa = False
    
    if arduino_serial and arduino_serial.is_open:
        try:
            arduino_serial.close()
            print("Comunicação serial encerrada.")
        except serial.SerialException as e:
            print(f"Erro ao fechar a porta serial: {e}")
        except Exception as e:
            print(f"Erro inesperado ao desconectar: {e}")

    status_label.config(text="Arduino Não Conectado", foreground="red")
    btn_conectar.config(state=tk.NORMAL)
    btn_desconectar.config(state=tk.DISABLED)
    lbl_temperatura.config(text="Temperatura: -- °C")
    print("Desconectado com sucesso.")

def ler_dados_arduino():
    global leitura_ativa
    while leitura_ativa:
        if arduino_serial and arduino_serial.is_open:
            try:
                line = arduino_serial.readline().decode('utf-8').strip()
                
                if line.startswith("TEMP:"):
                    try:
                        temp_str = line.split(":")[1].strip()
                        temperature = float(temp_str)
                        
                        root.after(10, lambda: lbl_temperatura.config(text=f"Temperatura: {temperature:.2f} °C"))
                    except ValueError:
                        print(f"Erro: Não foi possível converter temperatura de '{line}'")
                
            except serial.SerialException as e:
                # Se a porta foi desconectada durante a leitura
                if leitura_ativa:
                    print(f"Erro durante a leitura serial (desconexão?): {e}")
                    root.after(0, messagebox.showerror, "Erro de Leitura", f"Problema na comunicação serial: {e}")
                    root.after(0, desconectar_arduino)
                break
            except Exception as e:
                print(f"Erro inesperado durante a leitura: {e}")
        time.sleep(0.1)


root = tk.Tk()
root.title("Monitor de Temperatura NTC")
root.geometry("400x250")
root.resizable(False, False)

style = ttk.Style()
style.theme_use('clam') 
style.configure("TFrame", background="#f0f0f0")
style.configure("TButton", font=("Helvetica", 10), padding=5, background="#e0e0e0", foreground="black")
style.map("TButton", background=[('active', '#c0c0c0')])

style.configure("Connect.TButton", background="#4CAF50", foreground="white")
style.map("Connect.TButton", background=[('active', '#45a049')])

style.configure("Disconnect.TButton", background="#FF4C4C", foreground="white")
style.map("Disconnect.TButton", background=[('active', '#e04040')])

style.configure("TLabel", font=("Helvetica", 12), background="#f0f0f0")
style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), background="#f0f0f0")
style.configure("Temp.TLabel", font=("Helvetica", 24, "bold"), foreground="#0056b3", background="#f0f0f0") 


main_frame = ttk.Frame(root, padding="20 20 20 20")
main_frame.pack(fill=tk.BOTH, expand=True)

lbl_titulo = ttk.Label(main_frame, text="Monitor de Temperatura NTC", style="Title.TLabel")
lbl_titulo.pack(pady=10)

lbl_temperatura = ttk.Label(main_frame, text="Temperatura: -- °C", style="Temp.TLabel")
lbl_temperatura.pack(pady=20)

status_label = ttk.Label(main_frame, text="Arduino Não Conectado", font=("Helvetica", 10), foreground="red", background="#f0f0f0")
status_label.pack(pady=5)

button_frame = ttk.Frame(main_frame)
button_frame.pack(pady=10)

btn_conectar = ttk.Button(button_frame, text="Conectar", command=conectar_arduino, style="Connect.TButton")
btn_conectar.grid(row=0, column=0, padx=5)

btn_desconectar = ttk.Button(button_frame, text="Desconectar", command=desconectar_arduino, state=tk.DISABLED, style="Disconnect.TButton")
btn_desconectar.grid(row=0, column=1, padx=5)

def ao_fechar_janela():
    if messagebox.askokcancel("Sair", "Deseja realmente sair do Monitor de Temperatura?"):
        desconectar_arduino()
        root.destroy()

root.protocol("WM_DELETE_WINDOW", ao_fechar_janela)

root.mainloop()

if arduino_serial and arduino_serial.is_open:
    arduino_serial.close()
    print("Porta serial forçosamente fechada após mainloop.")