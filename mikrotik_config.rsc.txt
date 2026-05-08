#-------------------------------------------------------------------------------
# PROJETO: IPS Automatizado com Python & MikroTik
# OBJETIVO: Configuração de Interfaces, NAT e Regras de Firewall para o Lab
# AUTOR: Hacker do Bem (GitHub Community)
#-------------------------------------------------------------------------------

/sys identity set name="RouterOS-IPS-Lab"

# 1. Configuração de Interfaces (Nomes conforme a topologia do VMware)
/interface set [ find default-name=ether1 ] name=ether1-BRIDGE-TERMUX
/interface set [ find default-name=ether2 ] name=ether2-HOSTONLY-KALI
/interface set [ find default-name=ether3 ] name=ether3-NAT-INTERNET

# 2. Endereçamento IP
# IP para comunicação com o Termux (Ajuste conforme o seu roteador físico)
/ip address add address=192.168.1.7/24 interface=ether1-BRIDGE-TERMUX
# IP do Gateway da rede do Kali
/ip address add address=10.0.0.1/24 interface=ether2-HOSTONLY-KALI
# IP para saída WAN (Via DHCP para facilitar)
/ip dhcp-client add interface=ether3-NAT-INTERNET disabled=no

# 3. Configuração de NAT (Masquerade para o Kali ter internet)
/ip firewall nat
add chain=srcnat out-interface=ether3-NAT-INTERNET action=masquerade comment="NAT: Saida para Internet"

# 4. Regras de Firewall (O "Coração" do IPS)
/ip firewall filter
# Esta regra bloqueia qualquer pacote vindo de IPs na lista negra
add chain=input src-address-list=BLOQUEIO_AUTOMATICO action=drop comment="IPS: Bloqueio de Invasores ao Roteador"
add chain=forward src-address-list=BLOQUEIO_AUTOMATICO action=drop comment="IPS: Bloqueio de Invasores para a Rede"

# 5. Ativação da API (Necessária para o Script Python)
/ip service set api port=8728 disabled=no
/ip service set api-ssl disabled=yes

# 6. Criação de Usuário Específico para a API (Opcional - Segurança)
/user group add name=api-group policy=read,write,api,!local,!telnet,!ssh,!ftp
/user add name=admin-api group=api-group password=suasenhaaqui comment="Usuario exclusivo para o script Python"

print "--- Configuracao aplicada com sucesso! ---"

#-------------------------------------------------------------------------------
# CONFIGURAÇÃO DE ROTA E DNS (Essencial para Internet)
#-------------------------------------------------------------------------------

# 1. Configuração de DNS
# Permite que o roteador e as máquinas da rede Host-Only resolvam nomes
/ip dns set servers=8.8.8.8,8.8.4.4 allow-remote-requests=yes

# 2. Configuração de Rota Default (Gateway)
# Substitua o gateway pelo IP da sua rede NAT (geralmente final .2 no VMware)
/ip route add gateway=192.168.x.2 distance=1 comment="Rota Default para Internet"

# 3. Reforço da Interface Bridge para Gerenciamento
# Garante que o Termux consiga alcançar o MikroTik pela rede física
/ip address add address=192.168.1.7/24 interface=ether1-BRIDGE-TERMUX comment="IP de Acesso via Termux"

# 4. Configuração de NAT Masquerade
# Necessário para que a rede Host-Only (Kali) navegue usando o IP da WAN
/ip firewall nat
add chain=srcnat out-interface=ether3-NAT-INTERNET action=masquerade comment="NAT para rede interna"