import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Definir diretórios
input_dir = r"C:\DSSResumo\RESUMOFINAL"
output_dir = r"C:\DSSResumo\RESUMOFINAL\GRAFICOSNOVOS\violacoes_prodist"

# Criar diretório de saída se não existir
os.makedirs(output_dir, exist_ok=True)

# Lista de transformadores
transformadores = ['34631299', '34705676', '34693896', '90199814', '34569437',
                  '101428666', '34784390', '34611212', '91402190', '34685435',
                  '34633937', '34622044', '34629647', '86683110', '34623374']

# Valores de penetração
penetracao_valores = [0, 25, 50, 75, 100]

# Limites PRODIST para tensão
lim_adequada_inf = 0.92
lim_adequada_sup = 1.05
lim_precaria_inf = 0.87

# Lista de cenários
scenarios = []
for gd in penetracao_valores:
    for ev in penetracao_valores:
        scenarios.append(f"GD{gd}-EV{ev}")

# Cores para as categorias de violação
cores = {
    'Crítica Baixa': 'darkred',
    'Precária Baixa': 'orange',
    'Adequada': 'green'
}

# Função para classificar um valor de tensão
def classificar_tensao(valor):
    if valor < lim_precaria_inf:
        return 'Crítica Baixa'
    elif valor < lim_adequada_inf:
        return 'Precária Baixa'
    else:
        return 'Adequada'

# Função para analisar violações por cenário
def analisar_violacoes():
    # Dicionários para armazenar resultados
    violacoes_trafos = {scenario: {'Crítica Baixa': 0, 'Precária Baixa': 0, 'Adequada': 0} 
                        for scenario in scenarios}
    
    violacoes_amostras = {scenario: {'Crítica Baixa': 0, 'Precária Baixa': 0, 'Adequada': 0} 
                          for scenario in scenarios}
    
    total_trafos = len(transformadores)
    
    # Processar cada cenário
    for scenario in scenarios:
        file_path = os.path.join(input_dir, f"{scenario}_pu_summary.csv")
        
        try:
            df = pd.read_csv(file_path)
            
            # Contadores para este cenário
            trafos_por_categoria = {'Crítica Baixa': set(), 'Precária Baixa': set(), 'Adequada': set()}
            
            total_amostras = 0  # Contador para o número total de amostras
            amostras_por_categoria = {'Crítica Baixa': 0, 'Precária Baixa': 0, 'Adequada': 0}
            
            # Analisar cada transformador
            for trafo in transformadores:
                v_min_col = f"{trafo}_V_PU_Min"
                
                if v_min_col not in df.columns:
                    print(f"Coluna de tensão mínima para {trafo} não encontrada em {scenario}")
                    continue
                
                # Inicialmente, considere que o transformador está na categoria Adequada
                categoria_trafo = 'Adequada'
                
                # Para cada amostra (horário)
                for i in range(len(df)):
                    # Cada combinação de horário e transformador é UMA amostra
                    total_amostras += 1
                    
                    # Obtém o valor de tensão mínima
                    tensao_min = df[v_min_col].iloc[i]
                    
                    # Classifica o valor
                    categoria = classificar_tensao(tensao_min)
                    
                    # Adiciona à contagem de amostras
                    amostras_por_categoria[categoria] += 1
                    
                    # Atualizar categoria do transformador para a pior condição
                    if categoria != 'Adequada' and (
                        categoria_trafo == 'Adequada' or 
                        (categoria == 'Crítica Baixa' and categoria_trafo == 'Precária Baixa')
                    ):
                        categoria_trafo = categoria
                
                # Adicionar este transformador à sua categoria
                trafos_por_categoria[categoria_trafo].add(trafo)
            
            # Calcular percentuais de transformadores por categoria
            for categoria in violacoes_trafos[scenario].keys():
                num_trafos = len(trafos_por_categoria[categoria])
                violacoes_trafos[scenario][categoria] = (num_trafos / total_trafos) * 100
            
            # Verificar se a soma das amostras é igual ao total esperado
            soma_amostras = sum(amostras_por_categoria.values())
            if soma_amostras != total_amostras:
                print(f"AVISO: Soma de amostras ({soma_amostras}) diferente do total ({total_amostras}) para {scenario}")
            
            # Calcular percentuais de amostras por categoria
            for categoria in violacoes_amostras[scenario].keys():
                violacoes_amostras[scenario][categoria] = (amostras_por_categoria[categoria] / total_amostras) * 100
                
        except Exception as e:
            print(f"Erro ao processar {scenario}: {e}")
    
    return violacoes_trafos, violacoes_amostras

# Função para criar gráfico de barras empilhadas
def criar_grafico_violacoes(dados, titulo, output_path):
    categorias = ['Crítica Baixa', 'Precária Baixa', 'Adequada']
    
    # Preparar dados para o gráfico
    dados_por_categoria = {categoria: [] for categoria in categorias}
    
    for scenario in scenarios:
        for categoria in categorias:
            dados_por_categoria[categoria].append(dados[scenario][categoria])
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(18, 10))
    
    # Posições das barras
    posicoes = np.arange(len(scenarios))
    largura_barra = 0.70
    
    # Verificar se os dados somam 100% para cada cenário
    for i, scenario in enumerate(scenarios):
        soma = sum(dados[scenario].values())
        if abs(soma - 100) > 0.1:  # Tolerância de 0.1%
            print(f"AVISO: Soma dos percentuais para {scenario} é {soma}% (deveria ser 100%)")
    
    # Criar barras empilhadas
    bottom = np.zeros(len(scenarios))
    
    for categoria in categorias:
        ax.bar(posicoes, dados_por_categoria[categoria], largura_barra, label=categoria, 
               bottom=bottom, color=cores[categoria])
        
        # Adicionar rótulos percentuais nas barras (apenas se for maior que 1%)
        for i, valor in enumerate(dados_por_categoria[categoria]):
            if valor > 1.0:  # Apenas mostrar valores acima de 1%
                ax.text(i, bottom[i] + valor/2, f'{valor:.1f}%', 
                        ha='center', va='center', fontsize=9, 
                        color='black' if categoria == 'Adequada' else 'white')
        
        bottom += dados_por_categoria[categoria]
    
    # Configurar eixos e rótulos
    ax.set_title(titulo, fontsize=16)
    ax.set_xticks(posicoes)
    ax.set_xticklabels(scenarios, rotation=90)
    ax.set_ylabel('Porcentagem (%)', fontsize=14)
    ax.set_xlabel('Cenário', fontsize=14)
    ax.set_ylim(0, 100)  # Limitar o eixo Y para 100%
    
    # Adicionar legenda
    categorias_descricao = {
        'Crítica Baixa': 'Crítica Baixa (<0.87 p.u.)',
        'Precária Baixa': 'Precária Baixa (0.87-0.92 p.u.)',
        'Adequada': 'Adequada (0.92-1.05 p.u.)'
    }
    
    handles = [plt.Rectangle((0,0), 1, 1, color=cores[cat]) for cat in categorias]
    labels = [categorias_descricao[cat] for cat in categorias]
    
    ax.legend(handles, labels, loc='upper right', fontsize=10)
    
    # Adicionar grade
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Ajustar layout
    plt.tight_layout()
    
    # Salvar figura
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Gráfico salvo em: {output_path}")

# Executar análise de violações
print("Analisando violações PRODIST...")
violacoes_trafos, violacoes_amostras = analisar_violacoes()

# Criar gráficos
print("Criando gráficos de violações...")
criar_grafico_violacoes(
    violacoes_trafos,
    "Violações dos Valores PRODIST por Cenário - Porcentagem de Transformadores",
    os.path.join(output_dir, "violacoes_prodist_transformadores.png")
)

criar_grafico_violacoes(
    violacoes_amostras,
    "Violações dos Valores PRODIST por Cenário - Porcentagem de Amostras",
    os.path.join(output_dir, "violacoes_prodist_amostras.png")
)

print("Análise de violações PRODIST concluída com sucesso!")