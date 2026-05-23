import sys
import json
from pathlib import Path

# Kök dizini yola ekle
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.research_engine.database import save_study

STUDIES_DIR = ROOT / "data" / "studies"

def main():
    if not STUDIES_DIR.exists():
        print("[-] Studies dizini bulunamadı. Aktarılacak veri yok.")
        return

    migrated_count = 0
    for metadata_path in STUDIES_DIR.glob("*/metadata.json"):
        study_dir = metadata_path.parent
        print(f"[*] Aktarılıyor: {study_dir.name}")
        
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"[-] Metadata okunamadı {study_dir.name}: {e}")
            continue

        metadata["id"] = metadata.get("id") or study_dir.name
        
        payload = {}
        for file_name, key in [
            ("brief.json", "brief"),
            ("roles.json", "roles"),
            ("plan.json", "plan"),
            ("personas.json", "personas"),
            ("script.json", "script"),
            ("interviews.json", "interviews"),
            ("report.json", "report_json"),
        ]:
            target = study_dir / file_name
            if target.exists():
                try:
                    payload[key] = json.loads(target.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass
                    
        markdown_path = study_dir / "report.md"
        if markdown_path.exists():
            payload["report_markdown"] = markdown_path.read_text(encoding="utf-8")
            
        try:
            save_study(metadata, payload)
            migrated_count += 1
            print(f"[+] Başarıyla aktarıldı: {metadata['id']}")
        except Exception as e:
            print(f"[-] Veritabanı hatası {metadata['id']}: {e}")

    print(f"\n[OK] Veri taşıma (migration) tamamlandı! Toplam {migrated_count} çalışma SQLite'a aktarıldı.")

if __name__ == "__main__":
    main()
