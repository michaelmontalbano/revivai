# ---- Step 1: Import Libraries ---- #
from fastapi import FastAPI, File, UploadFile
import fitz  # PyMuPDF (for PDF text extraction)
import os
import shutil
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from fastapi.exceptions import HTTPException

# ✅ Initialize FastAPI
app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# @app.post("/analyze_pdf/")
# async def analyze_pdf(file: UploadFile = File(...)):
#     return {"message": "PDF received!", "filename": file.filename}

@app.post("/analyze_pdf/")
async def analyze_pdf(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    print(f"Received file: {file.filename}")

    try:
        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"File saved at {pdf_path}")

        pdf_chunks = extract_text_from_pdf(pdf_path)
        print(f"Extracted text: {pdf_chunks[:100]}")  # Print first 100 characters

        structured_data = analyze_pdf_with_checkmarks(pdf_chunks)
        print(f"Structured Data: {structured_data}")

        return {"structured_response": structured_data}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# ✅ Set model path (Update this if needed)
model_path = "falcon-7b-instruct"

# ✅ Load tokenizer and model from local directory
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# ✅ Create text generation pipeline
generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=500,
    temperature=0.7,
    pad_token_id=tokenizer.eos_token_id
)

# ✅ Define folder for uploads
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---- Step 2: Extract Text from PDF ---- #
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n\n".join([page.get_text() for page in doc])
    doc.close()

    max_chunk_size = 1500
    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    return chunks

def analyze_pdf_with_checkmarks(text_chunks):
    if not text_chunks:
        return {"error": "No text extracted from PDF"}

    prompt = f"""
    You are an AI assistant analyzing a rehab intake form. Extract key insights:

    **1. Occupation:** Describe their job.
    **2. Experience in Rehab:** Any past treatments?
    **3. Psychological Insights:** Emotional state?
    **4. Family Support:** Who helps them?
    **5. Relapse Probability:** Based on history, estimate risk.

    Extracted Text:
    {text_chunks[0]}

    Provide a structured JSON output.
    """

    response = generator(prompt)
    print(f"AI Response: {response}")  # Debugging

    if not response:
        return {"error": "AI model failed to generate a response"}

    return {
        "occupation": response[0]["generated_text"].split("**1. Occupation:**")[-1].split("**2.")[0].strip(),
        "experience": response[0]["generated_text"].split("**2. Experience in Rehab:**")[-1].split("**3.")[0].strip(),
        "psychological_insight": response[0]["generated_text"].split("**3. Psychological Insights:**")[-1].split("**4.")[0].strip(),
        "family_support": response[0]["generated_text"].split("**4. Family Support:**")[-1].split("**5.")[0].strip(),
        "relapse_probability": response[0]["generated_text"].split("**5. Relapse Probability:**")[-1].strip(),
    }

