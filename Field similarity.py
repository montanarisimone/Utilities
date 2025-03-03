# il mapping viene eseguito basandosi su descrizione e nome campo, assegnando pesi diversi
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import numpy as np

def load_data(FileA, FileB):
    # Carica i file Excel
    A_df = pd.read_excel(FileA, sheet_name=0)
    B_df = pd.read_excel(FileB, sheet_name=0)
    
    # Seleziona solo le colonne rilevanti e resetta gli indici
    A_df = A_df[['TableA', 'DWHA', 'FieldA', 'DescriptionA']].dropna().reset_index(drop=True)
    B_df = B_df[['TableA', 'FieldB', 'DescriptionB']].dropna().reset_index(drop=True)
    
    return A_df, B_df

def find_best_matches(A_df, B_df, model_name='all-MiniLM-L6-v2', 
                     similarity_threshold=0.6, 
                     desc_weight=0.7, field_weight=0.4):
    """
    Trova le migliori corrispondenze tra FileA e FileB basandosi sia sulle descrizioni
    che sui nomi dei campi, con pesi personalizzabili.
    
    Args:
        A_df: DataFrame con i dati FileA
        B_df: DataFrame con i dati FileB
        model_name: Nome del modello SentenceTransformer
        similarity_threshold: Soglia minima di similarità
        desc_weight: Peso per la similarità delle descrizioni (default 0.7)
        field_weight: Peso per la similarità dei nomi dei campi (default 0.3)
    """
    # Carica il modello NLP
    model = SentenceTransformer(model_name)
    
    # CALCOLO SIMILARITÀ SULLE DESCRIZIONI
    A_descriptions = A_df['DescriptionA'].astype(str).tolist()
    B_descriptions = B_df['DescriptionB'].astype(str).tolist()
    
    A_desc_embeddings = model.encode(A_descriptions, convert_to_tensor=True)
    B_desc_embeddings = model.encode(B_descriptions, convert_to_tensor=True)
    
    # Similarità tra descrizioni
    desc_similarities = util.cos_sim(A_desc_embeddings, B_desc_embeddings)
    
    # CALCOLO SIMILARITÀ SUI NOMI DEI CAMPI
    A_field_names = A_df['Properties'].astype(str).tolist()
    B_field_names = B_df['Field'].astype(str).tolist()
    
    A_field_embeddings = model.encode(A_field_names, convert_to_tensor=True)
    B_field_embeddings = model.encode(B_field_names, convert_to_tensor=True)
    
    # Similarità tra nomi dei campi
    field_similarities = util.cos_sim(A_field_embeddings, B_field_embeddings)
    
    matches = []
    for i in range(len(A_df)):
        if i >= len(desc_similarities):
            continue
        
        # Converti i tensori in numpy arrays
        desc_sim_row = desc_similarities[i].cpu().numpy()
        field_sim_row = field_similarities[i].cpu().numpy()
        
        # Calcola la similarità combinata con i pesi specificati
        combined_sim = (desc_weight * desc_sim_row) + (field_weight * field_sim_row)
        
        # Ordina gli indici in base alla similarità combinata
        sorted_indices = combined_sim.argsort()[::-1]  # Ordine decrescente
        
        for best_match_idx in sorted_indices:
            combined_score = combined_sim[best_match_idx]
            
            # Applica la soglia di similarità
            if combined_score < similarity_threshold:
                break
            
            # Assicurati che l'indice sia un intero
            best_match_idx_int = int(best_match_idx)
            
            # Verifica che l'indice sia valido
            if best_match_idx_int >= len(B_df):
                continue
            
            # Recupera i punteggi di similarità individuali
            desc_score = float(desc_sim_row[best_match_idx])
            field_score = float(field_sim_row[best_match_idx])
            
            otr_row = B_df.iloc[best_match_idx_int]
            matches.append({
                "TableA": A_df.loc[i, 'TableA'],
                "DWHA": A_df.loc[i, 'DWHA'],
                "FieldA": A_df.loc[i, 'FieldA'],
                "TableB": otr_row['TableB'],
                "FieldB": otr_row['FieldB'],
                "Description_Similarity": desc_score,
                "Field_Similarity": field_score,
                "Combined_Similarity": float(combined_score)
            })
    
    # Crea il DataFrame risultante e ordina per similarità combinata
    result_df = pd.DataFrame(matches)
    if not result_df.empty:
        result_df = result_df.sort_values('Combined_Similarity', ascending=False)
    
    return result_df

def main():
    # Percorsi dei file Excel (modifica con i tuoi file locali)
    FileA = "FileA.xlsx"
    FileB = "FileB.xlsx"
    
    # Carica i dati
    A_df, B_df = load_data(FileA, FileB)
    
    print(f"Elaborazione di {len(A_df)} campi FileA e {len(B_df)} campi FileB...")
    
    # Trova le migliori corrispondenze
    # Puoi modificare i pesi qui: aumenta desc_weight per dare più importanza alle descrizioni
    # o aumenta field_weight per dare più importanza ai nomi dei campi
    matches_df = find_best_matches(
        A_df, 
        B_df, 
        similarity_threshold=0.5,  # Soglia più bassa per catturare più match potenziali
        desc_weight=0.7,           # 70% del peso alle descrizioni
        field_weight=0.3           # 30% del peso ai nomi dei campi
    )
    
    # Salva il risultato in un file CSV
    matches_df.to_csv("pre_mapping.csv", index=False)
    print(f"Mappatura completata! Trovate {len(matches_df)} corrispondenze.")
    print(f"File salvato come pre_mapping.csv")

if __name__ == "__main__":
    main()
