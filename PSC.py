import os
import pandas as pd
import json
from docxtpl import DocxTemplate
from debug import thorough_clean_runs

def process_attendance(teams_csv_path, directory_csv_path):
    """
    Parses the messy Teams CSV, isolates the 'Participants' block, 
    and merges it with the static Master Directory.
    """
    # 1. Read the raw Teams CSV
    with open(teams_csv_path, 'r', encoding='utf-16') as f: # Teams CSVs are often UTF-16
        lines = f.readlines()
        
    # Find where the Participants table starts
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("Name\tFirst Join"): # Teams usually uses tabs in its native CSV exports
            start_idx = i
            break
            
    # Extract the actual participant rows
    participant_lines = lines[start_idx:]
    
    # Save temporarily to parse cleanly with pandas
    temp_path = "temp_participants.csv"
    with open(temp_path, 'w', encoding='utf-16') as f:
        f.writelines(participant_lines)
    
    ## NEW HEURISTIC: Truncate dataframe at the first NaN in Email
    # Read the clean participant block and the master directory
    df_teams = pd.read_csv(temp_path, sep='\t', encoding='utf-16')

    invalid_rows = df_teams[df_teams['Email'].isna()]
    if not invalid_rows.empty:
        cutoff_index = invalid_rows.index[0]
        df_teams = df_teams.iloc[:cutoff_index]
    
    # Clean the Email columns for a deterministic join
    df_teams['Email'] = df_teams['Email'].str.strip().str.lower()

    df_dir = pd.read_csv(directory_csv_path)
    
    # Clean the Email column in Teams output (often comes out weird)
    df_teams['Email'] = df_teams['Email'].str.strip().str.lower()
    df_dir['Email'] = df_dir['Email'].str.strip().str.lower()
    
    # Perform a Left Join to enrich the data
    df_merged = pd.merge(df_teams, df_dir, on="Email", how="left")
    
    # Fill NaN values for people not in the directory
    df_merged['Designation'] = df_merged['Designation'].fillna("External / Unknown")
    df_merged['Abbreviation'] = df_merged['Abbreviation'].fillna("EXT")
    df_merged['Attended'] = "Y" # If they are in the Teams CSV, they attended
    
    # Convert to a list of dictionaries for DocxTemplate
    return df_merged.to_dict(orient='records')

def main():
    # File Paths
    teams_csv = "Input_PSC/Meeting ABC UpdateCommittee DEF #5 - Attendance report 6-08-26.csv"
    master_dir = "Input_PSC/directory.csv"
    template_path = "Templates/MoM_Template_PSC.docx"
    json_data_path = "Input_PSC/transcript_data.json"
    output_path = "Output_PSC/MoM_PSC.docx"
    file_to_delete = "temp_participants.csv"

    # 1. Process Deterministic Data (Attendance)
    print("Processing attendance data...")
    attendees = process_attendance(teams_csv, master_dir)

    # 2. Load Stochastic Data (Mock LLM JSON)
    print("Loading transcript data...")
    with open(json_data_path, 'r') as f:
        context = json.load(f)

    # 3. Combine payloads
    context["attendees"] = attendees

    # 4. Render the Word Document
    print("Rendering MoM template...")
    doc = DocxTemplate(template_path)
    doc.get_docx()
    thorough_clean_runs(doc)
    doc.render(context)
    doc.save(output_path)
    
    print(f"Success! Document saved to {output_path}")
    if os.path.exists(file_to_delete):
        os.remove(file_to_delete)
    print(f"Cleaned up temporary file: {file_to_delete}")

if __name__ == "__main__":
    main()