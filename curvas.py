import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Criar diretório de saída se não existir
output_dir = r"C:\DSSResumo\RESUMOFINAL\GRAFICOSNOVOS\curvas"
os.makedirs(output_dir, exist_ok=True)

# Definir dados para a curva de geração solar (96 pontos para 24 horas)
solar_curve = [
    # 0h às 5h45 (24 pontos) - Sem geração solar
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
    
    # 6h às 9h (12 pontos) - Aumento gradual pela manhã
    0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85,
    
    # 9h às 15h (24 pontos) - Período de maior geração
    0.90, 0.92, 0.94, 0.96, 0.97, 0.98, 0.99, 1.00, 1.00, 1.00, 0.99, 0.98,
    0.97, 0.96, 0.95, 0.94, 0.93, 0.92, 0.91, 0.90, 0.88, 0.86, 0.84, 0.82,
    
    # 15h às 18h (12 pontos) - Declínio gradual ao final do dia
    0.80, 0.75, 0.70, 0.60, 0.50, 0.40, 0.30, 0.20, 0.15, 0.10, 0.05, 0.00,
    
    # 18h15 às 23h45 (24 pontos) - Sem geração solar
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00
]

# Criar um array de horários para o eixo X (24 horas em intervalos de 15 minutos)
start_time = datetime(2025, 1, 1, 0, 0)  # Data fictícia
time_points = [start_time + timedelta(minutes=15*i) for i in range(96)]

# Criar as curvas EV de forma totalmente explícita
# Curva 1: 8 horas de carga começando às 19h, reduzindo para 0.7 pu das 1h às 3h
ev_curve1 = np.zeros(96)

# Preencher valores hora a hora explicitamente
for i in range(96):
    time = start_time + timedelta(minutes=15*i)
    hour = time.hour
    
    # 19h-23h: carga total (1.0)
    if 19 <= hour < 24:
        ev_curve1[i] = 1.0
    # 0h-1h: carga total (1.0)
    elif 0 <= hour < 1:
        ev_curve1[i] = 1.0
    # 1h-3h: carga reduzida (0.7)
    elif 1 <= hour < 3:
        ev_curve1[i] = 0.7
    else:
        ev_curve1[i] = 0.0

# Curva 2: 12 horas de carga começando às 16h, reduzindo para 0.7 pu das 0h às 4h
ev_curve2 = np.zeros(96)

# Preencher valores hora a hora explicitamente
for i in range(96):
    time = start_time + timedelta(minutes=15*i)
    hour = time.hour
    
    # 16h-23h: carga total (1.0)
    if 16 <= hour < 24:
        ev_curve2[i] = 1.0
    # 0h-4h: carga reduzida (0.7)
    elif 0 <= hour < 4:
        ev_curve2[i] = 0.7
    else:
        ev_curve2[i] = 0.0

# Curva 3: 6 horas de carga começando ao meio-dia, sempre 1.0 pu
ev_curve3 = np.zeros(96)

# Preencher valores hora a hora explicitamente
for i in range(96):
    time = start_time + timedelta(minutes=15*i)
    hour = time.hour
    
    # 12h-18h: carga total (1.0)
    if 12 <= hour < 18:
        ev_curve3[i] = 1.0
    else:
        ev_curve3[i] = 0.0

# 1. Criar gráfico para a curva de geração solar
plt.figure(figsize=(12, 6))
plt.plot(time_points, solar_curve, 'r-', linewidth=2.5)
plt.title('Curva de Geração Solar (24 horas)', fontsize=14)
plt.ylabel('Geração Solar (p.u.)', fontsize=12)
plt.xlabel('Hora do Dia', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.ylim(0, 1.05)

# Formatar eixo X
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
plt.gcf().autofmt_xdate(rotation=0, ha='center')
plt.gca().set_xlim(time_points[0], time_points[-1])

# Salvar figura
solar_output_path = os.path.join(output_dir, "curva_geracao_solar.png")
plt.savefig(solar_output_path, dpi=300)
plt.close()
print(f"Gráfico da curva solar salvo em: {solar_output_path}")

# 2. Criar gráfico para as curvas de carregamento EV
plt.figure(figsize=(12, 6))

# Plotar curvas
plt.plot(time_points, ev_curve1, 'b-', linewidth=2.5, label='Curva 1: 8h carga (19h-3h)')
plt.plot(time_points, ev_curve2, 'g-', linewidth=2.5, label='Curva 2: 12h carga (16h-4h)')
plt.plot(time_points, ev_curve3, 'r-', linewidth=2.5, label='Curva 3: 6h carga (12h-18h)')

plt.title('Curvas de Carregamento de Veículos Elétricos (24 horas)', fontsize=14)
plt.ylabel('Potência de Carregamento (p.u.)', fontsize=12)
plt.xlabel('Hora do Dia', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.ylim(0, 1.05)

# Posicionar a legenda na parte superior direita para não sobrepor o gráfico
plt.legend(loc='upper right', fontsize=10)

# Formatar eixo X
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
plt.gcf().autofmt_xdate(rotation=0, ha='center')
plt.gca().set_xlim(time_points[0], time_points[-1])

# Ajustar layout
plt.tight_layout()

# Salvar figura
ev_output_path = os.path.join(output_dir, "curvas_carregamento_ev.png")
plt.savefig(ev_output_path, dpi=300)
plt.close()
print(f"Gráfico das curvas de carregamento EV salvo em: {ev_output_path}")

print("Todos os gráficos de curvas foram gerados com sucesso!")