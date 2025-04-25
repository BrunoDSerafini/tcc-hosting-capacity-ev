import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
from datetime import datetime, timedelta

def generate_individual_graphs():
    """
    Gera gráficos individuais para cada cenário e transformador
    """
    # Definir diretórios
    input_dir = r"C:\DSSResumo\RESUMOFINAL"
    output_dir = r"C:\DSSResumo\RESUMOFINAL\GRAFICOSINDIV"
    
    # Garantir que o diretório de saída existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Definir cenários
    scenarios = [
        'GD0-EV0', 'GD0-EV25', 'GD0-EV50', 'GD0-EV75', 'GD0-EV100',
        'GD25-EV0', 'GD25-EV25', 'GD25-EV50', 'GD25-EV75', 'GD25-EV100',
        'GD50-EV0', 'GD50-EV25', 'GD50-EV50', 'GD50-EV75', 'GD50-EV100',
        'GD75-EV0', 'GD75-EV25', 'GD75-EV50', 'GD75-EV75', 'GD75-EV100',
        'GD100-EV0', 'GD100-EV25', 'GD100-EV50', 'GD100-EV75', 'GD100-EV100'
    ]
    
    # Limites PRODIST
    voltage_limits = {
        'adequate_min': 0.92,
        'adequate_max': 1.05,
        'precarious_min': 0.87,
        'precarious_max': 1.06
    }
    
    # Processar cada cenário
    for scenario in scenarios:
        print(f"Processando cenário: {scenario}")
        
        # Definir caminho do arquivo CSV
        csv_file = os.path.join(input_dir, f"{scenario}_pu_summary.csv")
        
        # Verificar se o arquivo existe
        if not os.path.exists(csv_file):
            print(f"  Arquivo não encontrado: {csv_file}")
            continue
        
        try:
            # Ler arquivo CSV
            df = pd.read_csv(csv_file)
            
            # Criar diretório para o cenário
            scenario_dir = os.path.join(output_dir, scenario)
            os.makedirs(scenario_dir, exist_ok=True)
            
            # Identificar transformadores com base nas colunas
            transformers = []
            for col in df.columns:
                if col.endswith('_V_PU_Max'):
                    transformer_id = col.split('_V_PU_Max')[0]
                    transformers.append(transformer_id)
            
            # Gerar gráficos para cada transformador
            for transformer in transformers:
                # Gerar gráfico de tensão ao longo do dia
                generate_voltage_time_graph(df, transformer, scenario_dir, voltage_limits)
                
                # Gerar gráfico de corrente ao longo do dia
                generate_current_time_graph(df, transformer, scenario_dir)
            
            # Gerar gráficos de resumo para todos os transformadores
            generate_voltage_summary_graph(df, transformers, scenario, scenario_dir, voltage_limits)
            generate_current_summary_graph(df, transformers, scenario, scenario_dir)
            
            print(f"  Gráficos gerados para o cenário {scenario}")
            
        except Exception as e:
            print(f"  Erro ao processar cenário {scenario}: {str(e)}")

def generate_voltage_time_graph(df, transformer, output_dir, voltage_limits):
    """
    Gera gráfico de tensão por tempo para um transformador
    """
    try:
        # Extrair colunas de tensão
        v_min_col = f"{transformer}_V_PU_Min"
        v_avg_col = f"{transformer}_V_PU_Avg"
        v_max_col = f"{transformer}_V_PU_Max"
        
        # Verificar se todas as colunas existem
        if not all(col in df.columns for col in [v_min_col, v_avg_col, v_max_col]):
            print(f"    Colunas de tensão não encontradas para o transformador {transformer}")
            return
        
        # Converter hora para timestamp
        time_labels = []
        for hour in df['Hour']:
            total_minutes = hour * 15  # Cada unidade é 15 minutos
            hours = total_minutes // 60
            minutes = total_minutes % 60
            time_labels.append(f"{hours:02d}:{minutes:02d}")
        
        # Criar figura
        plt.figure(figsize=(14, 8))
        
        # Plotar linhas de tensão
        plt.plot(df['Hour'], df[v_min_col], color='green', linestyle='-', linewidth=2, label='Mínima')
        plt.plot(df['Hour'], df[v_avg_col], color='yellow', linestyle='-', linewidth=2, label='Média')
        plt.plot(df['Hour'], df[v_max_col], color='red', linestyle='-', linewidth=2, label='Máxima')
        
        # Adicionar linhas de limites PRODIST
        plt.axhline(y=voltage_limits['adequate_min'], color='black', linestyle='--', alpha=0.7, label='Adequada Mín (0.92 p.u.)')
        plt.axhline(y=voltage_limits['adequate_max'], color='black', linestyle='--', alpha=0.7, label='Adequada Máx (1.05 p.u.)')
        plt.axhline(y=voltage_limits['precarious_min'], color='gray', linestyle=':', alpha=0.7, label='Precária Mín (0.87 p.u.)')
        plt.axhline(y=voltage_limits['precarious_max'], color='gray', linestyle=':', alpha=0.7, label='Precária Máx (1.06 p.u.)')
        
        # Definir eixos X
        tick_positions = np.arange(0, len(df), 4)  # A cada 1 hora (4 intervalos de 15 min)
        tick_labels = [time_labels[i] for i in tick_positions]
        plt.xticks(tick_positions, tick_labels, rotation=45)
        
        # Adicionar rótulos e título
        plt.xlabel('Hora do Dia', color='black')
        plt.ylabel('Tensão (p.u.)', color='black')
        plt.title(f'Perfil de Tensão - Transformador {transformer}', color='black')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        # Salvar figura
        output_file = os.path.join(output_dir, f"V_PU_{transformer}_Daily.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"    Gráfico de tensão gerado para {transformer}")
        
    except Exception as e:
        print(f"    Erro ao gerar gráfico de tensão para {transformer}: {str(e)}")

def generate_current_time_graph(df, transformer, output_dir):
    """
    Gera gráfico de corrente por tempo para um transformador
    """
    try:
        # Extrair colunas de corrente
        i_min_col = f"{transformer}_I_PU_Min"
        i_avg_col = f"{transformer}_I_PU_Avg"
        i_max_col = f"{transformer}_I_PU_Max"
        
        # Verificar se todas as colunas existem
        if not all(col in df.columns for col in [i_min_col, i_avg_col, i_max_col]):
            print(f"    Colunas de corrente não encontradas para o transformador {transformer}")
            return
        
        # Converter hora para timestamp
        time_labels = []
        for hour in df['Hour']:
            total_minutes = hour * 15  # Cada unidade é 15 minutos
            hours = total_minutes // 60
            minutes = total_minutes % 60
            time_labels.append(f"{hours:02d}:{minutes:02d}")
        
        # Criar figura
        plt.figure(figsize=(14, 8))
        
        # Plotar linhas de corrente
        plt.plot(df['Hour'], df[i_min_col], color='green', linestyle='-', linewidth=2, label='Mínima')
        plt.plot(df['Hour'], df[i_avg_col], color='yellow', linestyle='-', linewidth=2, label='Média')
        plt.plot(df['Hour'], df[i_max_col], color='red', linestyle='-', linewidth=2, label='Máxima')
        
        # Adicionar linha de corrente nominal
        plt.axhline(y=1.0, color='black', linestyle='--', alpha=0.7, label='Corrente Nominal (1.0 p.u.)')
        
        # Definir eixos X
        tick_positions = np.arange(0, len(df), 4)  # A cada 1 hora (4 intervalos de 15 min)
        tick_labels = [time_labels[i] for i in tick_positions]
        plt.xticks(tick_positions, tick_labels, rotation=45)
        
        # Adicionar rótulos e título
        plt.xlabel('Hora do Dia', color='black')
        plt.ylabel('Corrente (p.u.)', color='black')
        plt.title(f'Perfil de Corrente - Transformador {transformer}', color='black')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        # Salvar figura
        output_file = os.path.join(output_dir, f"I_PU_{transformer}_Daily.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"    Gráfico de corrente gerado para {transformer}")
        
    except Exception as e:
        print(f"    Erro ao gerar gráfico de corrente para {transformer}: {str(e)}")

def generate_voltage_summary_graph(df, transformers, scenario, output_dir, voltage_limits):
    """
    Gera gráfico de resumo de tensão para todos os transformadores
    """
    try:
        # Dicionário para armazenar valores mínimos, médios e máximos
        transformer_voltages = {}
        
        # Extrair valores extremos para cada transformador
        for transformer in transformers:
            v_min_col = f"{transformer}_V_PU_Min"
            v_avg_col = f"{transformer}_V_PU_Avg"
            v_max_col = f"{transformer}_V_PU_Max"
            
            # Verificar se todas as colunas existem
            if not all(col in df.columns for col in [v_min_col, v_avg_col, v_max_col]):
                print(f"    Colunas de tensão não encontradas para o transformador {transformer}")
                continue
            
            # Encontrar valores mínimos, médios e máximos
            min_val = df[v_min_col].min()
            avg_val = df[v_avg_col].mean()
            max_val = df[v_max_col].max()
            
            transformer_voltages[transformer] = {
                'min': min_val,
                'avg': avg_val,
                'max': max_val
            }
        
        # Ordenar transformadores pelo valor máximo (decrescente)
        sorted_transformers = sorted(
            transformer_voltages.keys(),
            key=lambda t: transformer_voltages[t]['max'],
            reverse=True
        )
        
        # Extrair valores para plotagem
        min_values = [transformer_voltages[t]['min'] for t in sorted_transformers]
        avg_values = [transformer_voltages[t]['avg'] for t in sorted_transformers]
        max_values = [transformer_voltages[t]['max'] for t in sorted_transformers]
        
        # Criar figura
        plt.figure(figsize=(16, 10))
        
        # Definir largura da barra e posições
        bar_width = 0.25
        x = np.arange(len(sorted_transformers))
        
        # Plotar barras
        plt.bar(x - bar_width, min_values, bar_width, color='green', label='Mínima')
        plt.bar(x, avg_values, bar_width, color='yellow', label='Média')
        plt.bar(x + bar_width, max_values, bar_width, color='red', label='Máxima')
        
        # Adicionar valores nas barras
        for i, (min_val, avg_val, max_val) in enumerate(zip(min_values, avg_values, max_values)):
            plt.text(x[i] - bar_width, min_val + 0.01, f'{min_val:.3f}', ha='center', va='bottom',
                    color='black', fontsize=8, rotation=90)
            plt.text(x[i], avg_val + 0.01, f'{avg_val:.3f}', ha='center', va='bottom',
                    color='black', fontsize=8, rotation=90)
            plt.text(x[i] + bar_width, max_val + 0.01, f'{max_val:.3f}', ha='center', va='bottom',
                    color='black', fontsize=8, rotation=90)
        
        # Adicionar linhas de limites PRODIST
        plt.axhline(y=voltage_limits['adequate_min'], color='black', linestyle='--', alpha=0.7, label='Adequada Mín (0.92 p.u.)')
        plt.axhline(y=voltage_limits['adequate_max'], color='black', linestyle='--', alpha=0.7, label='Adequada Máx (1.05 p.u.)')
        plt.axhline(y=voltage_limits['precarious_min'], color='gray', linestyle=':', alpha=0.7, label='Precária Mín (0.87 p.u.)')
        plt.axhline(y=voltage_limits['precarious_max'], color='gray', linestyle=':', alpha=0.7, label='Precária Máx (1.06 p.u.)')
        
        # Configurar eixos
        plt.xlabel('Transformador', color='black')
        plt.ylabel('Tensão (p.u.)', color='black')
        plt.title(f'Resumo de Tensões - Cenário {scenario}', color='black')
        plt.xticks(x, sorted_transformers, rotation=90)
        plt.grid(True, axis='y', alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        # Salvar figura
        output_file = os.path.join(output_dir, f"V_PU_Summary.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"    Gráfico de resumo de tensão gerado para o cenário {scenario}")
        
    except Exception as e:
        print(f"    Erro ao gerar gráfico de resumo de tensão: {str(e)}")

def generate_current_summary_graph(df, transformers, scenario, output_dir):
    """
    Gera gráfico de resumo de corrente para todos os transformadores
    """
    try:
        # Dicionário para armazenar valores mínimos, médios e máximos
        transformer_currents = {}
        
        # Extrair valores extremos para cada transformador
        for transformer in transformers:
            i_min_col = f"{transformer}_I_PU_Min"
            i_avg_col = f"{transformer}_I_PU_Avg"
            i_max_col = f"{transformer}_I_PU_Max"
            
            # Verificar se todas as colunas existem
            if not all(col in df.columns for col in [i_min_col, i_avg_col, i_max_col]):
                print(f"    Colunas de corrente não encontradas para o transformador {transformer}")
                continue
            
            # Encontrar valores mínimos, médios e máximos
            min_val = df[i_min_col].min()
            avg_val = df[i_avg_col].mean()
            max_val = df[i_max_col].max()
            
            transformer_currents[transformer] = {
                'min': min_val,
                'avg': avg_val,
                'max': max_val
            }
        
        # Ordenar transformadores pelo valor máximo (decrescente)
        sorted_transformers = sorted(
            transformer_currents.keys(),
            key=lambda t: transformer_currents[t]['max'],
            reverse=True
        )
        
        # Extrair valores para plotagem
        min_values = [transformer_currents[t]['min'] for t in sorted_transformers]
        avg_values = [transformer_currents[t]['avg'] for t in sorted_transformers]
        max_values = [transformer_currents[t]['max'] for t in sorted_transformers]
        
        # Criar figura
        plt.figure(figsize=(16, 10))
        
        # Definir largura da barra e posições
        bar_width = 0.25
        x = np.arange(len(sorted_transformers))
        
        # Plotar barras
        plt.bar(x - bar_width, min_values, bar_width, color='green', label='Mínima')
        plt.bar(x, avg_values, bar_width, color='yellow', label='Média')
        plt.bar(x + bar_width, max_values, bar_width, color='red', label='Máxima')
        
        # Adicionar valores nas barras
        for i, (min_val, avg_val, max_val) in enumerate(zip(min_values, avg_values, max_values)):
            plt.text(x[i] - bar_width, min_val + 0.01, f'{min_val:.3f}', ha='center', va='bottom',
                    color='black', fontsize=8, rotation=90)
            plt.text(x[i], avg_val + 0.01, f'{avg_val:.3f}', ha='center', va='bottom',
                    color='black', fontsize=8, rotation=90)
            plt.text(x[i] + bar_width, max_val + 0.01, f'{max_val:.3f}', ha='center', va='bottom',
                    color='black', fontsize=8, rotation=90)
        
        # Adicionar linha de corrente nominal
        plt.axhline(y=1.0, color='black', linestyle='--', alpha=0.7, label='Corrente Nominal (1.0 p.u.)')
        
        # Configurar eixos
        plt.xlabel('Transformador', color='black')
        plt.ylabel('Corrente (p.u.)', color='black')
        plt.title(f'Resumo de Correntes - Cenário {scenario}', color='black')
        plt.xticks(x, sorted_transformers, rotation=90)
        plt.grid(True, axis='y', alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        # Salvar figura
        output_file = os.path.join(output_dir, f"I_PU_Summary.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"    Gráfico de resumo de corrente gerado para o cenário {scenario}")
        
    except Exception as e:
        print(f"    Erro ao gerar gráfico de resumo de corrente: {str(e)}")

# Executar o programa
if __name__ == "__main__":
    print("Iniciando geração de gráficos individuais...")
    generate_individual_graphs()
    print("Geração de gráficos concluída!")