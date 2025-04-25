import fiona
import csv
import os
import pandas as pd
from tqdm import tqdm

# Caminho para o arquivo .gdb e tabelas específicas
gdb_path = r"C:\Users\bruno\OneDrive\Área de Trabalho\TCC\inputs\EMT2023\Energisa_MT_405_2023-12-31_V11_20240612-1317.gdb"
tables = [
    "UCBT_tab", "EQTRMT", "EQTRAT", "UNTRMT", "UNTRAT", "SSDMT",
    "SSDBT", "SEGCON", "RAMLIG", "CRVCRG", "BAR", "UGBT_tab", "CTMT", "PONNOT",
]
output_dir = r"C:\Users\bruno\OneDrive\Área de Trabalho\TCC\outputteste"

try:
    print("🚀 Iniciando o processo de conversão das tabelas para CSV...")
    # Lista camadas disponíveis
    layers = fiona.listlayers(gdb_path)
    print("✅ Camadas disponíveis carregadas com sucesso.")
    print("Camadas encontradas:", layers)
    
    for i, table_name in enumerate(tables, start=1):
        print(f"🔄 [{i}/{len(tables)}] Iniciando conversão da tabela: {table_name}")
        
        if table_name not in layers:
            print(f"⚠️ A camada '{table_name}' não foi encontrada. Pulando...")
            continue
        
        output_csv = os.path.join(output_dir, f"{table_name}.csv")
        
        print(f"📊 Extraindo dados da tabela '{table_name}'...")
        # Abre a camada corretamente
        with fiona.open(gdb_path, layer=table_name) as src:
            fieldnames = list(src.schema['properties'].keys())
            
            if src.schema['geometry']:
                fieldnames.append('geometry')
            
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            
            # Armazena os dados em uma lista de dicionários com barra de progresso
            data = []
            total_features = len(src)
            with tqdm(total=total_features, desc=f"Convertendo {table_name}", unit="registro", ncols=100) as pbar:
                for feature in src:
                    row = feature['properties']
                    if 'geometry' in fieldnames:
                        row['geometry'] = feature['geometry']
                    data.append(row)
                    pbar.update(1)
            
            print(f"✅ Dados da tabela '{table_name}' extraídos com sucesso.")
            
            # Converte para DataFrame para melhor organização
            df = pd.DataFrame(data)
            
            print(f"💾 Iniciando exportação para CSV: {output_csv}...")
            # Escrita manual com barra de progresso
            with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Escrevendo CSV {table_name}", unit="linha", ncols=100):
                    writer.writerow(row.to_dict())
            
            print(f"✅ Tabela '{table_name}' convertida com sucesso para: {output_csv}")
    
    print("🎯 Processo de conversão concluído com sucesso!")

except KeyboardInterrupt:
    print("❗ Operação interrompida manualmente pelo usuário.")

except Exception as e:
    print(f"❌ Erro ao converter: {e}")
