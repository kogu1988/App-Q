import uvicorn
import gc
import sys

def main():
    # 1. Ajan Hafıza Yönetimi (Memory Cleanup)
    print("Bellek temizleniyor (Garbage Collection)...")
    gc.collect()
    
    # 2. Uvicorn Başlatma (Reload Kapalı)
    print("Backend sunucusu başlatılıyor (Port 8000, Reload=False)...")
    try:
        # Ajan ortamında (sandbox) dosya izleyici çakışmalarını önlemek için reload=False
        # Performans için 4 işçi (worker) başlatılıyor.
        uvicorn.run("apps.backend.main:app", host="0.0.0.0", port=8000, reload=False, workers=4)
    except Exception as e:
        print(f"Sunucu başlatılırken hata oluştu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
