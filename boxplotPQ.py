import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math

# Definir diretórios
input_dir = r"C:\DSSResumo\RESUMOFINAL"
powerflux_dir = r"C:\DSSResumo\RESUMOFINAL\POWERFLUX"
output_dir = r"C:\DSSResumo\RESUMOFINAL\GRAFICOSNOVOS\boxplot_por_transformador"

# Criar diretório de saída se não existir
os.makedirs(output_dir, exist_ok=True)

# Tensão nominal (fase-neutro)
tensao_nominal = 127  # V

# Potência nominal dos transformadores em kVA (trifásica)
trafo_kva = {
    '90199814': 75,
    '86683110': 112.5,
    '34569437': 112.5,
    '34611212': 112.5,
    '34622044': 75,
    '34623374': 112.5,
    '34629647': 112.5,
    '34631299': 75,
    '34633937': 75,
    '34685435': 75,
    '34693896': 112.5,
    '34705676': 45,
    '34784390': 75,
    '101428666': 75,
    '91402190': 112.5
}

# Lista de transformadores
transformadores = list(trafo_kva.keys())

# Lista de cenários
scenarios = []
for gd in [0, 25, 50, 75, 100]:
    for ev in [0, 25, 50, 75, 100]:
        scenarios.append(f"GD{gd}-EV{ev}")

# Calculando corrente nominal por fase
# Para um transformador trifásico: S = 3 * V * I => I = S / (3 * V)
# onde S é a potência aparente trifásica, V é a tensão fase-neutro, I é a corrente por fase
trafo_corrente_nominal = {}
for trafo_id, kva in trafo_kva.items():
    corrente_nominal = (kva * 1000) / (3 * tensao_nominal)  # Corrente nominal por fase em A
    trafo_corrente_nominal[trafo_id] = corrente_nominal

# Carregar a tabela de fator de potência
try:
    power_flow_path = os.path.join(powerflux_dir, "consolidated_transformer_power_flow.xlsx")
    power_flow_df = pd.read_excel(power_flow_path)
    power_flow_df.set_index('Transformer_ID', inplace=True)
except Exception as e:
    print(f"Erro ao carregar tabela de fluxo de potência: {e}")
    power_flow_df = None

# Função para calcular potências a partir dos dados de tensão e corrente
def calculate_power_data(transformer_id):
    p_data = {}
    q_data = {}
    
    for scenario in scenarios:
        file_path = os.path.join(input_dir, f"{scenario}_pu_summary.csv")
        
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            continue
        
        # Ler o CSV
        df = pd.read_csv(file_path)
        
        # Colunas para o transformador
        v_min_col = f"{transformer_id}_V_PU_Min"
        v_avg_col = f"{transformer_id}_V_PU_Avg"
        v_max_col = f"{transformer_id}_V_PU_Max"
        i_min_col = f"{transformer_id}_I_PU_Min"
        i_avg_col = f"{transformer_id}_I_PU_Avg"
        i_max_col = f"{transformer_id}_I_PU_Max"
        
        # Verificar se as colunas existem
        required_cols = [v_min_col, v_avg_col, v_max_col, i_min_col, i_avg_col, i_max_col]
        if not all(col in df.columns for col in required_cols):
            print(f"Algumas colunas para {transformer_id} não encontradas em {scenario}")
            continue
        
        # Obter fator de potência para este cenário
        try:
            pf_col = f"{scenario}_PF"
            power_factor = power_flow_df.loc[int(transformer_id), pf_col]
        except Exception as e:
            print(f"Erro ao obter fator de potência para {transformer_id} no cenário {scenario}: {e}")
            power_factor = 0.92  # Valor padrão se não conseguir obter
        
        # Calcular corrente nominal para este transformador
        i_nominal = trafo_corrente_nominal[transformer_id]
        
        # Calcular potências para cada ponto no tempo
        p_values = []
        q_values = []
        
        for idx, row in df.iterrows():
            # Obter valores de tensão e corrente em p.u.
            v_pu = row[v_max_col]  # Usando valores máximos para pior caso
            i_pu = row[i_max_col]
            
            # Converter para valores reais
            v_real = v_pu * tensao_nominal  # Tensão fase-neutro em V
            i_real = i_pu * i_nominal       # Corrente por fase em A
            
            # Calcular potência aparente monofásica (VA)
            s_mono = v_real * i_real
            
            # Calcular potência trifásica total (assumindo sistema equilibrado)
            s_tri = 3 * s_mono / 1000  # Convertendo para kVA
            
            # Calcular P (kW) e Q (kVAR) trifásicos
            p_tri = s_tri * power_factor
            q_tri = s_tri * math.sin(math.acos(power_factor))
            
            p_values.append(p_tri)
            q_values.append(q_tri)
        
        p_data[scenario] = p_values
        q_data[scenario] = q_values
    
    return p_data, q_data

# Processar cada transformador
for transformer in transformadores:
    print(f"Processando transformador {transformer}...")
    
    # Criar diretório para este transformador
    transformer_dir = os.path.join(output_dir, transformer)
    os.makedirs(transformer_dir, exist_ok=True)
    
    # Calcular potências
    p_data, q_data = calculate_power_data(transformer)
    
    if not p_data or not q_data:
        print(f"Nenhum dado encontrado para o transformador {transformer}")
        continue
    
    # Preparar dados para boxplots de P (kW) e Q (kVAR)
    p_boxplot_data = []
    q_boxplot_data = []
    
    for scenario in scenarios:
        if scenario in p_data and scenario in q_data:
            # Adicionar dados para este cenário
            for p_value in p_data[scenario]:
                p_boxplot_data.append({
                    'Cenário': scenario,
                    'Potência Ativa (kW)': p_value
                })
            
            for q_value in q_data[scenario]:
                q_boxplot_data.append({
                    'Cenário': scenario,
                    'Potência Reativa (kVAR)': q_value
                })
    
    # Converter para DataFrames
    df_p_boxplot = pd.DataFrame(p_boxplot_data)
    df_q_boxplot = pd.DataFrame(q_boxplot_data)
    
    # Criar gráfico para P (kW)
    plt.figure(figsize=(15, 8))
    ax = sns.boxplot(x='Cenário', y='Potência Ativa (kW)', data=df_p_boxplot)
    plt.title(f'Distribuição de Potência Ativa - Transformador {transformer} ({trafo_kva[transformer]} kVA)', fontsize=14)
    plt.xlabel('Cenário', fontsize=12)
    plt.ylabel('Potência Ativa (kW)', fontsize=12)
    plt.xticks(rotation=90)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    output_path = os.path.join(transformer_dir, f'boxplot_potencia_ativa_{transformer}.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    # Criar gráfico para Q (kVAR)
    plt.figure(figsize=(15, 8))
    ax = sns.boxplot(x='Cenário', y='Potência Reativa (kVAR)', data=df_q_boxplot)
    plt.title(f'Distribuição de Potência Reativa - Transformador {transformer} ({trafo_kva[transformer]} kVA)', fontsize=14)
    plt.xlabel('Cenário', fontsize=12)
    plt.ylabel('Potência Reativa (kVAR)', fontsize=12)
    plt.xticks(rotation=90)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    output_path = os.path.join(transformer_dir, f'boxplot_potencia_reativa_{transformer}.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Gráficos de potência salvos para o transformador {transformer}")

print("Todos os gráficos de potência foram gerados com sucesso!")