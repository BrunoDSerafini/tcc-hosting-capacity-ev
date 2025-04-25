import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Definir diretórios
input_dir = r"C:\DSSResumo\RESUMOFINAL"
output_dir = r"C:\DSSResumo\RESUMOFINAL\GRAFICOSNOVOS\heatmaps"

# Criar diretório de saída se não existir
os.makedirs(output_dir, exist_ok=True)

# Lista de transformadores
transformadores = ['34631299', '34705676', '34693896', '90199814', '34569437',
                  '101428666', '34784390', '34611212', '91402190', '34685435',
                  '34633937', '34622044', '34629647', '86683110', '34623374']

# Valores de penetração em ordem crescente
penetracao_valores = [0, 25, 50, 75, 100]

# Limites PRODIST para tensão
lim_adequada_inf = 0.92
lim_adequada_sup = 1.05
lim_precaria_inf = 0.87
lim_precaria_sup = 1.06

# Função para extrair valores extremos e médios de tensão e corrente
def extrair_valores(transformador_id):
    # Inicializar dataframes com valores NaN
    tensao_max_df = pd.DataFrame(index=penetracao_valores, columns=penetracao_valores, dtype=float)
    tensao_min_df = pd.DataFrame(index=penetracao_valores, columns=penetracao_valores, dtype=float)
    tensao_avg_df = pd.DataFrame(index=penetracao_valores, columns=penetracao_valores, dtype=float)
    corrente_max_df = pd.DataFrame(index=penetracao_valores, columns=penetracao_valores, dtype=float)
    corrente_min_df = pd.DataFrame(index=penetracao_valores, columns=penetracao_valores, dtype=float)
    corrente_avg_df = pd.DataFrame(index=penetracao_valores, columns=penetracao_valores, dtype=float)
    
    for gd in penetracao_valores:
        for ev in penetracao_valores:
            scenario = f"GD{gd}-EV{ev}"
            file_path = os.path.join(input_dir, f"{scenario}_pu_summary.csv")
            
            try:
                df = pd.read_csv(file_path)
                
                # Colunas para o transformador
                v_min_col = f"{transformador_id}_V_PU_Min"
                v_avg_col = f"{transformador_id}_V_PU_Avg"
                v_max_col = f"{transformador_id}_V_PU_Max"
                i_min_col = f"{transformador_id}_I_PU_Min"
                i_avg_col = f"{transformador_id}_I_PU_Avg"
                i_max_col = f"{transformador_id}_I_PU_Max"
                
                # Verificar se as colunas existem
                colunas_necessarias = [v_min_col, v_avg_col, v_max_col, i_min_col, i_avg_col, i_max_col]
                if not all(col in df.columns for col in colunas_necessarias):
                    print(f"Colunas para {transformador_id} não encontradas em {scenario}")
                    continue
                
                # Extrair valores extremos e médios
                tensao_max_df.loc[gd, ev] = float(df[v_max_col].max())
                tensao_min_df.loc[gd, ev] = float(df[v_min_col].min())
                tensao_avg_df.loc[gd, ev] = float(df[v_avg_col].mean())
                corrente_max_df.loc[gd, ev] = float(df[i_max_col].max())
                corrente_min_df.loc[gd, ev] = float(df[i_min_col].min())
                corrente_avg_df.loc[gd, ev] = float(df[i_avg_col].mean())
                
            except Exception as e:
                print(f"Erro ao processar {scenario} para {transformador_id}: {e}")
    
    return tensao_max_df, tensao_min_df, tensao_avg_df, corrente_max_df, corrente_min_df, corrente_avg_df

# Função para criar um heatmap
def criar_heatmap(df, titulo, output_path, cmap, vmin=None, vmax=None, add_annotations=True):
    plt.figure(figsize=(10, 8))
    
    # Garantir que os dados sejam numéricos
    df_float = df.astype(float)
    
    # Ordenar o DataFrame para exibir os valores de penetração em ordem crescente (de baixo para cima)
    df_ordered = df_float.sort_index(ascending=False)
    
    # Criar heatmap
    ax = sns.heatmap(df_ordered, annot=add_annotations, fmt=".3f", cmap=cmap, 
                     vmin=vmin, vmax=vmax, cbar_kws={'label': titulo.split('-')[0].strip()})
    
    # Configurar título e rótulos
    plt.title(titulo, fontsize=14)
    plt.xlabel('Penetração de Veículos Elétricos (%)', fontsize=12)
    plt.ylabel('Penetração de Geração Distribuída (%)', fontsize=12)
    
    # Ajustar rótulos dos eixos
    ax.set_xticklabels(penetracao_valores)
    ax.set_yticklabels(reversed(penetracao_valores))  # Reverter a ordem dos rótulos
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Heatmap salvo em: {output_path}")

# Processar cada transformador
for transformador in transformadores:
    print(f"Processando transformador {transformador}...")
    
    # Criar diretório para este transformador
    transformador_dir = os.path.join(output_dir, transformador)
    os.makedirs(transformador_dir, exist_ok=True)
    
    # Extrair valores
    tensao_max_df, tensao_min_df, tensao_avg_df, corrente_max_df, corrente_min_df, corrente_avg_df = extrair_valores(transformador)
    
    # Criar heatmaps para tensão máxima
    criar_heatmap(
        tensao_max_df,
        f"Tensão Máxima - Transformador {transformador}",
        os.path.join(transformador_dir, f"heatmap_tensao_maxima_{transformador}.png"),
        "Reds",
        vmin=0.92,  # Começar no limite inferior adequado
        vmax=1.06   # Terminar no limite superior precário
    )
    
    # Criar heatmaps para tensão mínima
    criar_heatmap(
        tensao_min_df,
        f"Tensão Mínima - Transformador {transformador}",
        os.path.join(transformador_dir, f"heatmap_tensao_minima_{transformador}.png"),
        "Blues_r",  # Invertido para que valores mais baixos sejam mais vermelhos
        vmin=0.87,  # Começar no limite inferior precário
        vmax=1.05   # Terminar no limite superior adequado
    )
    
    # Criar heatmaps para tensão média
    criar_heatmap(
        tensao_avg_df,
        f"Tensão Média - Transformador {transformador}",
        os.path.join(transformador_dir, f"heatmap_tensao_media_{transformador}.png"),
        "YlOrRd",
        vmin=0.92,
        vmax=1.05
    )
    
    # Criar heatmaps para corrente máxima
    criar_heatmap(
        corrente_max_df,
        f"Corrente Máxima - Transformador {transformador}",
        os.path.join(transformador_dir, f"heatmap_corrente_maxima_{transformador}.png"),
        "Reds",
        vmin=0    # Começar em 0
    )
    
    # Criar heatmaps para corrente mínima
    criar_heatmap(
        corrente_min_df,
        f"Corrente Mínima - Transformador {transformador}",
        os.path.join(transformador_dir, f"heatmap_corrente_minima_{transformador}.png"),
        "Blues",
        vmin=0    # Começar em 0
    )
    
    # Criar heatmaps para corrente média
    criar_heatmap(
        corrente_avg_df,
        f"Corrente Média - Transformador {transformador}",
        os.path.join(transformador_dir, f"heatmap_corrente_media_{transformador}.png"),
        "YlOrRd",
        vmin=0
    )

print("Todos os heatmaps foram gerados com sucesso!")