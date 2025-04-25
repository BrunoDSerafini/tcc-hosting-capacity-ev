import os
import sys
import shutil
import time
import importlib.util
from datetime import datetime
import importlib.machinery

# Definição do diretório base para salvar os cenários
BASE_PATH = r'C:\DSSFiles3'

# Caminho para o arquivo original
ORIGINAL_SCRIPT_PATH = r'C:\Users\bruno\OneDrive\Área de Trabalho\TCC\PYTHON\DSSWriter3.2.py'

# Configurações para geração de cenários
EV_PERCENTAGES = [0, 25, 50, 75, 100]  # Percentuais de EV
GD_PERCENTAGES = [0, 25, 50, 75, 100]  # Percentuais de GD
RANDOM_SEEDS = list(range(1, 52))  # Random seeds de 1 a 51

# Função para registrar logs
def log_progress(message, log_file=None):
    """Registra mensagens de progresso na tela e em arquivo"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    if log_file:
        with open(log_file, 'a') as f:
            f.write(log_message + "\n")

def create_scenario_directory(gd_percentage, ev_percentage, random_seed):
    """Cria a estrutura de diretórios para um cenário específico"""
    scenario_name = f"GD{gd_percentage}--EV{ev_percentage}--RS{random_seed}"
    scenario_path = os.path.join(BASE_PATH, scenario_name)
    
    # Criar diretório base se não existir
    if not os.path.exists(BASE_PATH):
        os.makedirs(BASE_PATH)
    
    # Criar diretório do cenário
    if not os.path.exists(scenario_path):
        os.makedirs(scenario_path)
    else:
        log_progress(f"Diretório já existe: {scenario_path} - pulando")
        return None
        
    # Criar subdiretório DSS
    os.makedirs(os.path.join(scenario_path, 'DSS'), exist_ok=True)
    
    return scenario_path

def load_original_module():
    """Carrega o módulo original como biblioteca"""
    # Verificar se o arquivo original existe
    if not os.path.exists(ORIGINAL_SCRIPT_PATH):
        raise FileNotFoundError(f"Arquivo original não encontrado: {ORIGINAL_SCRIPT_PATH}")
    
    # Criar nome do módulo baseado no nome do arquivo
    module_name = os.path.splitext(os.path.basename(ORIGINAL_SCRIPT_PATH))[0]
    
    # Carregar o módulo
    spec = importlib.util.spec_from_file_location(module_name, ORIGINAL_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module

def run_dsswriter_for_scenario(gd_percentage, ev_percentage, random_seed):
    """Executa o DSSWriter para um cenário específico"""
    # Criar diretório para o cenário
    scenario_path = create_scenario_directory(gd_percentage, ev_percentage, random_seed)
    if scenario_path is None:
        return False
    
    # Carregar o módulo original
    try:
        original_module = load_original_module()
        
        # Salvar valores originais para restaurar depois
        original_evspread = getattr(original_module, 'EVSpread', 100)
        original_gdspread = getattr(original_module, 'GDSpread', 100)
        original_random_seed = getattr(original_module, 'random_seed', 1)
        original_dss_path = getattr(original_module, 'DSS_PATH', r'C:\Users\bruno\OneDrive\Área de Trabalho\TCC\PYTHON\DSS')
        
        # Modificar variáveis para o cenário atual
        setattr(original_module, 'EVSpread', ev_percentage)
        setattr(original_module, 'GDSpread', gd_percentage)
        setattr(original_module, 'random_seed', random_seed)
        setattr(original_module, 'DSS_PATH', os.path.join(scenario_path, 'DSS'))
        
        # Executar a função generate_dss do módulo original
        original_module.generate_dss()
        
        # Restaurar valores originais
        setattr(original_module, 'EVSpread', original_evspread)
        setattr(original_module, 'GDSpread', original_gdspread)
        setattr(original_module, 'random_seed', original_random_seed)
        setattr(original_module, 'DSS_PATH', original_dss_path)
        
        return True
    except Exception as e:
        log_progress(f"Erro ao processar cenário GD={gd_percentage}, EV={ev_percentage}, RS={random_seed}: {str(e)}")
        return False

def generate_all_scenarios():
    """Gera todos os cenários definidos nas configurações"""
    # Criar arquivo de log
    log_file = os.path.join(BASE_PATH, "scenario_generation.log")
    with open(log_file, 'w') as f:
        f.write(f"Iniciando geração de cenários em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Calcular número total de cenários
    # Ajuste para considerar que casos com 0% ou 100% só usam random_seed=1
    total_scenarios = 0
    for gd_percentage in GD_PERCENTAGES:
        for ev_percentage in EV_PERCENTAGES:
            if (gd_percentage == 0 or gd_percentage == 100) and (ev_percentage == 0 or ev_percentage == 100):
                # Para 0% ou 100% de GD e EV, só use random_seed=1
                total_scenarios += 1
            else:
                # Para outros casos, use todos os random seeds
                total_scenarios += len(RANDOM_SEEDS)
    
    log_progress(f"Total de cenários a serem gerados: {total_scenarios}", log_file)
    
    # Contadores para estatísticas
    scenario_count = 0
    success_count = 0
    skip_count = 0
    error_count = 0
    
    # Registrar tempo de início
    start_time = time.time()
    
    # Gerar todos os cenários
    for gd_percentage in GD_PERCENTAGES:
        for ev_percentage in EV_PERCENTAGES:
            # Determinar quais random seeds usar para este cenário
            if (gd_percentage == 0 or gd_percentage == 100) and (ev_percentage == 0 or ev_percentage == 100):
                # Para 0% ou 100% de GD e EV, só use random_seed=1
                seeds_to_use = [1]
            else:
                # Para outros casos, use todos os random seeds
                seeds_to_use = RANDOM_SEEDS
            
            for random_seed in seeds_to_use:
                scenario_count += 1
                
                log_progress(f"Processando cenário {scenario_count}/{total_scenarios}: GD={gd_percentage}%, EV={ev_percentage}%, RS={random_seed}", log_file)
                
                # Executar o DSSWriter para este cenário
                success = run_dsswriter_for_scenario(gd_percentage, ev_percentage, random_seed)
                
                if success:
                    success_count += 1
                else:
                    # Verificar se é um erro ou se o diretório já existia
                    if os.path.exists(os.path.join(BASE_PATH, f"GD{gd_percentage}--EV{ev_percentage}--RS{random_seed}")):
                        skip_count += 1
                    else:
                        error_count += 1
                
                # Calcular progresso e tempo estimado restante
                elapsed_time = time.time() - start_time
                avg_time_per_scenario = elapsed_time / scenario_count
                remaining_scenarios = total_scenarios - scenario_count
                estimated_remaining_time = avg_time_per_scenario * remaining_scenarios
                
                # Registrar progresso
                log_progress(f"Progresso: {scenario_count}/{total_scenarios} ({scenario_count/total_scenarios*100:.1f}%)", log_file)
                log_progress(f"Tempo estimado restante: {estimated_remaining_time/60:.1f} minutos", log_file)
                log_progress(f"Estatísticas: {success_count} sucessos, {skip_count} ignorados, {error_count} erros", log_file)
    
    # Registrar estatísticas finais
    total_time = time.time() - start_time
    log_progress(f"Geração de cenários concluída em {total_time/60:.1f} minutos", log_file)
    log_progress(f"Total: {scenario_count} cenários | {success_count} sucessos | {skip_count} ignorados | {error_count} erros", log_file)

def generate_subset_scenarios(gd_values=None, ev_values=None, rs_start=1, rs_end=51):
    """
    Gera um subconjunto de cenários com os valores especificados
    
    Args:
        gd_values (list): Lista de percentuais de GD a serem gerados (default: todos)
        ev_values (list): Lista de percentuais de EV a serem gerados (default: todos)
        rs_start (int): Valor inicial de random seed (default: 1)
        rs_end (int): Valor final de random seed (default: 51)
    """
    # Usar valores padrão se não especificados
    gd_values = gd_values if gd_values is not None else GD_PERCENTAGES
    ev_values = ev_values if ev_values is not None else EV_PERCENTAGES
    rs_values = list(range(rs_start, rs_end + 1))
    
    # Criar arquivo de log
    log_file = os.path.join(BASE_PATH, "subset_generation.log")
    with open(log_file, 'w') as f:
        f.write(f"Iniciando geração de subconjunto de cenários em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"GD: {gd_values}\n")
        f.write(f"EV: {ev_values}\n")
        f.write(f"RS: {rs_start} a {rs_end}\n")
    
    # Calcular número total de cenários (ajustado para casos 0% e 100%)
    total_scenarios = 0
    for gd_percentage in gd_values:
        for ev_percentage in ev_values:
            if (gd_percentage == 0 or gd_percentage == 100) and (ev_percentage == 0 or ev_percentage == 100):
                # Para 0% ou 100% de GD e EV, só use random_seed=1
                total_scenarios += 1
            else:
                # Para outros casos, use todos os random seeds especificados
                total_scenarios += len(rs_values)
    
    log_progress(f"Total de cenários a serem gerados: {total_scenarios}", log_file)
    
    # Contadores para estatísticas
    scenario_count = 0
    success_count = 0
    skip_count = 0
    error_count = 0
    
    # Registrar tempo de início
    start_time = time.time()
    
    # Gerar todos os cenários do subconjunto
    for gd_percentage in gd_values:
        for ev_percentage in ev_values:
            # Determinar quais random seeds usar para este cenário
            if (gd_percentage == 0 or gd_percentage == 100) and (ev_percentage == 0 or ev_percentage == 100):
                # Para 0% ou 100% de GD e EV, só use random_seed=1
                seeds_to_use = [1]
            else:
                # Para outros casos, use todos os random seeds especificados
                seeds_to_use = rs_values
            
            for random_seed in seeds_to_use:
                scenario_count += 1
                
                log_progress(f"Processando cenário {scenario_count}/{total_scenarios}: GD={gd_percentage}%, EV={ev_percentage}%, RS={random_seed}", log_file)
                
                # Executar o DSSWriter para este cenário
                success = run_dsswriter_for_scenario(gd_percentage, ev_percentage, random_seed)
                
                if success:
                    success_count += 1
                else:
                    # Verificar se é um erro ou se o diretório já existia
                    if os.path.exists(os.path.join(BASE_PATH, f"GD{gd_percentage}--EV{ev_percentage}--RS{random_seed}")):
                        skip_count += 1
                    else:
                        error_count += 1
                
                # Calcular progresso e tempo estimado restante
                elapsed_time = time.time() - start_time
                avg_time_per_scenario = elapsed_time / scenario_count
                remaining_scenarios = total_scenarios - scenario_count
                estimated_remaining_time = avg_time_per_scenario * remaining_scenarios
                
                # Registrar progresso
                log_progress(f"Progresso: {scenario_count}/{total_scenarios} ({scenario_count/total_scenarios*100:.1f}%)", log_file)
                log_progress(f"Tempo estimado restante: {estimated_remaining_time/60:.1f} minutos", log_file)
    
    # Registrar estatísticas finais
    total_time = time.time() - start_time
    log_progress(f"Geração de cenários concluída em {total_time/60:.1f} minutos", log_file)
    log_progress(f"Total: {scenario_count} cenários | {success_count} sucessos | {skip_count} ignorados | {error_count} erros", log_file)

if __name__ == "__main__":
    # Verificar argumentos da linha de comando
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Uso: python cenarios-generator.py [opções]")
            print("Opções:")
            print("  --all                Gerar todos os cenários")
            print("  --gd valores         Lista de valores de GD (ex: 0 25 50)")
            print("  --ev valores         Lista de valores de EV (ex: 0 25 50)")
            print("  --rs-start valor     Valor inicial de random seed (padrão: 1)")
            print("  --rs-end valor       Valor final de random seed (padrão: 51)")
            sys.exit(0)
        
        # Processar argumentos
        if "--all" in sys.argv:
            # Gerar todos os cenários
            print("Gerando todos os cenários...")
            generate_all_scenarios()
        else:
            # Gerar subconjunto de cenários
            gd_values = None
            ev_values = None
            rs_start = 1
            rs_end = 51
            
            # Processar --gd
            if "--gd" in sys.argv:
                idx = sys.argv.index("--gd")
                if idx + 1 < len(sys.argv):
                    gd_values = []
                    i = idx + 1
                    while i < len(sys.argv) and not sys.argv[i].startswith("--"):
                        try:
                            gd_values.append(int(sys.argv[i]))
                        except ValueError:
                            pass
                        i += 1
            
            # Processar --ev
            if "--ev" in sys.argv:
                idx = sys.argv.index("--ev")
                if idx + 1 < len(sys.argv):
                    ev_values = []
                    i = idx + 1
                    while i < len(sys.argv) and not sys.argv[i].startswith("--"):
                        try:
                            ev_values.append(int(sys.argv[i]))
                        except ValueError:
                            pass
                        i += 1
            
            # Processar --rs-start
            if "--rs-start" in sys.argv:
                idx = sys.argv.index("--rs-start")
                if idx + 1 < len(sys.argv):
                    try:
                        rs_start = int(sys.argv[idx + 1])
                    except ValueError:
                        pass
            
            # Processar --rs-end
            if "--rs-end" in sys.argv:
                idx = sys.argv.index("--rs-end")
                if idx + 1 < len(sys.argv):
                    try:
                        rs_end = int(sys.argv[idx + 1])
                    except ValueError:
                        pass
            
            # Gerar subconjunto de cenários
            print(f"Gerando subconjunto de cenários:")
            print(f"  GD: {gd_values if gd_values else GD_PERCENTAGES}")
            print(f"  EV: {ev_values if ev_values else EV_PERCENTAGES}")
            print(f"  RS: {rs_start} a {rs_end}")
            generate_subset_scenarios(gd_values, ev_values, rs_start, rs_end)
    else:
        # Sem argumentos - gerar todos os cenários
        print("Gerando todos os cenários...")
        generate_all_scenarios()