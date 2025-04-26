import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import datetime

def generate_scenario_comparison_graphs():
    """Gera gráficos comparativos entre cenários para cada transformador"""
    # Definir diretórios
    input_dir = r"C:\DSSResumo\RESUMOFINAL"
    output_dir = r"C:\DSSResumo\RESUMOFINAL\GRAFICOSAGRUP"
    
    # Garantir que o diretório de saída existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Limites PRODIST
    voltage_limits = {
        'adequate_min': 0.92,
        'adequate_max': 1.05,
        'precarious_min': 0.87,
        'precarious_max': 1.06
    }
    
    # Lista de cenários para processar
    scenarios = []
    for gd in [0, 25, 50, 75, 100]:
        for ev in [0, 25, 50, 75, 100]:
            scenarios.append(f"GD{gd}-EV{ev}")
    
    # Registrar tempo de início
    start_time = time.time()
    now = datetime.datetime.now()
    print(f"Geração de gráficos comparativos por cenário iniciada em: {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    # Carregar todos os dados dos cenários primeiro
    scenarios_data = {}
    for scenario in scenarios:
        csv_file = os.path.join(input_dir, f"{scenario}_pu_summary.csv")
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                scenarios_data[scenario] = df
                print(f"Carregado cenário: {scenario}")
            except Exception as e:
                print(f"Erro ao carregar {scenario}: {str(e)}")
    
    # Identificar todos os transformadores disponíveis em pelo menos um cenário
    all_transformers = set()
    for scenario, df in scenarios_data.items():
        for col in df.columns:
            if col.endswith('_V_PU_Max'):
                transformer_id = col.split('_V_PU_Max')[0]
                all_transformers.add(transformer_id)
    
    print(f"Identificados {len(all_transformers)} transformadores no total")
    
    # Organizar transformadores em ordem
    transformers = sorted(list(all_transformers))
    
    # Contador de gráficos gerados
    graphs_count = 0
    
    # Para cada transformador, gerar gráficos comparativos entre cenários
    for transformer in transformers:
        print(f"\nProcessando transformador: {transformer}")
        
        # Criar diretório para o transformador
        transformer_dir = os.path.join(output_dir, transformer)
        os.makedirs(transformer_dir, exist_ok=True)
        
        # 1. Gráfico comparativo de tensão máxima entre cenários
        generate_voltage_max_comparison(scenarios_data, transformer, scenarios, voltage_limits, transformer_dir)
        graphs_count += 1
        
        # 2. Gráfico comparativo de tensão mínima entre cenários
        generate_voltage_min_comparison(scenarios_data, transformer, scenarios, voltage_limits, transformer_dir)
        graphs_count += 1
        
        # 3. Gráfico comparativo de corrente máxima entre cenários
        generate_current_max_comparison(scenarios_data, transformer, scenarios, transformer_dir)
        graphs_count += 1
        
        # 4. Gráfico 3D de GD, EV e tensão máxima
        generate_3d_voltage_plot(scenarios_data, transformer, transformer_dir)
        graphs_count += 1
        
        # 5. Gráfico 3D de GD, EV e corrente máxima
        generate_3d_current_plot(scenarios_data, transformer, transformer_dir)
        graphs_count += 1
    
    # Calcular tempo total
    total_elapsed = time.time() - start_time
    minutes = int(total_elapsed // 60)
    seconds = int(total_elapsed % 60)
    
    print("\n" + "=" * 60)
    print(f"Geração concluída em {minutes} minutos e {seconds} segundos")
    print(f"Total de gráficos gerados: {graphs_count}")
    print(f"Todos os gráficos foram salvos em: {output_dir}")
    print("=" * 60)

def generate_voltage_max_comparison(scenarios_data, transformer, scenarios, voltage_limits, output_dir):
    """
    Gera gráfico comparativo de tensão máxima entre cenários para um transformador
    
    Args:
        scenarios_data: Dicionário com os dados de todos os cenários
        transformer: ID do transformador
        scenarios: Lista de cenários
        voltage_limits: Limites de tensão do PRODIST
        output_dir: Diretório de saída
    """
    try:
        # Coletar valores máximos de tensão para cada cenário
        values = []
        valid_scenarios = []
        gd_values = []
        ev_values = []
        
        for scenario in scenarios:
            if scenario not in scenarios_data:
                continue
                
            df = scenarios_data[scenario]
            v_max_col = f"{transformer}_V_PU_Max"
            
            if v_max_col in df.columns:
                v_max = df[v_max_col].max()
                values.append(v_max)
                valid_scenarios.append(scenario)
                
                # Extrair valores GD e EV do nome do cenário
                gd = int(scenario.split('-')[0].replace('GD', ''))
                ev = int(scenario.split('-')[1].replace('EV', ''))
                gd_values.append(gd)
                ev_values.append(ev)
        
        if not values:
            print(f"  Sem dados de tensão máxima para o transformador {transformer}")
            return
        
        # Ordenar cenários pela combinação GD e EV
        sorted_indices = sorted(range(len(valid_scenarios)), 
                               key=lambda i: (gd_values[i], ev_values[i]))
        
        valid_scenarios = [valid_scenarios[i] for i in sorted_indices]
        values = [values[i] for i in sorted_indices]
        
        # Criar figura
        plt.figure(figsize=(16, 8))
        
        # Definir cores baseadas nos limites PRODIST
        colors = []
        for val in values:
            if val > voltage_limits['precarious_max']:
                colors.append('red')  # Crítica alta
            elif val > voltage_limits['adequate_max']:
                colors.append('orange')  # Precária alta
            else:
                colors.append('green')  # Adequada
        
        # Plotar barras
        bars = plt.bar(valid_scenarios, values, color=colors)
        
        # Adicionar valores nas barras
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, value + 0.005, 
                    f'{value:.3f}', ha='center', va='bottom', 
                    color='black', rotation=90, fontsize=8)
        
        # Adicionar linhas de limite PRODIST
        plt.axhline(y=voltage_limits['adequate_max'], color='black', linestyle='--', alpha=0.7, label='Adequada Máx (1.05 p.u.)')
        plt.axhline(y=voltage_limits['precarious_max'], color='gray', linestyle=':', alpha=0.7, label='Precária Máx (1.06 p.u.)')
        
        plt.xlabel('Cenário', color='black')
        plt.ylabel('Tensão Máxima (p.u.)', color='black')
        plt.title(f'Tensão Máxima por Cenário - Transformador {transformer}', color='black')
        plt.xticks(rotation=90)
        plt.grid(True, axis='y', alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        # Salvar figura
        plt.savefig(os.path.join(output_dir, f"{transformer}_tensao_maxima_cenarios.png"), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  Gerado gráfico de tensão máxima para o transformador {transformer}")
        
    except Exception as e:
        print(f"  Erro ao gerar gráfico de tensão máxima para {transformer}: {str(e)}")

def generate_voltage_min_comparison(scenarios_data, transformer, scenarios, voltage_limits, output_dir):
    """
    Gera gráfico comparativo de tensão mínima entre cenários para um transformador
    
    Args:
        scenarios_data: Dicionário com os dados de todos os cenários
        transformer: ID do transformador
        scenarios: Lista de cenários
        voltage_limits: Limites de tensão do PRODIST
        output_dir: Diretório de saída
    """
    try:
        # Coletar valores mínimos de tensão para cada cenário
        values = []
        valid_scenarios = []
        gd_values = []
        ev_values = []
        
        for scenario in scenarios:
            if scenario not in scenarios_data:
                continue
                
            df = scenarios_data[scenario]
            v_min_col = f"{transformer}_V_PU_Min"
            
            if v_min_col in df.columns:
                v_min = df[v_min_col].min()
                values.append(v_min)
                valid_scenarios.append(scenario)
                
                # Extrair valores GD e EV do nome do cenário
                gd = int(scenario.split('-')[0].replace('GD', ''))
                ev = int(scenario.split('-')[1].replace('EV', ''))
                gd_values.append(gd)
                ev_values.append(ev)
        
        if not values:
            print(f"  Sem dados de tensão mínima para o transformador {transformer}")
            return
        
        # Ordenar cenários pela combinação GD e EV
        sorted_indices = sorted(range(len(valid_scenarios)), 
                               key=lambda i: (gd_values[i], ev_values[i]))
        
        valid_scenarios = [valid_scenarios[i] for i in sorted_indices]
        values = [values[i] for i in sorted_indices]
        
        # Criar figura
        plt.figure(figsize=(16, 8))
        
        # Definir cores baseadas nos limites PRODIST
        colors = []
        for val in values:
            if val < voltage_limits['precarious_min']:
                colors.append('red')  # Crítica baixa
            elif val < voltage_limits['adequate_min']:
                colors.append('orange')  # Precária baixa
            else:
                colors.append('green')  # Adequada
        
        # Plotar barras
        bars = plt.bar(valid_scenarios, values, color=colors)
        
        # Adicionar valores nas barras
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, value + 0.005, 
                    f'{value:.3f}', ha='center', va='bottom', 
                    color='black', rotation=90, fontsize=8)
        
        # Adicionar linhas de limite PRODIST
        plt.axhline(y=voltage_limits['adequate_min'], color='black', linestyle='--', alpha=0.7, label='Adequada Mín (0.92 p.u.)')
        plt.axhline(y=voltage_limits['precarious_min'], color='gray', linestyle=':', alpha=0.7, label='Precária Mín (0.87 p.u.)')
        
        plt.xlabel('Cenário', color='black')
        plt.ylabel('Tensão Mínima (p.u.)', color='black')
        plt.title(f'Tensão Mínima por Cenário - Transformador {transformer}', color='black')
        plt.xticks(rotation=90)
        plt.grid(True, axis='y', alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        # Salvar figura
        plt.savefig(os.path.join(output_dir, f"{transformer}_tensao_minima_cenarios.png"), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  Gerado gráfico de tensão mínima para o transformador {transformer}")
        
    except Exception as e:
        print(f"  Erro ao gerar gráfico de tensão mínima para {transformer}: {str(e)}")

def generate_current_max_comparison(scenarios_data, transformer, scenarios, output_dir):
    """
    Gera gráfico comparativo de corrente máxima entre cenários para um transformador
    
    Args:
        scenarios_data: Dicionário com os dados de todos os cenários
        transformer: ID do transformador
        scenarios: Lista de cenários
        output_dir: Diretório de saída
    """
    try:
        # Coletar valores máximos de corrente para cada cenário
        values = []
        valid_scenarios = []
        gd_values = []
        ev_values = []
        
        for scenario in scenarios:
            if scenario not in scenarios_data:
                continue
                
            df = scenarios_data[scenario]
            i_max_col = f"{transformer}_I_PU_Max"
            
            if i_max_col in df.columns:
                i_max = df[i_max_col].max()
                values.append(i_max)
                valid_scenarios.append(scenario)
                
                # Extrair valores GD e EV do nome do cenário
                gd = int(scenario.split('-')[0].replace('GD', ''))
                ev = int(scenario.split('-')[1].replace('EV', ''))
                gd_values.append(gd)
                ev_values.append(ev)
        
        if not values:
            print(f"  Sem dados de corrente máxima para o transformador {transformer}")
            return
        
        # Ordenar cenários pela combinação GD e EV
        sorted_indices = sorted(range(len(valid_scenarios)), 
                               key=lambda i: (gd_values[i], ev_values[i]))
        
        valid_scenarios = [valid_scenarios[i] for i in sorted_indices]
        values = [values[i] for i in sorted_indices]
        
        # Criar figura
        plt.figure(figsize=(16, 8))
        
        # Definir cores baseadas na corrente nominal
        colors = ['red' if val > 1.0 else 'green' for val in values]
        
        # Plotar barras
        bars = plt.bar(valid_scenarios, values, color=colors)
        
        # Adicionar valores nas barras
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, value + 0.02, 
                    f'{value:.3f}', ha='center', va='bottom', 
                    color='black', rotation=90, fontsize=8)
        
        # Adicionar linha de corrente nominal
        plt.axhline(y=1.0, color='black', linestyle='--', alpha=0.7, label='Corrente Nominal (1.0 p.u.)')
        
        plt.xlabel('Cenário', color='black')
        plt.ylabel('Corrente Máxima (p.u.)', color='black')
        plt.title(f'Corrente Máxima por Cenário - Transformador {transformer}', color='black')
        plt.xticks(rotation=90)
        plt.grid(True, axis='y', alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        # Salvar figura
        plt.savefig(os.path.join(output_dir, f"{transformer}_corrente_maxima_cenarios.png"), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  Gerado gráfico de corrente máxima para o transformador {transformer}")
        
    except Exception as e:
        print(f"  Erro ao gerar gráfico de corrente máxima para {transformer}: {str(e)}")

def generate_3d_voltage_plot(scenarios_data, transformer, output_dir):
    """
    Gera gráfico 3D de GD vs EV vs Tensão Máxima para um transformador
    
    Args:
        scenarios_data: Dicionário com os dados de todos os cenários
        transformer: ID do transformador
        output_dir: Diretório de saída
    """
    try:
        # Importar mplot3d para gráficos 3D
        from mpl_toolkits.mplot3d import Axes3D
        
        # Coletar dados para gráfico 3D
        gd_values = []
        ev_values = []
        voltage_values = []
        
        for scenario, df in scenarios_data.items():
            v_max_col = f"{transformer}_V_PU_Max"
            
            if v_max_col in df.columns:
                # Extrair valores GD e EV do nome do cenário
                gd = int(scenario.split('-')[0].replace('GD', ''))
                ev = int(scenario.split('-')[1].replace('EV', ''))
                
                v_max = df[v_max_col].max()
                
                gd_values.append(gd)
                ev_values.append(ev)
                voltage_values.append(v_max)
        
        if not voltage_values:
            print(f"  Sem dados suficientes para gráfico 3D de tensão para o transformador {transformer}")
            return
        
        # Criar figura 3D
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Criar um gráfico de dispersão 3D
        scatter = ax.scatter(gd_values, ev_values, voltage_values, c=voltage_values, 
                            cmap='RdYlGn_r', marker='o', s=100, alpha=0.8)
        
        # Adicionar uma barra de cores
        cbar = fig.colorbar(scatter, ax=ax, pad=0.1)
        cbar.set_label('Tensão Máxima (p.u.)', rotation=270, labelpad=20)
        
        # Rótulos dos eixos
        ax.set_xlabel('Nível de GD (%)')
        ax.set_ylabel('Nível de EV (%)')
        ax.set_zlabel('Tensão Máxima (p.u.)')
        
        # Título
        plt.title(f'Impacto de GD e EV na Tensão Máxima - Transformador {transformer}')
        
        # Salvar figura
        plt.savefig(os.path.join(output_dir, f"{transformer}_tensao_3d.png"), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  Gerado gráfico 3D de tensão para o transformador {transformer}")
        
    except Exception as e:
        print(f"  Erro ao gerar gráfico 3D de tensão para {transformer}: {str(e)}")

def generate_3d_current_plot(scenarios_data, transformer, output_dir):
    """
    Gera gráfico 3D de GD vs EV vs Corrente Máxima para um transformador
    
    Args:
        scenarios_data: Dicionário com os dados de todos os cenários
        transformer: ID do transformador
        output_dir: Diretório de saída
    """
    try:
        # Importar mplot3d para gráficos 3D
        from mpl_toolkits.mplot3d import Axes3D
        
        # Coletar dados para gráfico 3D
        gd_values = []
        ev_values = []
        current_values = []
        
        for scenario, df in scenarios_data.items():
            i_max_col = f"{transformer}_I_PU_Max"
            
            if i_max_col in df.columns:
                # Extrair valores GD e EV do nome do cenário
                gd = int(scenario.split('-')[0].replace('GD', ''))
                ev = int(scenario.split('-')[1].replace('EV', ''))
                
                i_max = df[i_max_col].max()
                
                gd_values.append(gd)
                ev_values.append(ev)
                current_values.append(i_max)
        
        if not current_values:
            print(f"  Sem dados suficientes para gráfico 3D de corrente para o transformador {transformer}")
            return
        
        # Criar figura 3D
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Criar um gráfico de dispersão 3D
        scatter = ax.scatter(gd_values, ev_values, current_values, c=current_values, 
                            cmap='RdYlGn_r', marker='o', s=100, alpha=0.8)
        
        # Adicionar uma barra de cores
        cbar = fig.colorbar(scatter, ax=ax, pad=0.1)
        cbar.set_label('Corrente Máxima (p.u.)', rotation=270, labelpad=20)
        
        # Rótulos dos eixos
        ax.set_xlabel('Nível de GD (%)')
        ax.set_ylabel('Nível de EV (%)')
        ax.set_zlabel('Corrente Máxima (p.u.)')
        
        # Título
        plt.title(f'Impacto de GD e EV na Corrente Máxima - Transformador {transformer}')
        
        # Salvar figura
        plt.savefig(os.path.join(output_dir, f"{transformer}_corrente_3d.png"), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  Gerado gráfico 3D de corrente para o transformador {transformer}")
        
    except Exception as e:
        print(f"  Erro ao gerar gráfico 3D de corrente para {transformer}: {str(e)}")

if __name__ == "__main__":
    print("GERAÇÃO DE GRÁFICOS COMPARATIVOS ENTRE CENÁRIOS")
    print("=" * 60)
    generate_scenario_comparison_graphs()
