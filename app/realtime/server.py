"""Trang thử gợi ý sau mỗi từ. Chạy từ thư mục gốc repo:  python -m app.realtime.server  -> http://localhost:8765

Streamlit chỉ nhận chữ khi rời ô nhập nên không gợi ý lúc gõ được; ở đây trang HTML nói chuyện với server qua WebSocket.
Mỗi kết nối có một `Session`. Tầng từ điển chạy ngay; tầng ViT5 chỉ chạy khi trang báo người dùng đã dừng tay, và bỏ kết
quả nếu câu đã đổi trong lúc chạy. Log lựa chọn: outputs/logs/realtime_history.jsonl
"""
import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http import HTTPStatus
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # mô hình đã có sẵn, tránh tự tải thêm từ Hub

from websockets.asyncio.server import serve  # noqa: E402
from websockets.datastructures import Headers  # noqa: E402
from websockets.http11 import Response  # noqa: E402

from src.correction.predict import from_config as load_corrector  # noqa: E402
from src.lexicon.candidates import Lexicon  # noqa: E402
from src.realtime.session import Session  # noqa: E402
from src.utils.text_utils import load_config  # noqa: E402

PAGE = Path(__file__).with_name("index.html")
HISTORY = Path("outputs/logs/realtime_history.jsonl")
HOST, PORT = "localhost", 8765


def log_choice(entry: dict) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M:%S"), **entry}, ensure_ascii=False) + "\n")


def serve_page(connection, request):
    if request.path == "/ws":
        return None
    if request.path != "/":
        return connection.respond(HTTPStatus.NOT_FOUND, "Not found\n")
    body = PAGE.read_bytes()
    headers = Headers([("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body))),
                       ("Cache-Control", "no-store")])
    return Response(200, "OK", headers, body)


class App:
    def __init__(self, config: str = "configs/lexicon.yaml"):
        cfg = load_config(config)
        self.params = cfg["params"]
        self.lex = Lexicon.from_config(cfg)
        print("Đang nạp mô hình...", flush=True)
        self.corrector = load_corrector(config=cfg["correction_config"])
        self.pool = ThreadPoolExecutor(max_workers=1)  # GPU chỉ chạy một việc một lúc
        print(f"Sẵn sàng: http://{HOST}:{PORT}", flush=True)

    def score(self, reqs):
        flat = self.corrector.score_pairs([r[1] for r in reqs for _ in r[2]], [c for r in reqs for c in r[2]])
        out, pos = [], 0
        for r in reqs:
            out.append(flat[pos:pos + len(r[2])])
            pos += len(r[2])
        return out

    async def handle(self, ws):
        p = self.params
        session = Session(self.lex, k=p["k"], alpha=p["alpha"], beta=p["beta"])
        latest = 0

        async def send(seq, ms=None, model_ms=None):
            await ws.send(json.dumps({"seq": seq, "words": session.state(), "ms": ms, "model_ms": model_ms}, ensure_ascii=False))

        async for message in ws:
            data = json.loads(message)
            seq = latest = data["seq"]
            if data["type"] == "update":
                t0 = time.perf_counter()
                session.sync(data["text"])
                await send(seq, ms=round((time.perf_counter() - t0) * 1000, 1))
            elif data["type"] == "choose":
                w = session.words[data["i"]]
                log_choice({"raw": w.raw, "chosen": data["option"], "options": [c for c, _ in w.options[:session.top]],
                            "context": data["text"]})
                session.choose(data["i"], data["option"].lower())
                session.sync(data["text"])
                await send(seq)
            elif data["type"] == "pause":
                reqs = session.refine_requests()
                if not reqs:
                    continue

                async def run(reqs, seq):
                    t0 = time.perf_counter()
                    scores = await asyncio.get_running_loop().run_in_executor(self.pool, partial(self.score, reqs))
                    if seq == latest:  # người dùng chưa gõ thêm thì kết quả mới còn đúng
                        session.apply_refine(reqs, scores)
                        await send(seq, model_ms=round((time.perf_counter() - t0) * 1000))

                asyncio.create_task(run(reqs, seq))


async def main():
    app = App()
    async with serve(app.handle, HOST, PORT, process_request=serve_page):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
