"""Demo khung tin nhắn: gợi ý cả câu trong lúc gõ, bấm Gửi để sửa cả câu và diễn đạt lại.
Chạy từ thư mục gốc repo:  python -m app.realtime.server  -> http://localhost:8765

Streamlit chỉ nhận chữ khi rời ô nhập nên không gợi ý lúc gõ được; ở đây trang HTML nói chuyện với server qua WebSocket.
Mỗi kết nối có một `Session`. Tầng từ điển chạy ngay; tầng ViT5 chỉ chạy khi trang báo người dùng đã dừng tay, và bỏ kết
quả nếu câu đã đổi trong lúc chạy. Bấm Gửi: câu đã sửa (mô hình sửa cả câu) trả về trước, câu diễn đạt lại trả về sau.
Log: outputs/logs/realtime_history.jsonl
"""
import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")  # mô hình đã có sẵn, tránh tự tải thêm từ Hub

from websockets.asyncio.server import serve  # noqa: E402
from websockets.datastructures import Headers  # noqa: E402
from websockets.http11 import Response  # noqa: E402

from src.lexicon.candidates import Lexicon  # noqa: E402
from src.pipeline.assistant import from_config as load_pipeline  # noqa: E402
from src.realtime.session import Session  # noqa: E402
from src.utils.text_utils import load_config  # noqa: E402

PAGE = Path(__file__).with_name("index.html")
HISTORY = Path("outputs/logs/realtime_history.jsonl")
HOST, PORT = "localhost", 8765


def log_event(entry: dict) -> None:
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
        print("Đang nạp mô hình (sửa lỗi + diễn đạt lại)...", flush=True)
        self.pipeline = load_pipeline()  # configs/pipeline.yaml: cùng bộ sửa lỗi với configs/lexicon.yaml
        self.pool = ThreadPoolExecutor(max_workers=1)  # GPU chỉ chạy một việc một lúc
        print(f"Sẵn sàng: http://{HOST}:{PORT}", flush=True)

    def score(self, reqs):
        flat = self.pipeline.corrector.score_pairs([r[1] for r in reqs for _ in r[2]], [c for r in reqs for c in r[2]])
        out, pos = [], 0
        for r in reqs:
            out.append(flat[pos:pos + len(r[2])])
            pos += len(r[2])
        return out

    def paraphrase(self, text: str, corrected: str) -> dict:
        r = self.pipeline.suggest(text, corrected)
        if r["unknown_words"]:
            return {"text": None, "reason": "câu đã sửa còn từ nghi lỗi: " + ", ".join(r["unknown_words"])}
        if not r["suggestions"]:
            return {"text": None, "reason": "không có cách diễn đạt nào vừa giữ nghĩa vừa đủ khác"}
        return {"text": r["suggestions"][0]["text"], "reason": None}

    async def handle(self, ws):
        p = self.params
        session = Session(self.lex, k=p["k"], alpha=p["alpha"], beta=p["beta"])
        loop = asyncio.get_running_loop()
        latest, caret = 0, None

        async def send_state(seq, ms=None, model_ms=None):
            # danh sách gợi ý chỉ cho câu chứa con trỏ (tách câu theo . ! ?)
            await ws.send(json.dumps({"type": "state", "seq": seq, "words": session.state(),
                                      "rows": session.sentences(caret=caret), "ms": ms, "model_ms": model_ms},
                                     ensure_ascii=False))

        async def refine(reqs, seq):
            t0 = time.perf_counter()
            scores = await loop.run_in_executor(self.pool, self.score, reqs)
            if seq == latest:  # người dùng chưa gõ thêm thì kết quả mới còn đúng
                session.apply_refine(reqs, scores)
                await send_state(seq, model_ms=round((time.perf_counter() - t0) * 1000))

        async def submit(sent, seq):
            t0 = time.perf_counter()
            corr = await loop.run_in_executor(self.pool, self.pipeline.correct, sent)
            fixes = [c["text"] for c in corr["choices"]]
            await ws.send(json.dumps({"type": "fixes", "seq": seq, "rows": fixes,
                                      "ms": round((time.perf_counter() - t0) * 1000)}, ensure_ascii=False))
            t1 = time.perf_counter()
            para = await loop.run_in_executor(self.pool, self.paraphrase, sent, fixes[0])
            await ws.send(json.dumps({"type": "para", "seq": seq, **para, "ms": round((time.perf_counter() - t1) * 1000)},
                                     ensure_ascii=False))
            log_event({"event": "send", "input": sent, "fixes": fixes, "paraphrase": para["text"], "reason": para["reason"]})

        async for message in ws:
            data = json.loads(message)
            kind = data["type"]
            if kind == "update":
                latest, caret = data["seq"], data.get("caret")
                t0 = time.perf_counter()
                session.sync(data["text"])
                await send_state(latest, ms=round((time.perf_counter() - t0) * 1000, 1))
            elif kind == "caret":  # con trỏ chuyển sang câu khác mà chữ không đổi
                latest, caret = data["seq"], data["caret"]
                await send_state(latest)
            elif kind == "pause":
                reqs = session.refine_requests() if data["seq"] == latest else []
                if reqs:
                    asyncio.create_task(refine(reqs, latest))
            elif kind == "pick":  # bấm một câu trong danh sách lúc đang gõ; trang sẽ gửi "update" với câu mới ngay sau
                session.pick(data["picks"], data["first"])
                log_event({"event": "pick", "context": data["text"], "chosen": data["chosen"], "rank": data["rank"],
                           "rows": data["rows"]})
            elif kind == "send":
                asyncio.create_task(submit(data["text"], data["seq"]))
            elif kind == "use":  # bấm một câu trong danh sách sau khi Gửi
                log_event({"event": "use", "kind": data["kind"], "input": data["input"], "chosen": data["chosen"],
                           "rank": data["rank"]})


async def main():
    app = App()
    async with serve(app.handle, HOST, PORT, process_request=serve_page):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
