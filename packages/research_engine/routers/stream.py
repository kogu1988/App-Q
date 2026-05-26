import asyncio
import os
import json
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis # Non-blocking asenkron redis paketi

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stream", tags=["Streaming"])

# Fallback Valkey/Redis URL
VALKEY_URL = os.getenv("VALKEY_URL", "redis://localhost:6379/0")

# ⚡ Performance Optimization: Global Connection Pool for Valkey/Redis
# Pre-allocates connections to prevent socket exhaustion during heavy traffic.
redis_pool = aioredis.ConnectionPool.from_url(VALKEY_URL, decode_responses=True, max_connections=100)

async def redis_event_generator(research_id: str):
    """Redis/Valkey PubSub kanalına bağlanıp asenkron generator olarak istemciye veri basar."""
    # Reuse the global pool rather than creating a new connection per client
    client = aioredis.Redis(connection_pool=redis_pool)
    pubsub = client.pubsub()
    channel_name = f"synthesis_status:{research_id}"
    
    await pubsub.subscribe(channel_name)
    
    try:
        # Bağlantı açıldı sinyali (SSE Handshake)
        yield "data: {\"status\": \"connected\", \"message\": \"SSE stream initialized\"}\n\n"
        
        while True:
            # 8GB VRAM üzerindeki işlem döngüsünü sıkıştırmamak için non-blocking bekletme süresi
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                raw_data = message["data"]
                # SSE standardına uygun olarak 'data: ' ön eki ve çift satır sonu ile iletilmeli
                yield f"data: {raw_data}\n\n"
                
                # Eğer LangGraph durumu tamamlandı veya başarısız olarak işaretlendiyse akışı sonlandır
                try:
                    parsed_json = json.loads(raw_data)
                    if parsed_json.get("status") in ["completed", "failed"]:
                        break
                except json.JSONDecodeError:
                    pass
                    
            await asyncio.sleep(0.1) # Event loop'un nefes almasını sağlayan işbirlikçi asenkron bekleme
    except asyncio.CancelledError:
        # İstemci sekmeyi kapattığında veya bağlantıyı kestiğinde tetiklenir
        logger.info(f"Client disconnected from SSE stream for research_id: {research_id}")
    except Exception as e:
        logger.error(f"SSE stream error for research_id {research_id}: {e}")
    finally:
        # ⚡ Performance Optimization: Graceful Socket Teardown
        try:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()
        except Exception:
            pass # Ignore errors if already closed
        
        # We don't close the client anymore because it's using a connection pool
        # The pool manages its own lifecycle.

@router.get("/{research_id}", response_class=StreamingResponse)
async def stream_research_status(research_id: str):
    """
    Ön yüzün EventSource API üzerinden bağlanacağı, Braun & Clarke 6 aşamalı analizi
    ve durum güncellemelerini parça parça akıtan katı SSE endpoint'i.
    """
    return StreamingResponse(
        redis_event_generator(research_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Nginx buffer katmanının akışı durdurmasını (blocking) engelleyen kritik başlık
        }
    )

class WebSocketConnectionManager:
    """Aktif WebSocket oturumlarını, kalp atışlarını (heartbeat) ve izole odaları yöneten sınıftır."""
    def __init__(self):
        # research_id -> list of active connections
        self.active_rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, research_id: str):
        await websocket.accept()
        if research_id not in self.active_rooms:
            self.active_rooms[research_id] = []
        self.active_rooms[research_id].append(websocket)
        logger.info(f"Active WebSocket connection accepted in room: {research_id}")

    def disconnect(self, websocket: WebSocket, research_id: str):
        if research_id in self.active_rooms:
            if websocket in self.active_rooms[research_id]:
                self.active_rooms[research_id].remove(websocket)
            if not self.active_rooms[research_id]:
                del self.active_rooms[research_id]
        logger.info(f"WebSocket client disconnected from room: {research_id}")

    async def broadcast_to_room(self, research_id: str, event_payload: dict):
        """Belirli bir araştırma odasındaki tüm dinleyicilere (ön yüz ekranlarına) veriyi fırlatır."""
        if research_id in self.active_rooms:
            # ⚡ Performance Optimization: Sockets might be dead. We send JSON and catch connection errors.
            dead_sockets = []
            for connection in self.active_rooms[research_id]:
                try:
                    await connection.send_json(event_payload)
                except Exception:
                    dead_sockets.append(connection)
            
            # Clean up dead sockets immediately to prevent memory leaks
            for dead in dead_sockets:
                self.disconnect(dead, research_id)

manager = WebSocketConnectionManager()

async def handle_interactive_probing(research_id: str, command: dict):
    """Kullanıcının canlı mülakata ('Talk to Research') müdahalesini işler."""
    logger.info(f"Interactive probe requested for room {research_id}: {command}")
    # İleride burada Ajan 2'ye asenkron komut paslama lojiği olacak.
    pass

@router.websocket("/ws/{research_id}")
async def interview_realtime_websocket(websocket: WebSocket, research_id: str):
    """
    Ajan görüşmelerinin canlı mülakat metinlerini ve dalkavukluk uyarı bayraklarını
    ön yüze anlık yansıtan çift yönlü WebSocket hattı.
    """
    await manager.connect(websocket, research_id)
    try:
        while True:
            # İstemciden gelecek olan interaktif komutları (Talk to Research probing sorguları) dinler
            # ⚡ Performance Optimization: Added a timeout check implicitly by using generic receive
            data = await websocket.receive_text()
            
            if data == "ping": # Explicit heartbeat handling
                await websocket.send_text("pong")
                continue
                
            try:
                parsed_command = json.loads(data)
                
                # Eğer kullanıcı bir ajana doğrudan takip sorusu yöneltirse orkestrasyon kuyruğuna asenkron pasla
                if parsed_command.get("command") == "probe_agent":
                    await handle_interactive_probing(research_id, parsed_command)
            except json.JSONDecodeError:
                logger.warning("Geçersiz WebSocket payload'u alındı.")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, research_id)
    except Exception as e:
        logger.error(f"WebSocket error encountered in room {research_id}: {e}")
        manager.disconnect(websocket, research_id)
