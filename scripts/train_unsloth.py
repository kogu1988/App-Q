"""
App-Q Yerel Model Egitim Hatti (Unsloth QLoRA)
RTX 4060 8GB VRAM icin ozel olarak optimize edilmistir.
Kullanim: python train_unsloth.py
"""
import os
import sys
from pathlib import Path

# RTX 4060 8GB VRAM optimizasyonlari
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

ROOT = Path(__file__).resolve().parents[1]

try:
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from unsloth.chat_templates import get_chat_template
except ImportError:
    print("Unsloth veya gerekli kutuphaneler kurulu degil.")
    print("Kurulum icin: pip install unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git")
    sys.exit(1)

def main():
    max_seq_length = 2048
    dtype = None # Auto
    load_in_4bit = True # 8GB VRAM icin sart
    
    dataset_path = ROOT / "data" / "finetuning" / "app_q_dataset.jsonl"
    if not dataset_path.exists():
        print(f"Veri seti bulunamadi: {dataset_path}")
        print("Once 'python scripts/prepare_finetuning_data.py' calistirin.")
        sys.exit(1)

    print("Model yukleniyor... Llama-3.1-8B-Instruct")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
        max_seq_length = max_seq_length,
        dtype = dtype,
        load_in_4bit = load_in_4bit,
    )
    
    print("LoRA Adapter ekleniyor...")
    model = FastLanguageModel.get_peft_model(
        model,
        r = 16, # LoRA rank
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj",],
        lora_alpha = 16,
        lora_dropout = 0,
        bias = "none",
        use_gradient_checkpointing = "unsloth",
        random_state = 3407,
        use_rslora = False,
        loftq_config = None,
    )
    
    # Veri seti formati ShareGPT/ChatML
    tokenizer = get_chat_template(
        tokenizer,
        chat_template = "llama-3",
        mapping = {"role": "from", "content": "value", "user": "human", "assistant": "gpt"},
    )
    
    def formatting_prompts_func(examples):
        convos = examples["conversations"]
        texts = [tokenizer.apply_chat_template(convo, tokenize = False, add_generation_prompt = False) for convo in convos]
        return { "text" : texts }

    print("Veri seti yukleniyor...")
    dataset = load_dataset("json", data_files=str(dataset_path), split="train")
    dataset = dataset.map(formatting_prompts_func, batched = True)
    
    print("Egitim (Training) basliyor...")
    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        dataset_num_proc = 2,
        packing = False, # Kisitli VRAM icin
        args = TrainingArguments(
            per_device_train_batch_size = 1, # RTX 4060 icin
            gradient_accumulation_steps = 8,
            warmup_steps = 5,
            max_steps = 60, # Demo icin 60 adim
            learning_rate = 2e-4,
            fp16 = not getattr(model, "is_bfloat16_supported", lambda: False)(),
            bf16 = getattr(model, "is_bfloat16_supported", lambda: False)(),
            logging_steps = 1,
            optim = "adamw_8bit",
            weight_decay = 0.01,
            lr_scheduler_type = "linear",
            seed = 3407,
            output_dir = "outputs",
        ),
    )
    
    trainer_stats = trainer.train()
    
    # Model kaydet
    output_dir = ROOT / "models" / "app-q-llama3-8b-lora"
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    
    print(f"Egitim tamamlandi. LoRA adapter su konuma kaydedildi: {output_dir}")
    
    # Opsiyonel: GGUF'a cevir ve Ollama Modelfile'a entegre et
    print("Ollama'da kullanmak icin Modelfile icerisine su satiri ekleyin:")
    print(f"ADAPTER {output_dir}")

if __name__ == "__main__":
    main()
