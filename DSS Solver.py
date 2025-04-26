import os
import sys
import time
import traceback
from datetime import datetime, timedelta
import py_dss_interface

# Configurações
BASE_PATH = r"C:\DSSFiles3"
LOG_FILE = os.path.join(BASE_PATH, "dss_solver_progress.log")

def log_message(message, log_file=None, print_to_console=True):
    """Registra mensagens no arquivo de log e na tela"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    
    if print_to_console:
        print(log_message)
    
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")

def find_all_dss_files():
    """Encontra todos os arquivos DSS no diretório base e subdiretórios"""
    dss_files = []
    
    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            if file.endswith(".dss") and file.startswith("kW="):
                dss_files.append(os.path.join(root, file))
    
    return sorted(dss_files)  # Ordenar por caminho

def solve_dss_file(dss_path, dss_instance=None):
    """Resolve um arquivo DSS específico - versão ultra-mínima"""
    try:
        # Criar nova instância DSS se não fornecido
        if dss_instance is None:
            dss = py_dss_interface.DSSDLL()
        else:
            dss = dss_instance
        
        # Limpar e compilar - tão simples quanto possível
        dss.text("clear")
        dss.text(f"compile \"{dss_path}\"")
        dss.text("solve")
        
        return True, "Sucesso"
    
    except Exception as e:
        error_trace = traceback.format_exc()
        return False, f"Erro inesperado: {str(e)}\n{error_trace}"

def main():
    # Iniciar o arquivo de log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Iniciando solução em lote dos arquivos OpenDSS em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Encontrar todos os arquivos DSS
    log_message("Buscando arquivos DSS...", LOG_FILE)
    dss_files = find_all_dss_files()
    total_files = len(dss_files)
    log_message(f"Encontrados {total_files} arquivos DSS para processar.", LOG_FILE)
    
    if total_files == 0:
        log_message("Nenhum arquivo encontrado. Verifique o diretório base.", LOG_FILE)
        return
    
    # Inicializar contadores
    processed = 0
    successful = 0
    failed = 0
    start_time = time.time()
    
    # Criar uma única instância do DSS para reutilização
    dss = py_dss_interface.DSSDLL()
    log_message("Instância do OpenDSS inicializada.", LOG_FILE)
    
    # Processar cada arquivo
    for dss_file in dss_files:
        processed += 1
        
        # Calcular estatísticas de progresso
        elapsed_time = time.time() - start_time
        avg_time_per_file = elapsed_time / processed if processed > 1 else 0
        remaining_files = total_files - processed
        estimated_remaining_time = avg_time_per_file * remaining_files
        eta = datetime.now() + timedelta(seconds=estimated_remaining_time)
        
        # Extrair informações do cenário do caminho do arquivo
        try:
            scenario_folder = os.path.basename(os.path.dirname(os.path.dirname(dss_file)))
            file_name = os.path.basename(dss_file)
            
            # Parse GD, EV e RS do nome da pasta
            parts = scenario_folder.split('--')
            gd = parts[0].replace('GD', '')
            ev = parts[1].replace('EV', '')
            rs = parts[2].replace('RS', '')
        except:
            scenario_folder = "Desconhecido"
            file_name = os.path.basename(dss_file)
            gd = "N/A"
            ev = "N/A"
            rs = "N/A"
        
        # Log de progresso
        progress_pct = (processed / total_files) * 100
        log_message(f"Processando {processed}/{total_files} ({progress_pct:.1f}%): {scenario_folder}/{file_name}", LOG_FILE)
        log_message(f"Cenário: GD={gd}, EV={ev}, RS={rs}", LOG_FILE)
        
        if processed > 1:  # Evitar divisão por zero no primeiro arquivo
            log_message(f"Tempo médio por arquivo: {avg_time_per_file:.2f} segundos", LOG_FILE)
            log_message(f"Tempo estimado restante: {timedelta(seconds=int(estimated_remaining_time))}", LOG_FILE)
            log_message(f"ETA: {eta.strftime('%Y-%m-%d %H:%M:%S')}", LOG_FILE)
        
        # Resolver o arquivo
        start_solve_time = time.time()
        success, message = solve_dss_file(dss_file, dss)
        solve_time = time.time() - start_solve_time
        
        # Registrar resultado
        if success:
            successful += 1
            log_message(f"✓ Sucesso: {file_name} resolvido em {solve_time:.2f} segundos", LOG_FILE)
        else:
            failed += 1
            log_message(f"✗ Falha: {file_name} - {message}", LOG_FILE)
        
        # Mostrar estatísticas atuais
        log_message(f"Estatísticas: {successful} sucessos, {failed} falhas", LOG_FILE)
        
        # Linha em branco para separar os registros
        log_message("", LOG_FILE)
    
    # Estatísticas finais
    total_time = time.time() - start_time
    log_message("==== Resumo Final ====", LOG_FILE)
    log_message(f"Total de arquivos processados: {processed}", LOG_FILE)
    log_message(f"Sucessos: {successful}", LOG_FILE)
    log_message(f"Falhas: {failed}", LOG_FILE)
    log_message(f"Taxa de sucesso: {(successful/processed)*100 if processed > 0 else 0:.2f}%", LOG_FILE)
    log_message(f"Tempo total de execução: {timedelta(seconds=int(total_time))}", LOG_FILE)
    log_message(f"Tempo médio por arquivo: {total_time/processed if processed > 0 else 0:.2f} segundos", LOG_FILE)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_trace = traceback.format_exc()
        log_message(f"Erro fatal no script: {str(e)}\n{error_trace}", LOG_FILE)