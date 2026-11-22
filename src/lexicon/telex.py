"""Giải mã Telex/VNI chưa được bộ gõ chuyển đổi: "nguowif" -> "người", "conf", "cofn" -> "còn", "to6i1" -> "tối".

Đây là luật chắc chắn, không cần mô hình. Hàm chỉ trả các dạng có thể có; có đúng là từ tiếng Việt hay không
do `Lexicon` kiểm tra bằng từ điển (vd "facebook" giải mã ra chuỗi vô nghĩa thì bị loại ở đó).
"""
import unicodedata

TONE_KEYS = {"s": "́", "f": "̀", "r": "̉", "x": "̃", "j": "̣"}
VNI_TONES = {"1": "́", "2": "̀", "3": "̉", "4": "̃", "5": "̣"}
CIRCUMFLEX = {"a": "â", "e": "ê", "o": "ô"}
HORN_OR_BREVE = {"a": "ă", "o": "ơ", "u": "ư"}
VOWELS = set("aăâeêioôơuưy")
MARKED = set("ăâêôơư")


def _vowel_positions(letters: list[str]) -> list[int]:
    """Vị trí nguyên âm, bỏ "u" trong "qu" và "i" trong "gi" khi theo sau là nguyên âm khác (thuộc phụ âm đầu)."""
    pos = [i for i, c in enumerate(letters) if c in VOWELS]
    if len(pos) > 1 and pos[0] == 1 and ((letters[0] == "q" and letters[1] == "u") or (letters[0] == "g" and letters[1] == "i")):
        pos = pos[1:]
    return pos


def _apply_w(letters: list[str]) -> bool:
    """Phím "w" (hoặc số 7, 8): "uo" -> "ươ", ngược lại đổi nguyên âm cuối có thể nhận dấu."""
    for i in range(len(letters) - 1):
        if letters[i] == "u" and letters[i + 1] == "o":
            letters[i], letters[i + 1] = "ư", "ơ"
            return True
    for i in range(len(letters) - 1, -1, -1):
        if letters[i] in HORN_OR_BREVE:
            letters[i] = HORN_OR_BREVE[letters[i]]
            return True
    return False


def _apply_circumflex(letters: list[str], vowel: str | None = None) -> bool:
    for i in range(len(letters) - 1, -1, -1):
        if letters[i] in CIRCUMFLEX and (vowel is None or letters[i] == vowel):
            letters[i] = CIRCUMFLEX[letters[i]]
            return True
    return False


def _place_tone(letters: list[str], tone: str, new_style: bool) -> str | None:
    """Đặt dấu thanh. Vần mở hai nguyên âm: kiểu cũ "hòa", kiểu mới "hoà" (trả cả hai để từ điển chọn)."""
    pos = _vowel_positions(letters)
    if not pos:
        return None
    marked = [i for i in pos if letters[i] in MARKED]
    if marked:
        target = marked[-1]
    elif pos[-1] < len(letters) - 1:  # có phụ âm cuối
        target = pos[-1]
    elif len(pos) == 1:
        target = pos[0]
    elif new_style and letters[pos[-2]] in "ou" and letters[pos[-1]] in "aey":
        target = pos[-1]
    else:
        target = pos[-2]
    out = list(letters)
    out[target] = out[target] + tone
    return unicodedata.normalize("NFC", "".join(out))


def _finish(letters: list[str], tone: str | None, changed: bool) -> list[str]:
    if not changed:
        return []
    if tone is None:
        return ["".join(letters)]
    forms = [_place_tone(letters, tone, False), _place_tone(letters, tone, True)]
    return list(dict.fromkeys(f for f in forms if f))


def _decode_telex(word: str) -> list[str]:
    letters: list[str] = []
    tone = None
    changed = False
    for c in word:
        if c == "d" and letters[:1] == ["d"] and len(letters) == 1:
            letters[0] = "đ"
            changed = True
        elif c in CIRCUMFLEX and c in letters and _apply_circumflex(letters, c):
            changed = True
        elif c == "w" and letters and _apply_w(letters):
            changed = True
        elif c in TONE_KEYS and tone is None and any(ch in VOWELS for ch in letters):
            tone = TONE_KEYS[c]  # s, f, r, x, j không bao giờ là phụ âm cuối nên sau nguyên âm chỉ có thể là dấu thanh
            changed = True
        else:
            letters.append(c)
    return _finish(letters, tone, changed)


def _decode_vni(word: str) -> list[str]:
    letters: list[str] = []
    tone = None
    changed = False
    for c in word:
        if c in VNI_TONES and tone is None and any(ch in VOWELS for ch in letters):
            tone, changed = VNI_TONES[c], True
        elif c == "6" and _apply_circumflex(letters):
            changed = True
        elif c == "7" and _apply_w(letters):
            changed = True
        elif c == "8" and "a" in letters:
            letters[letters.index("a")] = "ă"
            changed = True
        elif c == "9" and letters[:1] == ["d"]:
            letters[0] = "đ"
            changed = True
        elif c.isdigit():
            return []  # chữ số không thuộc VNI: mã, giờ, tiền
        else:
            letters.append(c)
    return _finish(letters, tone, changed)


def decode(word: str) -> list[str]:
    """Các dạng Telex/VNI có thể của `word` (chữ thường); rỗng nếu từ không dùng phím Telex/VNI nào."""
    word = word.lower()
    if not word.isascii() or not word.isalnum() or not any(c.isalpha() for c in word):
        return []
    return _decode_vni(word) if any(c.isdigit() for c in word) else _decode_telex(word)
