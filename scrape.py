from Bio import Entrez
import pandas as pd
from tqdm import tqdm
import time

Entrez.email == 'mcmontalbano3@gmail.com'


def search_pubmed(query, start_year=2005, end_year=2025, max_results=10000):
    query += f" AND ({start_year}:{end_year}[dp])"
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    return record["IdList"]

def fetch_details(id_list):
    ids = ",".join(id_list)
    handle = Entrez.efetch(db="pubmed", id=ids, rettype="medline", retmode="text")
    return handle.read()

def get_metadata(id_list):
    all_results = []
    for pmid in tqdm(id_list):
        time.sleep(0.2)  # Be respectful to API
        try:
            fetch = Entrez.efetch(db="pubmed", id=pmid, rettype="xml", retmode="text")
            data = Entrez.read(fetch)
            article = data["PubmedArticle"][0]["MedlineCitation"]["Article"]
            title = article.get("ArticleTitle", "")
            abstract = article.get("Abstract", {}).get("AbstractText", [""])[0]
            authors = [a['LastName'] + " " + a['ForeName'] for a in article.get("AuthorList", []) if "LastName" in a]
            date = article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {}).get("Year", "NA")
            all_results.append({
                "PMID": pmid,
                "Title": title,
                "Abstract": abstract,
                "Authors": ", ".join(authors),
                "Year": date
            })
        except Exception as e:
            print(f"Failed on {pmid}: {e}")
    return pd.DataFrame(all_results)

# 🔍 Example: search and extract
# ids = search_pubmed("addiction treatment", start_year=2005, end_year=2025)
# df = get_metadata(ids)
# df.to_csv("addiction_papers.csv", index=False)
import requests

url = 'https://aaaceus.com/course_content.asp?preview=1&course=139'
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    with open('course_content.html', 'w', encoding='utf-8') as file:
        file.write(response.text)
    print("The course content has been downloaded and saved as 'course_content.html'.")
else:
    print(f"Failed to retrieve the content. Status code: {response.status_code}")

