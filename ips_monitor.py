import routeros_api
import time

# --- CONFIGURAÇÕES ---
HOST = '192.168.1.7' # Exemplo de ip 
USER = 'admin' # Exemplo de usario
PASS = '' 
LIMITE = 10 

print(f"--- Monitoramento Ativo em {HOST} ---")

connection = routeros_api.RouterOsApiPool(HOST, username=USER, password=PASS, plaintext_login=True)
api = connection.get_api()

try:
    while True:
        conexoes = api.get_resource('/ip/firewall/connection').get()
        # Pegamos a lista de quem já está bloqueado para não tentar repetir
        lista_bloqueados = api.get_resource('/ip/firewall/address-list').get()
        ips_na_lista = [item.get('address') for item in lista_bloqueados if item.get('list') == 'BLOQUEIO_AUTOMATICO']
        
        contador = {}

        for conn in conexoes:
            ip_origem = conn.get('src-address', '').split(':')[0]

            # Ignora IPs que não queremos bloquear (Gateway e conexões locais)
            if ip_origem in ['10.0.0.2', '127.0.0.1', '0.0.0.0', '192.168.1.1', '192.168.46.1']:
                continue

            if ip_origem.startswith('10.0.0'):
                contador[ip_origem] = contador.get(ip_origem, 0) + 1
                
                # Se atingiu o limite e NÃO está na lista ainda, bloqueia!
                if contador[ip_origem] >= LIMITE and ip_origem not in ips_na_lista:
                    print(f"!!! ATAQUE DETECTADO: Bloqueando {ip_origem} !!!")
                    try:
                        api.get_resource('/ip/firewall/address-list').add(
                            list='BLOQUEIO_AUTOMATICO',
                            address=ip_origem,
                            timeout='00:05:00'
                        )
                        # Adicionamos na nossa lista local para o loop atual não repetir
                        ips_na_lista.append(ip_origem)
                    except:
                        pass # Se der erro mesmo assim, ignora
        
        print("--- Varredura concluída. Aguardando... ---")
        time.sleep(3)

except KeyboardInterrupt:
    print("\nEncerrando...")
    connection.disconnect()
except Exception as e:
    print(f"\nErro inesperado: {e}")