import os
from pathlib import Path
from llama_parse import LlamaParse
from typing import List, Dict
import json

def process_pdfs(pdf_dir: str, output_dir: str) -> None:
    """
    Process all PDFs in the given directory using LlamaParse and save the results.
    
    Args:
        pdf_dir (str): Directory containing PDF files
        output_dir (str): Directory to save processed results
    """
    # Initialize LlamaParse
    parser = LlamaParse()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    # Process each PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        output_path = os.path.join(output_dir, f"{Path(pdf_file).stem}.json")
        
        print(f"Processing {pdf_file}...")
        
        try:
            # Parse the PDF
            result = parser.parse(pdf_path)
            
            # Save the result
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
                
            print(f"Successfully processed {pdf_file}")
            
        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")

if __name__ == "__main__":
    pdf_dir = "rag_docs/pdfs"
    output_dir = "rag_docs/parsed_pdfs"
    process_pdfs(pdf_dir, output_dir) 