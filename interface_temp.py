import serial
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import serial.tools.list_ports
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SERIAL_PORT_PADRAO = 'COM6'
BAUD_RATE = 9600

EMAIL = 'cristhianmantenha60@gmail.com'
SENHA_APP = 'sdzx njnp vkdy uicm'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

arduino_serial = None
leitura_ativa = False
ultima_temperatura_lida = None


def atualizar_temperatura_na_interface(temp_valor):
    global ultima_temperatura_lida
    ultima_temperatura_lida = temp_valor
    lbl_temperatura.config(text=f"Temperatura: {temp_valor:.2f} °C")

def ler_dados_arduino():
    global arduino_serial, leitura_ativa
    
    if arduino_serial and arduino_serial.is_open:
        try:
            print("Iniciando sincronização da leitura serial...")
            arduino_serial.flushInput()
            for _ in range(20):
                line_raw = arduino_serial.readline()
                line = line_raw.decode('utf-8', errors='ignore').strip()
                if line.startswith("TEMP:"):
                    print("Sincronização bem-sucedida!")
                    break
                time.sleep(0.01)
        except Exception as e:
            print(f"Erro durante a sincronização serial: {e}")

    while leitura_ativa:
        if arduino_serial and arduino_serial.is_open:
            try:
                linha = arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                if linha.startswith("TEMP:"):
                    try:
                        temp_str = linha.split("TEMP:")[1].strip()
                        temperatura = float(temp_str)
                        root.after(10, lambda: atualizar_temperatura_na_interface(temperatura))
                    except ValueError:
                        print(f"Erro: Não foi possível converter temperatura de '{linha}'")
                
            except serial.SerialException as e:
                if leitura_ativa:
                    print(f"Erro na porta serial durante a leitura: {e}. Desconectando.")
                    root.after(0, messagebox.showerror, "Erro de Leitura", f"Problema na comunicação serial: {e}")
                    root.after(0, desconectar_arduino)
                break
            except UnicodeDecodeError as e:
                print(f"Erro de decodificação: {e}. Dados brutos: '{linha.encode('utf-8')}'")
            except Exception as e:
                print(f"Erro inesperado durante a leitura serial: {e}")
        time.sleep(0.1)

def conectar_arduino():
    global arduino_serial, leitura_ativa
    
    if arduino_serial is None or not arduino_serial.is_open:
        print("\nVerificando portas seriais disponíveis no sistema...")
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            status_label.config(text="Erro: Nenhuma porta!", foreground="red")
            messagebox.showerror("Erro de Conexão", "Nenhuma porta serial encontrada. Conecte o Arduino e tente novamente.")
            return
        
        print("Portas seriais detectadas:")
        for p in ports:
            print(f"  - {p.device} ({p.description})")
        
        porta_para_conectar = SERIAL_PORT_PADRAO
        if not any(p.device == porta_para_conectar for p in ports):
            if ports:
                messagebox.showwarning("Aviso de Porta", 
                                       f"A porta '{SERIAL_PORT_PADRAO}' não foi encontrada.\n"
                                       f"Tentando conectar à primeira porta disponível: '{ports[0].device}'")
                porta_para_conectar = ports[0].device
            else:
                status_label.config(text="Nenhuma porta para conectar!", foreground="red")
                return

        try:
            print(f"\nTentando abrir conexão com a porta: '{porta_para_conectar}'...")
            arduino_serial = serial.Serial(porta_para_conectar, BAUD_RATE, timeout=1)
            time.sleep(2)

            leitura_ativa = True
            
            status_label.config(text=f"Conectado a {porta_para_conectar}", foreground="green")
            btn_conectar.config(state=tk.DISABLED)
            btn_desconectar.config(state=tk.NORMAL)
            btn_enviar_email.config(state=tk.NORMAL)
            btn_salvar_txt.config(state=tk.NORMAL)
            
            if not any(t.name == 'serial_reader_thread' for t in threading.enumerate()):
                threading.Thread(target=ler_dados_arduino, daemon=True, name='serial_reader_thread').start()
            print("Conexão estabelecida com Arduino.")

        except serial.SerialException as e:
            status_label.config(text=f"Erro ao conectar: {e}", foreground="red")
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar à porta '{porta_para_conectar}'.")
            print(f"ERRO: Não foi possível conectar à porta '{porta_para_conectar}': {e}")
            arduino_serial = None

        except Exception as e:
            status_label.config(text=f"Erro Inesperado: {e}", foreground="red")
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado ao tentar conectar.\nDetalhes: {e}")
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
    btn_enviar_email.config(state=tk.DISABLED)
    btn_salvar_txt.config(state=tk.DISABLED)
    lbl_temperatura.config(text="Temperatura: -- °C")
    print("Desconectado com sucesso.")

def enviar_email():
    email_destino = entry_email_destino.get()
    
    if not email_destino or "@" not in email_destino:
        messagebox.showwarning("Erro", "Por favor, insira um endereço de e-mail de destino válido.")
        return
    if ultima_temperatura_lida is None:
        messagebox.showwarning("Aviso", "Nenhuma temperatura lida para enviar por e-mail.")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = email_destino
    msg['Subject'] = f"Relatório de Temperatura - {time.strftime('%d/%m/%Y %H:%M:%S')}"

    corpo_email = f"""
Prezado Cliente,

Este é um relatório automático da temperatura ambiente registrada pelo seu sensor.

Temperatura Atual: {ultima_temperatura_lida:.2f} °C
Data e Hora do Registro: {time.strftime('%d/%m/%Y %H:%M:%S')}
(Fuso Horário: {time.tzname[0]})

Atenciosamente,
Cristhian
    """
    msg.attach(MIMEText(corpo_email, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, SENHA_APP)
        text = msg.as_string()
        server.sendmail(EMAIL, email_destino, text)
        server.quit()
        messagebox.showinfo("Sucesso", f"E-mail com a temperatura enviado para {email_destino}!")
        print(f"E-mail enviado para {email_destino} com a temperatura {ultima_temperatura_lida:.2f}°C")
    except smtplib.SMTPAuthenticationError:
        messagebox.showerror("Erro de Autenticação", "Falha de autenticação. Verifique seu e-mail e SENHA DE APP.")
        print("Erro de autenticação. Verifique as credenciais.")
    except smtplib.SMTPException as e:
        messagebox.showerror("Erro de Envio", f"Erro ao enviar e-mail: {e}.\nVerifique as configurações SMTP, sua conexão à internet ou as permissões de envio do seu e-mail.")
        print(f"Erro SMTP ao enviar e-mail: {e}")
    except Exception as e:
        messagebox.showerror("Erro Geral", f"Ocorreu um erro inesperado ao enviar o e-mail: {e}")
        print(f"Erro inesperado no envio de email: {e}")

def salvar_registro_txt():
    if ultima_temperatura_lida is None:
        messagebox.showwarning("Aviso", "Nenhuma temperatura lida ainda para salvar.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")],
        title="Salvar Registro de Temperatura"
    )
    
    if not file_path:
        return

    try:
        timestamp = time.strftime('%d/%m/%Y %H:%M:%S')
        registro = f"[{timestamp}] Temperatura: {ultima_temperatura_lida:.2f} °C\n"
        
        with open(file_path, 'a') as f:
            f.write(registro)
        
        messagebox.showinfo("Sucesso", f"Registro salvo em:\n{file_path}")
        print(f"Registro salvo: {registro.strip()} em {file_path}")
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o registro: {e}")
        print(f"Erro ao salvar registro TXT: {e}")


root = tk.Tk()
root.title("Monitor e Registro de Temperatura")
root.geometry("450x450")
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

style.configure("Email.TButton", background="#007BFF", foreground="white")
style.map("Email.TButton", background=[('active', '#0056b3')])

style.configure("Save.TButton", background="#8B4513", foreground="white")
style.map("Save.TButton", background=[('active', '#69340f')])

style.configure("TLabel", font=("Helvetica", 12), background="#f0f0f0") 
style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), background="#f0f0f0") 
style.configure("Temp.TLabel", font=("Helvetica", 24, "bold"), foreground="#0056b3", background="#f0f0f0") 


main_frame = ttk.Frame(root, padding="20")
main_frame.pack(fill=tk.BOTH, expand=True)

lbl_titulo = ttk.Label(main_frame, text="Monitor e Registro de Temperatura", style="Title.TLabel")
lbl_titulo.pack(pady=10)

lbl_temperatura = ttk.Label(main_frame, text="Temperatura: -- °C", style="Temp.TLabel")
lbl_temperatura.pack(pady=10)

status_label = ttk.Label(main_frame, text="Arduino Não Conectado", font=("Helvetica", 10), foreground="red")
status_label.pack(pady=5)

button_frame = ttk.Frame(main_frame)
button_frame.pack(pady=10)

btn_conectar = ttk.Button(button_frame, text="Conectar", command=conectar_arduino, style="Connect.TButton")
btn_conectar.grid(row=0, column=0, padx=5)

btn_desconectar = ttk.Button(button_frame, text="Desconectar", command=desconectar_arduino, state=tk.DISABLED, style="Disconnect.TButton")
btn_desconectar.grid(row=0, column=1, padx=5)

controls_frame = ttk.LabelFrame(main_frame, text="Personalização", padding="10")
controls_frame.pack(pady=15, fill=tk.X, padx=10)

ttk.Label(controls_frame, text="E-mail de Destino:", background="#f0f0f0").pack(anchor='w')
entry_email_destino = ttk.Entry(controls_frame, width=40, font=("Helvetica", 10))
entry_email_destino.pack(pady=5, fill=tk.X)

btn_enviar_email = ttk.Button(controls_frame, text="Enviar E-mail com Temperatura", command=enviar_email, style="Email.TButton", state=tk.DISABLED)
btn_enviar_email.pack(pady=5)

btn_salvar_txt = ttk.Button(controls_frame, text="Salvar Registro (TXT)", command=salvar_registro_txt, style="Save.TButton", state=tk.DISABLED)
btn_salvar_txt.pack(pady=5)


def ao_fechar_janela():
    if messagebox.askokcancel("Sair", "Deseja realmente sair do Monitor de Temperatura?"):
        desconectar_arduino()
        root.destroy()

root.protocol("WM_DELETE_WINDOW", ao_fechar_janela)

root.mainloop()

if arduino_serial and arduino_serial.is_open:
    arduino_serial.close()
    print("Porta serial fechada.")