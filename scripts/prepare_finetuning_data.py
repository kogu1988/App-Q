import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.database import get_question_collection

def main():
    questions = get_question_collection()
    
    # Filter only liked questions
    liked_questions = [q for q in questions if q.get("is_liked")]
    
    if not liked_questions:
        print("Begenilen soru bulunamadi. Lutfen arayuzden sorulari 'begen' olarak isaretleyin.")
        sys.exit(0)
        
    dataset = []
    
    for q in liked_questions:
        context = q.get("purpose_context") or "Arastirma amaci belirtilmemis."
        title = q.get("research_title") or "Genel"
        category = q.get("research_category") or "Urun"
        
        # ShareGPT format
        conversation = {
            "conversations": [
                {
                    "from": "system",
                    "value": "Sen App-Q pazar arastirmasi sisteminin akilli soru asistanisin. Sana verilen baglama ve arastirma fikrine en uygun, derinlikli ve itiraz yakalayici pazar arastirmasi sorusunu uret."
                },
                {
                    "from": "human",
                    "value": f"Arastirma Konusu: {title}\nKategori: {category}\nArastirma Amaci: {context}\nBu baglamda kullaniciya sorulacak en stratejik ve derinlikli soru ne olmalidir?"
                },
                {
                    "from": "gpt",
                    "value": q["question"]
                }
            ]
        }
        dataset.append(conversation)
        
    out_dir = ROOT / "data" / "finetuning"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = out_dir / "app_q_dataset.jsonl"
    
    with open(out_file, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"[{len(dataset)} soru] ShareGPT formatinda hazirlandi: {out_file}")

if __name__ == "__main__":
    main()
