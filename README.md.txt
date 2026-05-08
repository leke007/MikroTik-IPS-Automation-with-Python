🛠️ Cenário do Laboratório
Roteador: MikroTik RouterOS v7.x (VMware).

Atacante: Kali Linux (Metasploit/Nmap).

Controlador: Python 3.13 via Termux (Smartphone).

Interface de Comunicação: RouterOS API (Porta 8728).
🌐 Arquitetura de Conectividade (VMware Workstation)
Para que o script Python rodando no Android (Termux) pudesse controlar o roteador virtual e monitorar o ataque do Kali Linux, a estrutura de rede foi desenhada da seguinte forma:

1. Adaptador 1: Bridge (Comunicação com o Termux)
Função: Conecta a interface do MikroTik diretamente à rede Wi-Fi/LAN física.

Objetivo no Lab: Permitir que o script Python, executado via Termux no smartphone, alcance a API do MikroTik (porta 8728) através do IP da rede local.

2. Adaptador 2: Host-Only (Rede do Lab / Target)
Função: Cria um segmento de rede isolado dentro do VMware (10.0.0.0/24).

Objetivo no Lab: É nesta rede que o Kali Linux reside. O MikroTik atua como o Gateway (10.0.0.1), monitorando todo o tráfego que passa por esta interface para detectar varreduras do Nmap.

3. Adaptador 3: NAT (Saída para Internet)
Função: Prover conexão externa para as máquinas virtuais.

Objetivo no Lab: Utilizado para que o MikroTik e o Kali possam baixar pacotes e atualizações, saindo via src-nat (Masquerade) pela infraestrutura do hospedeiro.

🛠️ Configuração de Saída (Masquerade)
Para que o Kali Linux (na rede Host-Only) consiga navegar via NAT, a seguinte regra de firewall foi aplicada:,
/ip firewall nat
add chain=srcnat out-interface=ether-NAT action=masquerade comment="Saida para Internet"

⚙️ Configuração do MikroTik (Firewall)
Para o script funcionar, primeiro configurei o "gatilho" no Firewall do RouterOS. A regra abaixo bloqueia qualquer IP que entre na lista dinâmica criada pelo Python:

Bash
/ip firewall filter
add chain=input src-address-list=BLOQUEIO_AUTOMATICO action=drop comment="IPS: Bloqueio Automatico"

Bash
/ip service enable api
🐍 O Script Python (A Inteligência)
O script utiliza a biblioteca routeros_api para monitorar a tabela de conexões.

Lógica de Funcionamento:
Varredura: O script consulta o recurso /ip/firewall/connection a cada 1 segundo.

Contagem: Ele filtra conexões originadas na rede alvo (10.0.0.0/24) e conta quantas conexões simultâneas cada IP possui.

Decisão: Se um IP exceder o limite (ex: 5 conexões simultâneas), ele é classificado como um possível ataque de port scanning.

Ação: O script envia um comando para o MikroTik adicionando o IP infrator à address-list com um timeout de 5 minutos.

🚀 Script Base (Versão para Evolução)
Abaixo, a versão funcional que utilizei no laboratório. Ela inclui tratamento de exceções para evitar travamentos caso o IP já esteja bloqueado.

Python
import routeros_api
import time

# Conexão com o RouterOS
HOST = 'seu_ip_aqui'
USER = 'admin'
PASS = 'sua_senha'
LIMITE = 5

def monitor_ips():
    connection = routeros_api.RouterOsApiPool(HOST, username=USER, password=PASS, plaintext_login=True)
    api = connection.get_api()
    
    print("--- Sistema de Defesa Ativo ---")
    
    try:
        while True:
            conexoes = api.get_resource('/ip/firewall/connection').get()
            contador = {}
            
            # Pegamos quem já está bloqueado para evitar duplicidade
            lista_negra = api.get_resource('/ip/firewall/address-list').get()
            bloqueados = [i.get('address') for i in lista_negra if i.get('list') == 'BLOQUEIO_AUTOMATICO']

            for conn in conexoes:
                ip = conn.get('src-address', '').split(':')[0]
                
                # Regras de exceção (Gateway e Local)
                if ip.startswith('10.0.0') and ip != '10.0.0.2':
                    contador[ip] = contador.get(ip, 0) + 1
                    
                    if contador[ip] >= LIMITE and ip not in bloqueados:
                        print(f"ALERTA: Bloqueando {ip}!")
                        try:
                            api.get_resource('/ip/firewall/address-list').add(
                                list='BLOQUEIO_AUTOMATICO', address=ip, timeout='00:05:00'
                            )
                        except: pass
            time.sleep(1)
    except KeyboardInterrupt:
        connection.disconnect()

if __name__ == "__main__":
    monitor_ips()
📈 Próximos Passos (To-Do)
[ ] Implementar filtro por tcp-state para evitar falsos positivos de conexões antigas.

[ ] Adicionar logs em arquivo .log para auditoria posterior.

[ ] Criar uma interface gráfica (Dashboard) para visualizar os bloqueios.