import os
import pandas as pd
import numpy as np

# Definição dos caminhos
DICT_PATH = r'C:\Users\bruno\OneDrive\Área de Trabalho\TCC\PYTHON\CSV\dict'  # Caminho para os arquivos de dicionário
CSV_PATH = r'C:\Users\bruno\OneDrive\Área de Trabalho\TCC\PYTHON\CSV\conv'  # Caminho para os arquivos CSV
DSS_PATH = r'C:\Users\bruno\OneDrive\Área de Trabalho\TCC\PYTHON\DSS'  # Caminho para salvar arquivos OpenDSS

# Parâmetros para carga adicional
rechargerload = 15  # Carga adicional em kW
EVSpread = 0  # Porcentagem de cargas que sofrerão aumento para veículos elétricos
GDSpread = 0  # Porcentagem de cargas que receberão geração distribuída
random_seed = 1  # Semente Aleatória para Reprodução

# Distribuição de curvas de carga
CurvaRecharger1 = 33.3333  # %
CurvaRecharger2 = 33.3334  # %
CurvaRecharger3 = 33.3333  # %

# Parâmetro para fator de potência
default_powerfactor = 0.92

# Tipo de dia para curvas de carga (DU, SA, DO)
default_day_type = 'DU'

# Base de tensão
medium_voltage_base = 13.8  # kV
low_voltage_base = 0.22  # kV

# Garantir que o diretório DSS existe
os.makedirs(DSS_PATH, exist_ok=True)

# Escopo alvo informado pelo usuário
escopo_alvo = [
    '34631299', '34705676', '34693896', '90199814', '34569437',
    '101428666', '34784390', '34611212', '91402190', '34685435',
    '34633937', '34622044', '34629647', '86683110',
 '34623374'
]

# Função para carregar arquivos CSV
def load_csv(file_name):
    try:
        df = pd.read_csv(os.path.join(CSV_PATH, file_name), sep=';', decimal='.', dtype=str)
        # Se o arquivo tem UNI_TR_MT, filtrar pelo escopo_alvo imediatamente
        if 'UNI_TR_MT' in df.columns:
            df = df[df['UNI_TR_MT'].isin(escopo_alvo)]
        return df
    except Exception as e:
        print(f"Erro ao carregar {file_name}: {e}")
        return pd.DataFrame()

# Função para carregar dicionários
def load_dict(file_name):
    try:
        df = pd.read_csv(os.path.join(DICT_PATH, file_name), sep=';', decimal='.', dtype=str)
        # Converter colunas numéricas relevantes
        if 'R1' in df.columns:
            df['R1'] = pd.to_numeric(df['R1'], errors='coerce')
        if 'X1' in df.columns:
            df['X1'] = pd.to_numeric(df['X1'], errors='coerce')
        if 'CNOM' in df.columns:
            df['CNOM'] = pd.to_numeric(df['CNOM'], errors='coerce')
        if 'CMAX' in df.columns:
            df['CMAX'] = pd.to_numeric(df['CMAX'], errors='coerce')
        return df
    except Exception as e:
        print(f"Erro ao carregar dicionário {file_name}: {e}")
        return pd.DataFrame()

# Função para traduzir códigos usando dicionário
def translate_code(df, column, dict_df, dict_key, dict_value):
    if column in df.columns:
        if dict_key in dict_df.columns and dict_value in dict_df.columns:
            mapping = dict_df.set_index(dict_key)[dict_value].to_dict()
            df[column] = df[column].map(mapping).fillna(df[column])
    return df

# Função para determinar o número de fases
def determine_phases(fas_con):
    if fas_con in ['ABCN', 'ABC']:
        return 3
    elif fas_con in ['ABN', 'AB']:
        return 2
    elif fas_con in ['AN', 'BN', 'A', 'B']:
        return 1
    else:
        return 3  # Default to 3 phases if unknown

# Função para aplicar aumento de carga para veículos elétricos
def apply_load_increase(loads_df):
    num_loads = len(loads_df)
    num_to_increase = int((EVSpread / 100) * num_loads)
    np.random.seed(random_seed)  # Garantir que a semente aleatória seja aplicada
    loads_to_increase = loads_df.sample(num_to_increase, random_state=random_seed).copy()

    # Definir curva de carga aleatória baseada na distribuição
    choices = ['CurvaRecharger1', 'CurvaRecharger2', 'CurvaRecharger3']
    probabilities = [CurvaRecharger1 / 100, CurvaRecharger2 / 100, CurvaRecharger3 / 100]
    loads_to_increase['TIP_CC'] = np.random.choice(choices, size=len(loads_to_increase), p=probabilities)

    # Criar nova carga para as UCBTs selecionadas
    new_loads = loads_to_increase.copy()
    new_loads['kW_increased'] = rechargerload
    new_loads['PAC'] = loads_to_increase['PAC']  # Mesmo barramento
    new_loads['FAS_CON'] = loads_to_increase['FAS_CON']
    new_loads['TEN_FORN'] = loads_to_increase['TEN_FORN']  # Adicionado para garantir a tensão correta
    
    print(f"Adicionando {num_to_increase} carregadores de EV ({EVSpread}% das UCs)")
    return new_loads

# Função para aplicar geração distribuída fotovoltaica
def apply_distributed_generation(loads_df):
    num_loads = len(loads_df)
    num_to_add_gd = int((GDSpread / 100) * num_loads)
    np.random.seed(random_seed)  # Garantir que a semente aleatória seja aplicada
    loads_with_gd = loads_df.sample(num_to_add_gd, random_state=random_seed).copy()
    
    # Criar geração fotovoltaica para as UCBTs selecionadas
    loads_with_gd['kW_generation'] = pd.to_numeric(loads_with_gd['CAR_INST'], errors='coerce')
    loads_with_gd['TIP_CC_GD'] = 'CurvaGD'  # Usar a curva universal de geração fotovoltaica
    
    print(f"Adicionando {num_to_add_gd} geradores fotovoltaicos (GD) ({GDSpread}% das UCs)")
    return loads_with_gd

def check_and_fix_connectivity(lines_df, loads_df, transformers_df):
    """
    Verifica e corrige a conectividade da rede seguindo estritamente a hierarquia:
    UCBT -> RAMLIG -> SSDBT -> Transformador
    """
    # Valores padrão para quando faltar dados
    default_values = {
        'R1': 0.5,
        'X1': 0.1,
        'CNOM': 400,
        'CMAX': 600,
        'COMP': 30
    }

    # Separar SSDBT e RAMLIG
    ssdbt_df = lines_df[lines_df['TIP_CND'].str.startswith('SSDBT', na=False)].copy()
    ramlig_df = lines_df[lines_df['TIP_CND'].str.startswith('RAMLIG', na=False)].copy()
    
    # Criar dicionário de transformador por carga e seus barramentos
    load_transformer_map = dict(zip(loads_df['PAC'], loads_df['UNI_TR_MT']))
    transformer_bus_map = dict(zip(transformers_df['COD_ID'], transformers_df['PAC_2']))
    transformer_phases_map = dict(zip(transformers_df['COD_ID'], transformers_df['FAS_CON_S']))
    
    # Criar dicionários de conexões por tipo
    ssdbt_connections = {}
    ramlig_connections = {}
    
    # Mapear conexões SSDBT existentes
    for _, row in ssdbt_df.iterrows():
        if pd.isna(row['PAC_1']) or pd.isna(row['PAC_2']):
            continue
        if row['PAC_1'] not in ssdbt_connections:
            ssdbt_connections[row['PAC_1']] = set()
        if row['PAC_2'] not in ssdbt_connections:
            ssdbt_connections[row['PAC_2']] = set()
        ssdbt_connections[row['PAC_1']].add(row['PAC_2'])
        ssdbt_connections[row['PAC_2']].add(row['PAC_1'])
    
    # Mapear conexões RAMLIG existentes
    for _, row in ramlig_df.iterrows():
        if pd.isna(row['PAC_1']) or pd.isna(row['PAC_2']):
            continue
        if row['PAC_1'] not in ramlig_connections:
            ramlig_connections[row['PAC_1']] = set()
        if row['PAC_2'] not in ramlig_connections:
            ramlig_connections[row['PAC_2']] = set()
        ramlig_connections[row['PAC_1']].add(row['PAC_2'])
        ramlig_connections[row['PAC_2']].add(row['PAC_1'])

    # Calcular médias para SSDBT e RAMLIG
    def calculate_averages(df):
        averages = {}
        for key in default_values:
            try:
                values = pd.to_numeric(df[key], errors='coerce')
                value = values[values > 0].mean()  # Considerar apenas valores positivos
                averages[key] = value if pd.notnull(value) else default_values[key]
            except:
                averages[key] = default_values[key]
        return averages

    ssdbt_avg = calculate_averages(ssdbt_df)
    ramlig_avg = calculate_averages(ramlig_df)

    def check_path_to_transformer(load_bus, transformer_bus):
        """
        Verifica se existe um caminho válido da carga até o transformador
        seguindo a hierarquia RAMLIG -> SSDBT
        """
        if load_bus not in ramlig_connections:
            return False, None

        for intermediate_bus in ramlig_connections[load_bus]:
            visited = set([load_bus])
            to_check = [intermediate_bus]
            
            while to_check:
                current = to_check.pop(0)
                if current == transformer_bus:
                    return True, intermediate_bus
                
                if current not in visited and current in ssdbt_connections:
                    visited.add(current)
                    to_check.extend(ssdbt_connections[current])
        
        return False, None

    new_lines = []
    processed_loads = set()

    # Verificar cada carga
    for _, load in loads_df.iterrows():
        if pd.isna(load['PAC']) or load['PAC'] in processed_loads:
            continue

        load_bus = load['PAC']
        transformer_id = load['UNI_TR_MT']
        
        if transformer_id not in transformer_bus_map:
            continue
            
        transformer_bus = transformer_bus_map[transformer_id]
        transformer_phases = transformer_phases_map[transformer_id]

        # Verificar conectividade existente
        has_path, intermediate_bus = check_path_to_transformer(load_bus, transformer_bus)
        
        if not has_path:
            # Criar PAC intermediário
            intermediate_bus = f"PAC_INT_{transformer_id}_{load_bus}"
            
            # Criar RAMLIG
            new_lines.append({
                'PAC_1': load_bus,
                'PAC_2': intermediate_bus,
                'COMP': ramlig_avg['COMP'],
                'UNI_TR_MT': transformer_id,
                'TIP_CND': 'RAMLIG',
                'FAS_CON': load['FAS_CON'] if pd.notnull(load['FAS_CON']) else transformer_phases,
                'R1': ramlig_avg['R1'],
                'X1': ramlig_avg['X1'],
                'CNOM': ramlig_avg['CNOM'],
                'CMAX': ramlig_avg['CMAX']
            })
            
            # Criar SSDBT
            new_lines.append({
                'PAC_1': intermediate_bus,
                'PAC_2': transformer_bus,
                'COMP': ssdbt_avg['COMP'],
                'UNI_TR_MT': transformer_id,
                'TIP_CND': 'SSDBT',
                'FAS_CON': transformer_phases,
                'R1': ssdbt_avg['R1'],
                'X1': ssdbt_avg['X1'],
                'CNOM': ssdbt_avg['CNOM'],
                'CMAX': ssdbt_avg['CMAX']
            })

        processed_loads.add(load_bus)

    # Adicionar novas linhas ao dataframe
    if new_lines:
        new_lines_df = pd.DataFrame(new_lines)
        print(f"Adicionadas {len(new_lines)} novas linhas para garantir conectividade")
        lines_df = pd.concat([lines_df, new_lines_df], ignore_index=True)

    return lines_df

# Função para converter valores para float corretamente
def safe_to_numeric(value):
    if isinstance(value, str):
        value = value.replace(',', '.')
    return pd.to_numeric(value, errors='coerce')

# Função para escrever o cabeçalho e configuração do circuito
def write_circuit_configuration(dss_file):
    dss_file.write("Clear\n")
    
    # Definir o circuito
    dss_file.write("! Circuit Definition\n")
    dss_file.write("New Circuit.MyCircuit")
    dss_file.write(" bus1=sourcebus.1.2.3.0")
    dss_file.write(f" basekv={medium_voltage_base}")
    dss_file.write(" pu=1.0")
    dss_file.write(" phases=3")
    dss_file.write(" MVAsc3=2000")  # Ajustar potência de curto-circuito
    dss_file.write(" MVAsc1=2100\n\n")

    # Definir parâmetros de solução primeiro
    dss_file.write("! Solution Parameters\n")
    dss_file.write("Set DefaultBaseFreq=60\n")
    dss_file.write("Set maxiterations=100\n")      # Aumentar número máximo de iterações
    dss_file.write("Set maxcontroliter=100\n")     # Aumentar iterações de controle
    dss_file.write("Set algorithm=newton\n")       # Usar método Newton-Raphson
    dss_file.write("Set tolerance=0.0001\n")       # Ajustar tolerância
    dss_file.write("Set voltagebases=[13.8, 0.22]\n\n")


    dss_file.write("Calcvoltagebases\n\n")
    
# Função para escrever os transformadores de média tensão
def write_medium_voltage_transformers(dss_file):
    # Carregar dados necessários
    CSV_DATA = {key: load_csv(file) for key, file in {
        'UNTRMT': 'UNTRMT.csv',
        'EQTRMT': 'EQTRMT.csv'
    }.items()}

    DICT_DATA = {key: load_dict(file) for key, file in {
        'TTEN': 'TTEN.csv',
        'TPOT': 'TPOT.csv'
    }.items()}

    # Traduzir colunas relevantes
    translate_code(CSV_DATA['EQTRMT'], 'POT_NOM', DICT_DATA['TPOT'], 'COD_ID', 'POT')
    translate_code(CSV_DATA['EQTRMT'], 'TEN_PRI', DICT_DATA['TTEN'], 'COD_ID', 'TEN')
    translate_code(CSV_DATA['EQTRMT'], 'TEN_SEC', DICT_DATA['TTEN'], 'COD_ID', 'TEN')

    # Filtrar transformadores válidos
    valid_transformers = CSV_DATA['UNTRMT'][
        CSV_DATA['UNTRMT']['COD_ID'].isin(escopo_alvo)
    ]

    dss_file.write("! Medium Voltage Transformers\n")
    for _, row in valid_transformers.iterrows():
        eq_row = CSV_DATA['EQTRMT'][CSV_DATA['EQTRMT']['UNI_TR_MT'] == row['COD_ID']]
        if not eq_row.empty:
            eq_row = eq_row.iloc[0]
            secondary_bus = row['PAC_2']
            conn_primary = 'delta' if len(row['FAS_CON_P']) == 3 else 'wye'
            conn_secondary = 'wye' if row['FAS_CON_S'] == 'ABCN' else 'delta'
            phases_primary = determine_phases(row['FAS_CON_P'])
            phases_secondary = determine_phases(row['FAS_CON_S'])
            primary_kv = pd.to_numeric(eq_row['TEN_PRI'], errors='coerce') / 1000
            secondary_kv = pd.to_numeric(eq_row['TEN_SEC'], errors='coerce') / 1000
            pot_nom = safe_to_numeric(eq_row['POT_NOM']) * 1000  # Converter de kVA para VA

            # Verificar se potência nominal é válida
            if pd.isna(pot_nom) or pot_nom == 0:
                print(f"AVISO: Transformador {row['COD_ID']} ignorado devido à potência nominal inválida.")
                continue

            # Calcular perdas corretamente
            per_tot = safe_to_numeric(eq_row['PER_TOT'])
            per_fer = safe_to_numeric(eq_row['PER_FER'])

            # Converter perdas para porcentagem
            per_tot = ((per_tot * 1000) / pot_nom) * 100 if per_tot < 10 else (per_tot / pot_nom) * 100
            per_fer = ((per_fer * 1000) / pot_nom) * 100 if per_fer < 10 else (per_fer / pot_nom) * 100

            dss_file.write(f"New Transformer.{row['COD_ID']} Phases={phases_primary} Windings=2\n")
            dss_file.write(f"~ Buses=[sourcebus.1.2.3, {secondary_bus}.1.2.3] Conns=[{conn_primary} {conn_secondary}]\n")  # Especificar fases explicitamente
            dss_file.write(f"~ kVs=[{primary_kv:.3f} {secondary_kv:.3f}] kVAs=[{pot_nom/1000:.1f} {pot_nom/1000:.1f}]\n")
            dss_file.write(f"~ %LoadLoss={per_tot:.3f} %NoLoadLoss={per_fer:.3f} XHL={eq_row['XHL']}\n")

# Função para escrever as linhas de baixa tensão
def write_low_voltage_lines(dss_file):
    CSV_DATA = {key: load_csv(file) for key, file in {
        'SSDBT': 'SSDBT.csv',
        'RAMLIG': 'RAMLIG.csv',
        'SEGCON': 'SEGCON.csv',
        'UCBT': 'UCBT_tab.csv',
        'UNTRMT': 'UNTRMT.csv'
    }.items()}
    
    # Traduzir os condutores
    CSV_DATA['SSDBT'] = CSV_DATA['SSDBT'].merge(CSV_DATA['SEGCON'], how='left', left_on='TIP_CND', right_on='COD_ID')
    CSV_DATA['RAMLIG'] = CSV_DATA['RAMLIG'].merge(CSV_DATA['SEGCON'], how='left', left_on='TIP_CND', right_on='COD_ID')
    
    # Filtrar somente linhas do escopo alvo
    CSV_DATA['SSDBT'] = CSV_DATA['SSDBT'][CSV_DATA['SSDBT']['UNI_TR_MT'].isin(escopo_alvo)]
    CSV_DATA['RAMLIG'] = CSV_DATA['RAMLIG'][CSV_DATA['RAMLIG']['UNI_TR_MT'].isin(escopo_alvo)]
    
    # Concatenar linhas e ramais
    all_lines = pd.concat([CSV_DATA['SSDBT'], CSV_DATA['RAMLIG']], ignore_index=True)
    
    # Ajustar conectividade
    all_lines = check_and_fix_connectivity(all_lines, CSV_DATA['UCBT'], CSV_DATA['UNTRMT'])
    
    # Valores padrão para substituir NaN
    default_values = {
        'R1': 0.25,
        'X1': 0.0001,
        'CNOM': 400,
        'CMAX': 600,
        'COMP': 30,  # Comprimento padrão de 30 metros
        'FAS_CON': 'ABC'  # Configuração trifásica como padrão
    }
    
# Escrever linhas no arquivo DSS
    dss_file.write("! Low Voltage Lines\n")
    for _, row in all_lines.iterrows():
        # Substituir valores NaN por padrões
        r1 = float(row['R1']) if pd.notnull(row['R1']) else default_values['R1']
        x1 = float(row['X1']) if pd.notnull(row['X1']) else default_values['X1']
        cnom = float(row['CNOM']) if pd.notnull(row['CNOM']) else default_values['CNOM']
        cmax = float(row['CMAX']) if pd.notnull(row['CMAX']) else default_values['CMAX']
        comp = float(row['COMP']) if pd.notnull(row['COMP']) else default_values['COMP']
        
        # Converter ohm/km para ohm total na linha
        comp_km = comp / 1000.0  # Converter o comprimento de metros para km
        r1_ohm = r1 * comp_km   # Resistência total para o comprimento da linha
        x1_ohm = x1 * comp_km    # Reatância total para o comprimento da linha

        
        phases = determine_phases(row['FAS_CON'] if pd.notnull(row['FAS_CON']) else default_values['FAS_CON'])
        dss_file.write(f"New Line.{row['PAC_1']}_{row['PAC_2']} Phases={phases}\n")
        dss_file.write(f"~ Bus1={row['PAC_1']}.1.2.3 Bus2={row['PAC_2']}.1.2.3\n")  # Especificar fases explicitamente
        dss_file.write(f"~ Length={comp} units=m\n")
        
        # Usar os valores convertidos (em ohm) para o comprimento específico da linha
        dss_file.write(f"~ R1={r1_ohm:.6f} X1={x1_ohm:.6f} C1=0.0\n")
        
        dss_file.write(f"~ NormAmps={cnom} EmergAmps={cmax}\n")

# Função para escrever as curvas de carga
def write_load_curves(dss_file):
    # Carregar dados necessários
    curves = load_csv('CRVCRG.csv')

    # Filtrar pelas curvas do tipo de dia definido
    filtered_curves = curves[curves['TIP_DIA'] == default_day_type]

    # Calcular valores em p.u. e escrever no arquivo DSS
    dss_file.write("! Load Curves\n")
    for _, row in filtered_curves.iterrows():
        # Converter colunas POT_01 a POT_96 para float
        pot_columns = [f"POT_{i:02d}" for i in range(1, 97)]
        pot_values = row[pot_columns].astype(float)

        # Verificar se há valores NaN
        if pot_values.isna().any():
            continue

        # Calcular o valor máximo e normalizar
        max_value = pot_values.max()
        if max_value == 0:
            continue  # Evita divisões por zero

        pu_values = (pot_values / max_value).round(4).tolist()

        # Escrever curva no arquivo DSS
        pu_values_str = " ".join(map(str, pu_values))
        dss_file.write(f"New Loadshape.{row['COD_ID']} npts=96 interval=0.25 mult=({pu_values_str}) useactual=no\n")

# Função para escrever curvas de carga dos carregadores de veículos elétricos
def write_recharger_load_curves(dss_file):
    dss_file.write("! EV Charger Load Curves\n")
    
    # Curva 1: 8 horas de carga começando às 19h, reduzindo para 0.7 pu nas últimas 2 horas
    curve1 = [0.0] * 76 + [1.0] * 24 + [0.7] * 8 + [0.0] * 12
    
    # Curva 2: 12 horas de carga começando às 16h, reduzindo para 0.7 pu nas últimas 4 horas
    curve2 = [0.0] * 64 + [1.0] * 32 + [0.7] * 16 + [0.0] * 8
    
    # Curva 3: 6 horas de carga começando ao meio-dia, sempre 1.0 pu
    curve3 = [0.0] * 48 + [1.0] * 24 + [0.0] * 24
    
    # Escrever curvas no arquivo DSS
    dss_file.write("New LoadShape.CurvaRecharger1 npts=96 interval=0.25\n")
    dss_file.write(f"~ mult=[{', '.join(map(str, curve1))}]\n")
    
    dss_file.write("New LoadShape.CurvaRecharger2 npts=96 interval=0.25\n")
    dss_file.write(f"~ mult=[{', '.join(map(str, curve2))}]\n")
    
    dss_file.write("New LoadShape.CurvaRecharger3 npts=96 interval=0.25\n")
    dss_file.write(f"~ mult=[{', '.join(map(str, curve3))}]\n")

# Função para escrever curva de geração fotovoltaica
def write_photovoltaic_generation_curve(dss_file):
    dss_file.write("! Photovoltaic Generation Curve\n")
    
    # Criar curva de geração fotovoltaica (96 pontos, um para cada 15 minutos)
    # Valores de 0 a 1 que representam o padrão típico de geração solar ao longo do dia
    # 0h às 5h45: 0 (sem geração)
    # 6h às 18h: aumento gradual até pico em torno do meio-dia, depois declínio
    # 18h15 às 23h45: 0 (sem geração)
    
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
        0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00
    ]
    
    # Escrever curva no arquivo DSS
    dss_file.write("New LoadShape.CurvaGD npts=96 interval=0.25\n")
    dss_file.write(f"~ mult=[{', '.join(map(str, solar_curve))}]\n")

    
# Função para escrever as cargas em baixa tensão
def write_loads(dss_file):
    CSV_DATA = {key: load_csv(file) for key, file in {
        'UCBT': 'UCBT_tab.csv'
    }.items()}
    
    DICT_DATA = {key: load_csv(file) for key, file in {
        'TTEN': 'TTEN.csv'
    }.items()}
    
    translate_code(CSV_DATA['UCBT'], 'TEN_FORN', DICT_DATA['TTEN'], 'COD_ID', 'TEN')
    valid_loads = CSV_DATA['UCBT'][CSV_DATA['UCBT']['UNI_TR_MT'].isin(escopo_alvo)]

    # Aplicar aumento de carga para veículos elétricos
    additional_loads = apply_load_increase(valid_loads)
    
    # Aplicar geração distribuída fotovoltaica
    pv_loads = apply_distributed_generation(valid_loads)

    # Escrever cargas no arquivo DSS
    dss_file.write("! Loads\n")
    for _, row in valid_loads.iterrows():
        phases = determine_phases(row['FAS_CON'])
        load_name = f"{row['PAC']}_{_}"
        # Especificar conexão e fases explicitamente
        conn = "delta" if phases == 3 else "wye"
        dss_file.write(f"New Load.{load_name} Phases={phases} Bus1={row['PAC']}.1.2.3\n")
        dss_file.write(f"~ kV={float(row['TEN_FORN']) / 1000:.3f} Conn={conn}\n")
        dss_file.write(f"~ kW={row['CAR_INST']} PF={default_powerfactor} Model=1 Daily={row['TIP_CC']}\n")

    # Escrever cargas adicionais para veículos elétricos
    for _, row in additional_loads.iterrows():
        phases = determine_phases(row['FAS_CON'])
        load_name = f"Recharger_{row['PAC']}_{_}"
        dss_file.write(f"New Load.{load_name} Phases={phases} Bus1={row['PAC']}.1.2.3\n")
        dss_file.write(f"~ kV={float(row['TEN_FORN']) / 1000:.3f} Conn={'delta' if phases == 3 else 'wye'}\n")
        dss_file.write(f"~ kW={row['kW_increased']} PF={default_powerfactor} Model=1 Daily={row['TIP_CC']}\n")
    
    # Escrever geradores fotovoltaicos
    dss_file.write("\n! Distributed Generation (Photovoltaic)\n")
    for _, row in pv_loads.iterrows():
        phases = determine_phases(row['FAS_CON'])
        gen_name = f"PV_{row['PAC']}_{_}"
        dss_file.write(f"New Generator.{gen_name} Phases={phases} Bus1={row['PAC']}.1.2.3\n")
        dss_file.write(f"~ kV={float(row['TEN_FORN']) / 1000:.3f} Conn={'delta' if phases == 3 else 'wye'}\n")
        dss_file.write(f"~ kW={float(row['CAR_INST']) * (3/4) } PF={default_powerfactor} Model=1 Daily=CurvaGD\n")

# Função para escrever os comandos de monitores
def write_monitors(dss_file):
    dss_file.write("\n! Monitors\n")
    for transformer_id in escopo_alvo:
        dss_file.write(f"New Monitor.{transformer_id}_voltage Element=Transformer.{transformer_id} Terminal=2 Mode=0\n")
        dss_file.write(f"New Monitor.{transformer_id}_current Element=Transformer.{transformer_id} Terminal=2 Mode=1\n")
        



    dss_file.write("\n! Final Solution Commands\n")
    dss_file.write("Set MaxControlIter=100\n")
    dss_file.write("Solve MaxControl=100 number=96\n")
    dss_file.write("Show Voltage LN Nodes\n")
    dss_file.write("Show Voltage Elements\n")
    dss_file.write("Show Powers kVA Elements\n")
    dss_file.write("Show Losses\n")

# Gerar arquivo DSS
def generate_dss():
    file_name = f"kW={int(rechargerload)}--EV={EVSpread}--GD={GDSpread}--RS={random_seed}--V3.0.dss"
    file_path = os.path.join(DSS_PATH, file_name)

    with open(file_path, 'w') as dss_file:
        # 1. Configuração básica e parâmetros de solução
        dss_file.write("Clear\n\n")

        # 2. Definição do Circuito
        dss_file.write("! Circuit Definition\n")
        dss_file.write("New Circuit.MyCircuit")
        dss_file.write(" bus1=sourcebus.1.2.3.0")
        dss_file.write(f" basekv={medium_voltage_base}")
        dss_file.write(" pu=1.0")
        dss_file.write(" phases=3")
        dss_file.write(" MVAsc3=2000")
        dss_file.write(" MVAsc1=2100\n\n")
        
        dss_file.write("! Solution Parameters\n")
        dss_file.write("Set DefaultBaseFreq=60\n")
        dss_file.write("Set maxiterations=100\n")
        dss_file.write("Set maxcontroliter=100\n")
        dss_file.write("Set algorithm=newton\n")
        dss_file.write("Set tolerance=0.0001\n")
        dss_file.write(f"Set voltagebases=[{medium_voltage_base}, {low_voltage_base}]\n\n")
        
        # Informações da simulação como comentário
        dss_file.write(f"! Simulation Parameters:\n")
        dss_file.write(f"! - EV Load: {rechargerload} kW\n")
        dss_file.write(f"! - EV Spread: {EVSpread}%\n") 
        dss_file.write(f"! - DG Spread: {GDSpread}%\n\n")

        dss_file.write("Calcvoltagebases\n\n")

        # 3. Curvas de carga (definir antes dos elementos que as usarão)
        print("Writing load curves...")
        write_load_curves(dss_file)
        write_recharger_load_curves(dss_file)
        write_photovoltaic_generation_curve(dss_file)

        # 4. Transformadores
        print("Writing transformers...")
        write_medium_voltage_transformers(dss_file)

        # 5. Linhas de baixa tensão
        print("Writing low voltage lines...")
        write_low_voltage_lines(dss_file)

        # 6. Cargas
        print("Writing loads...")
        write_loads(dss_file)
        
        # 7. Monitores (definir antes de iniciar a solução)
        print("Setting up monitors...")
        write_monitors(dss_file)

        # 8. Primeiro resolver em modo snapshot para verificar a convergência
        dss_file.write("\n! Initial Snapshot Solution\n")
        dss_file.write("Set mode=snapshot\n")
        dss_file.write("Set controlmode=static\n")
        dss_file.write("Solve\n")

        # 9. Se convergiu, passar para modo diário
        dss_file.write("\n! Daily Mode Solution\n")
        dss_file.write("Set mode=daily\n")
        dss_file.write("Set stepsize=0.25h\n")  # 15 minutos
        dss_file.write("Set number=96\n")       # 24 horas = 96 intervalos de 15 minutos
        dss_file.write("Set controlmode=time\n")
        
        # 10. Resolver no modo diário
        dss_file.write("\n! Solve Daily\n")
        dss_file.write("Solve\n")
        
        # 11. Mostrar resultados
        dss_file.write("\n! Show Results\n")
        dss_file.write("Show Voltage LN Nodes\n")
        dss_file.write("Show Currents Elements\n")
        dss_file.write("Show Powers kVA Elements\n")
        dss_file.write("Show Losses\n")
        
        # 12. Exportar resultados dos monitores
        dss_file.write("\n! Export Monitor Data\n")
        for transformer_id in escopo_alvo:
            dss_file.write(f"Export Monitor {transformer_id}_voltage\n")
            dss_file.write(f"Export Monitor {transformer_id}_current\n")
            
            
        # 13. Exportar perfis de tensão e outros resultados
        dss_file.write("\n! Export Simulation Results\n")
        dss_file.write("Export Voltages\n")
        dss_file.write("Export Currents\n")
        dss_file.write("Export Powers\n")
        dss_file.write("Export Losses\n")
        
        # 14. Análise final das violações de tensão
        dss_file.write("\n! Check Voltage Violations\n")
        dss_file.write("Show Voltages LN Nodes\n")
        dss_file.write("Plot Profile Phases=All\n")

        print(f"Arquivo {file_name} gerado com sucesso em {DSS_PATH}.")


# Executar o programa
if __name__ == "__main__":
    print(f"Gerando arquivo DSS com:")
    print(f"- Carga adicional EV: {rechargerload} kW")
    print(f"- Porcentagem de UCs com EV: {EVSpread}%")
    print(f"- Porcentagem de UCs com GD: {GDSpread}%")
    generate_dss()
    print("Simulação concluída.")