import csv
import json
import os

def markdown_table_to_json(markdown_table: str) -> list:
    lines = markdown_table.split("\n")
    dict_reader = csv.DictReader(lines, delimiter="|")
    data = []
    for row in list(dict_reader)[1:]:
        r = {k.strip(): v.strip() for k, v in row.items() if k != ""}
        data.append(r)
    return data


def format_training_example(narrative: str, techniques: list) -> str:
    
    techniques_json = json.dumps(techniques, indent=2, ensure_ascii=False)
    
    formatted_text = f'''Abaixo está uma narrativa de um incidente de segurança. Gere um JSON listando as técnicas MITRE ATT&CK, a descrição da atividade e as correções recomendadas.

### Narrativa:
{narrative.strip()}

### JSON:
{techniques_json}
'''
    
    return formatted_text


if __name__ == "__main__":
    raw_data_folder = "data/raw/situations"
    output_file = "data/training/training_data.jsonl"

    data = []

    for dirpath, dirnames, filenames in os.walk(raw_data_folder):
        narrativa_file = None
        tabela_file = None
        
        for filename in filenames:
            if filename.startswith("narrativa") and filename.endswith(".txt"):
                narrativa_file = os.path.join(dirpath, filename)
            if filename.startswith("tabela") and filename.endswith(".txt"):
                tabela_file = os.path.join(dirpath, filename)
        
        if narrativa_file and tabela_file:
            try:
                with open(narrativa_file, "r", encoding="latin-1") as f:
                    narrative = f.read()
                
                with open(tabela_file, "r", encoding="latin-1") as f:
                    markdown_content = f.read()
                
                techniques = markdown_table_to_json(markdown_content)
                
                formatted_text = format_training_example(narrative, techniques)
                
                data.append({"text": formatted_text})
                
                print(f"✓ Processado: {os.path.basename(dirpath)}")
            
            except Exception as e:
                print(f"{e}")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="latin-1") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
            
