import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Definir diretórios
input_dir = r"C:\DSSResumo\RESUMOFINAL"
output_dir = r"C:\DSSResumo\RESUMOFINAL\GRAFICOSNOVOS\boxplot_por_transformador"

# Limites PRODIST
lim_adequada_inf = 0.92
lim_adequada_sup = 1.05
lim_precaria_inf = 0.87
lim_precaria_sup = 1.06

# Criar diretório de saída se não existir
os.makedirs(output_dir, exist_ok=True)

# Lista de transformadores
transformadores = ['34631299', '34705676', '34693896', '90199814', '34569437',
                   '101428666', '34784390', '34611212', '91402190', '34685435',
                   '34633937', '34622044', '34629647', '86683110', '34623374']

# Lista de cenários
scenarios = []
for gd in [0, 25, 50, 75, 100]:
    for ev in [0, 25, 50, 75, 100]:
        scenarios.append(f"GD{gd}-EV{ev}")

# Função para obter dados de tensão para todos os cenários
def get_voltage_data(transformer_id):
    voltage_data = {}
    
    for scenario in scenarios:
        file_path = os.path.join(input_dir, f"{scenario}_pu_summary.csv")
        
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            continue
        
        # Ler o CSV
        df = pd.read_csv(file_path)
        
        # Colunas de tensão para o transformador
        min_col = f"{transformer_id}_V_PU_Min"
        avg_col = f"{transformer_id}_V_PU_Avg"
        max_col = f"{transformer_id}_V_PU_Max"
        
        # Verificar se as colunas existem
        if min_col not in df.columns or avg_col not in df.columns or max_col not in df.columns:
            print(f"Colunas de tensão para {transformer_id} não encontradas em {scenario}")
            continue
        
        # Armazenar os dados para este cenário
        voltage_data[scenario] = {
            'min': df[min_col].values,
            'avg': df[avg_col].values,
            'max': df[max_col].values
        }
    
    return voltage_data

# Processar cada transformador
for transformer in transformadores:
    print(f"Processando transformador {transformer}...")
    
    # Criar diretório para este transformador
    transformer_dir = os.path.join(output_dir, transformer)
    os.makedirs(transformer_dir, exist_ok=True)
    
    # Obter dados de tensão
    voltage_data = get_voltage_data(transformer)
    
    if not voltage_data:
        print(f"Nenhum dado encontrado para o transformador {transformer}")
        continue
    
    # Preparar dados para boxplot
    boxplot_data = []
    
    for scenario in scenarios:
        if scenario in voltage_data:
            # Concatenar todos os valores (min, avg, max) para boxplot
            all_values = np.concatenate([
                voltage_data[scenario]['min'],
                voltage_data[scenario]['avg'],
                voltage_data[scenario]['max']
            ])
            
            # Adicionar dados para este cenário
            for value in all_values:
                boxplot_data.append({
                    'Cenário': scenario,
                    'Tensão (p.u.)': value
                })
    
    # Converter para DataFrame
    df_boxplot = pd.DataFrame(boxplot_data)
    
    # Criar figura
    plt.figure(figsize=(15, 8))
    
    # Criar boxplot
    ax = sns.boxplot(x='Cenário', y='Tensão (p.u.)', data=df_boxplot)
    
    # Adicionar linhas de referência PRODIST
    plt.axhline(y=lim_adequada_inf, color='black', linestyle='--', label='Limite Adequada (0.92 p.u.)')
    plt.axhline(y=lim_adequada_sup, color='black', linestyle='--', label='Limite Adequada (1.05 p.u.)')
    plt.axhline(y=lim_precaria_inf, color='gray', linestyle=':', label='Limite Precária (0.87 p.u.)')
    plt.axhline(y=lim_precaria_sup, color='gray', linestyle=':', label='Limite Precária (1.06 p.u.)')
    
    # Configurar título e rótulos
    plt.title(f'Distribuição de Tensão - Transformador {transformer}', fontsize=14)
    plt.xlabel('Cenário', fontsize=12)
    plt.ylabel('Tensão (p.u.)', fontsize=12)
    plt.xticks(rotation=90)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Adicionar legenda
    plt.legend()
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar figura
    output_path = os.path.join(transformer_dir, f'boxplot_tensao_{transformer}.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Gráfico salvo em: {output_path}")

print("Todos os gráficos foram gerados com sucesso!")
