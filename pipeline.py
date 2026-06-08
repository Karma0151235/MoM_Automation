import pandas as pd
import json
from docxtpl import DocxTemplate

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
        
    # Read the clean participant block and the master directory
    df_teams = pd.read_csv(temp_path, sep='\t')
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
    teams_csv = "Input/Meeting ABC UpdateCommittee DEF #5 - Attendance report 6-08-26.csv"
    master_dir = "Input/directory.csv"
    template_path = "MoM_Template.docx"
    json_data_path = "Input/transcript_data.json"
    output_path = "Output/Final_MoM_Document.docx"

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
    doc.render(context)
    doc.save(output_path)
    
    print(f"Success! Document saved to {output_path}")

if __name__ == "__main__":
    main()