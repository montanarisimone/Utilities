import yaml
import csv
import sys
from pathlib import Path

def get_api_name(yaml_content):
    """
    Estrae il nome dell'API dal contenuto YAML.
    """
    return yaml_content.get('info', {}).get('title', 'default_api')

def extract_properties(yaml_content):
    """
    Estrae le definizioni e le relative proprietà dal file YAML.
    Restituisce una lista di tuple con le informazioni richieste per ogni campo.
    """
    results = []
    
    # Estrae la sezione definitions
    definitions = yaml_content.get('definitions', {})
    
    # Itera su ogni definizione
    for def_name, def_content in definitions.items():
        # Ottiene la lista dei campi required
        required_fields = def_content.get('required', [])
        
        # Ottiene le properties dell'oggetto
        properties = def_content.get('properties', {})
        
        # Per ogni proprietà, estrae tutte le informazioni richieste
        for prop_name, prop_details in properties.items():
            # Determina se il campo è obbligatorio
            is_required = 'Si' if prop_name in required_fields else 'No'
            
            # Estrae i dettagli della proprietà, usando None se non presenti
            prop_type = prop_details.get('type')
            prop_example = prop_details.get('example')
            prop_description = prop_details.get('description')
            
            # Gestisce il caso speciale di $ref
            if '$ref' in prop_details:
                prop_type = prop_details['$ref']
            
            # Se la proprietà è un array, include anche il tipo degli elementi
            if prop_type == 'array' and 'items' in prop_details:
                if '$ref' in prop_details['items']:
                    prop_type = f"array of {prop_details['items']['$ref']}"
                elif 'type' in prop_details['items']:
                    prop_type = f"array of {prop_details['items']['type']}"
            
            # Gestisce i formati speciali (come date-time, uuid)
            if 'format' in prop_details:
                prop_type = f"{prop_type} ({prop_details['format']})"
            
            results.append((
                def_name,          # nome_oggetto
                prop_name,         # nome_campo
                is_required,       # campo_obbligatorio
                prop_type,         # campo_tipo
                prop_example,      # campo_esempio
                prop_description   # campo_descrizione
            ))
    
    return results

def yaml_to_csv(input_file):
    """
    Converte il file YAML in CSV con tutte le colonne richieste.
    Il nome del file di output è basato sul titolo dell'API.
    """
    # Legge il file YAML
    with open(input_file, 'r', encoding='utf-8') as f:
        yaml_content = yaml.safe_load(f)
    
    # Ottiene il nome dell'API per il file di output
    api_name = get_api_name(yaml_content)
    output_file = f"{api_name}.csv"
    
    # Estrae le proprietà con tutte le informazioni
    properties_list = extract_properties(yaml_content)
    
    # Scrive il file CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Scrive l'header
        writer.writerow([
            'nome_oggetto',
            'nome_campo',
            'campo_obbligatorio',
            'campo_tipo',
            'campo_esempio',
            'campo_descrizione'
        ])
        
        # Scrive i dati
        for row in properties_list:
            # Converte eventuali None in stringhe vuote
            row_cleaned = ['' if x is None else str(x) for x in row]
            writer.writerow(row_cleaned)
    
    return output_file

def main():
    # Controllo degli argomenti
    if len(sys.argv) != 2:
        print("Uso: python script.py input.yaml")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Verifica che il file di input esista
    if not Path(input_file).exists():
        print(f"Errore: Il file {input_file} non esiste")
        sys.exit(1)
    
    try:
        output_file = yaml_to_csv(input_file)
        print(f"Conversione completata. Output salvato in {output_file}")
    except Exception as e:
        print(f"Errore durante la conversione: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
