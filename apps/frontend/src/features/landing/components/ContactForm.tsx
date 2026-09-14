"use client";

import { useState } from "react";
import { toast } from "sonner";

/** İletişim formu (refactor R4-1). */
export function ContactForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !message.trim()) {
      toast.error("Lütfen tüm alanları doldurun.");
      return;
    }
    setSending(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${API_BASE}/api/client/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), email: email.trim(), message: message.trim() }),
      });
      if (!res.ok) throw new Error("Gönderilemedi.");
      toast.success("Mesajınız iletildi! En kısa sürede dönüş yapacağız.");
      setName(""); setEmail(""); setMessage("");
    } catch {
      toast.error("Mesaj gönderilemedi. Lütfen hiclarere@clarere.com adresine e-posta atın.");
    } finally {
      setSending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-[8px] border border-[#d9d9dd] p-6 sm:p-8 space-y-5">
      <div>
        <label className="block text-sm font-medium text-[#212121] mb-1.5">Adınız</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Adınız Soyadınız"
          className="w-full px-4 py-2.5 rounded-[8px] border border-[#d9d9dd] text-sm focus:outline-none focus:ring-2 focus:ring-[#17171c]/20 focus:border-[#17171c] transition-colors"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-[#212121] mb-1.5">E-posta</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="ornek@email.com"
          className="w-full px-4 py-2.5 rounded-[8px] border border-[#d9d9dd] text-sm focus:outline-none focus:ring-2 focus:ring-[#17171c]/20 focus:border-[#17171c] transition-colors"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-[#212121] mb-1.5">Mesajınız</label>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Bize iletmek istediğiniz mesaj..."
          rows={4}
          className="w-full px-4 py-2.5 rounded-[8px] border border-[#d9d9dd] text-sm focus:outline-none focus:ring-2 focus:ring-[#17171c]/20 focus:border-[#17171c] transition-colors resize-none"
        />
      </div>
      <button
        type="submit"
        disabled={sending}
        className="w-full py-3 rounded-full bg-[#17171c] text-white text-sm font-semibold hover:bg-[#17171c]/85 transition-colors disabled:opacity-50"
      >
        {sending ? "Gönderiliyor..." : "Gönder"}
      </button>
    </form>
  );
}
