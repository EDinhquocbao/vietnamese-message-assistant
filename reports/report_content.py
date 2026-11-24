"""Nội dung báo cáo đồ án (dùng với reports/build_report.py).

Quy ước trong chữ: **đậm**, *nghiêng*, `tên tệp` (nghiêng), [@khóa] = trích dẫn IEEE, «T:khóa» / «F:khóa» / «E:khóa» = số
bảng / hình / công thức (điền sau khi đánh số). Mọi số liệu lấy từ docs/improvement_plan.md và mục 14 file plan.
"""
import re

from build_report import (bullets, caption, equation, field, figure, frac, hat, heading, lim_low, mr, mt, nary, page_break,
                          para, paren, sign_block, sqrt, sub, sup, table)

INFO = {
    "title": "Hệ thống sửa lỗi chính tả và gợi ý diễn đạt cho tin nhắn tiếng Việt",
    "name": "Đinh Quốc Bảo",
    "mssv": "34802403236",
    "class": "24DAI",
    "teacher": "Th.S Trần Hàm Dương",
    "course": "Xử lý ngôn ngữ tự nhiên",
}

REFERENCES = {
    "vaswani": "A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser, and I. Polosukhin, “Attention is all you need,” in *Advances in Neural Information Processing Systems 30 (NIPS 2017)*, Long Beach, CA, USA, 2017, pp. 5998–6008.",
    "t5": "C. Raffel, N. Shazeer, A. Roberts, K. Lee, S. Narang, M. Matena, Y. Zhou, W. Li, and P. J. Liu, “Exploring the limits of transfer learning with a unified text-to-text transformer,” *Journal of Machine Learning Research*, vol. 21, no. 140, pp. 1–67, 2020.",
    "vit5": "L. Phan, H. Tran, H. Nguyen, and T. H. Trinh, “ViT5: Pretrained text-to-text transformer for Vietnamese language generation,” in *Proc. 2022 Conf. North American Chapter of the Association for Computational Linguistics: Human Language Technologies: Student Research Workshop*, Seattle, WA, USA, 2022, pp. 136–142.",
    "bartpho": "N. L. Tran, D. M. Le, and D. Q. Nguyen, “BARTpho: Pre-trained sequence-to-sequence models for Vietnamese,” in *Proc. Interspeech 2022*, Incheon, Korea, 2022, pp. 1751–1755.",
    "vsec": "D.-T. Do, H. T. Nguyen, T. N. Bui, and D. H. Vo, “VSEC: Transformer-based model for Vietnamese spelling correction,” in *PRICAI 2021: Trends in Artificial Intelligence*, Lecture Notes in Computer Science. Cham, Switzerland: Springer, 2021, pp. 259–272.",
    "hierarchical": "H. Tran, C. V. Dinh, L. Phan, and S. T. Nguyen, “Hierarchical transformer encoders for Vietnamese spelling correction,” arXiv:2105.13578, 2021.",
    "vilexnorm": "T.-N. Nguyen, T.-P. Le, and K. V. Nguyen, “ViLexNorm: A lexical normalization corpus for Vietnamese social media text,” in *Proc. 18th Conf. European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers)*, St. Julian’s, Malta, 2024, pp. 1421–1437.",
    "visolex": "A. T.-H. Nguyen, D. H. Nguyen, and K. V. Nguyen, “ViSoLex: An open-source repository for Vietnamese social media lexical normalization,” arXiv:2501.07020, 2025.",
    "visp": "S. Q. Nguyen and K. V. Nguyen, “A large-scale benchmark for Vietnamese sentence paraphrases,” in *Findings of the Association for Computational Linguistics: NAACL 2025*, Albuquerque, NM, USA, 2025, pp. 1045–1060.",
    "vec": "yammdd, “Vietnamese error correction corpus,” Hugging Face Datasets. [Online]. Available: https://huggingface.co/datasets/yammdd/vietnamese-error-correction-corpus (truy cập: 19/10/2026).",
    "nsw": "A. Hoang, “vn-nsw-dictionary: Vietnamese non-standard word dictionary,” GitHub repository. [Online]. Available: https://github.com/AnhHoang0529/vn-nsw-dictionary (truy cập: 09/11/2026).",
    "kernighan": "M. D. Kernighan, K. W. Church, and W. A. Gale, “A spelling correction program based on a noisy channel model,” in *Proc. 13th Int. Conf. Computational Linguistics (COLING 1990)*, vol. 2, Helsinki, Finland, 1990, pp. 205–210.",
    "brill": "E. Brill and R. C. Moore, “An improved error model for noisy channel spelling correction,” in *Proc. 38th Annu. Meeting of the Association for Computational Linguistics*, Hong Kong, 2000, pp. 286–293.",
    "symspell": "W. Garbe, “SymSpell: Symmetric delete spelling correction algorithm,” GitHub repository, 2012. [Online]. Available: https://github.com/wolfgarbe/SymSpell (truy cập: 09/11/2026).",
    "softmasked": "S. Zhang, H. Huang, J. Liu, and H. Li, “Spelling error correction with soft-masked BERT,” in *Proc. 58th Annu. Meeting of the Association for Computational Linguistics*, 2020, pp. 882–890.",
    "gector": "K. Omelianchuk, V. Atrasevych, A. Chernodub, and O. Skurzhanskyi, “GECToR – Grammatical error correction: Tag, not rewrite,” in *Proc. 15th Workshop on Innovative Use of NLP for Building Educational Applications*, Seattle, WA, USA, 2020, pp. 163–170.",
    "lasertagger": "E. Malmi, S. Krause, S. Rothe, D. Mirylenka, and A. Severyn, “Encode, tag, realize: High-precision text editing,” in *Proc. 2019 Conf. Empirical Methods in Natural Language Processing and 9th Int. Joint Conf. Natural Language Processing (EMNLP-IJCNLP)*, Hong Kong, China, 2019, pp. 5054–5065.",
    "proofread": "R. Liu, Y. Zhang, Y. Zhu, H. Sun, Y. Zhang, M. X. Huang, S. Cai, L. Meng, and S. Zhai, “Proofread: Fixes all errors with one tap,” arXiv:2406.04523, 2024.",
    "errant": "C. Bryant, M. Felice, and T. Briscoe, “Automatic annotation and evaluation of error types for grammatical error correction,” in *Proc. 55th Annu. Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, Vancouver, Canada, 2017, pp. 793–805.",
    "levenshtein": "V. I. Levenshtein, “Binary codes capable of correcting deletions, insertions, and reversals,” *Soviet Physics Doklady*, vol. 10, no. 8, pp. 707–710, 1966.",
    "bleu": "K. Papineni, S. Roukos, T. Ward, and W.-J. Zhu, “BLEU: A method for automatic evaluation of machine translation,” in *Proc. 40th Annu. Meeting of the Association for Computational Linguistics*, Philadelphia, PA, USA, 2002, pp. 311–318.",
    "ibleu": "H. Sun and M. Zhou, “Joint learning of a dual SMT system for paraphrase generation,” in *Proc. 50th Annu. Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)*, Jeju Island, Korea, 2012, pp. 38–42.",
    "sbert": "N. Reimers and I. Gurevych, “Sentence-BERT: Sentence embeddings using Siamese BERT-networks,” in *Proc. 2019 Conf. Empirical Methods in Natural Language Processing and 9th Int. Joint Conf. Natural Language Processing (EMNLP-IJCNLP)*, Hong Kong, China, 2019, pp. 3982–3992.",
    "multilingual": "N. Reimers and I. Gurevych, “Making monolingual sentence embeddings multilingual using knowledge distillation,” in *Proc. 2020 Conf. Empirical Methods in Natural Language Processing (EMNLP)*, 2020, pp. 4512–4525.",
    "deberta": "P. He, J. Gao, and W. Chen, “DeBERTaV3: Improving DeBERTa using ELECTRA-style pre-training with gradient-disentangled embedding sharing,” in *Proc. 11th Int. Conf. Learning Representations (ICLR)*, Kigali, Rwanda, 2023.",
    "xnli": "A. Conneau, R. Rinott, G. Lample, A. Williams, S. Bowman, H. Schwenk, and V. Stoyanov, “XNLI: Evaluating cross-lingual sentence representations,” in *Proc. 2018 Conf. Empirical Methods in Natural Language Processing*, Brussels, Belgium, 2018, pp. 2475–2485.",
    "mmr": "J. Carbonell and J. Goldstein, “The use of MMR, diversity-based reranking for reordering documents and producing summaries,” in *Proc. 21st Annu. Int. ACM SIGIR Conf. Research and Development in Information Retrieval*, Melbourne, Australia, 1998, pp. 335–336.",
    "nucleus": "A. Holtzman, J. Buys, L. Du, M. Forbes, and Y. Choi, “The curious case of neural text degeneration,” in *Proc. 8th Int. Conf. Learning Representations (ICLR)*, 2020.",
    "sentencepiece": "T. Kudo and J. Richardson, “SentencePiece: A simple and language independent subword tokenizer and detokenizer for neural text processing,” in *Proc. 2018 Conf. Empirical Methods in Natural Language Processing: System Demonstrations*, Brussels, Belgium, 2018, pp. 66–71.",
    "adafactor": "N. Shazeer and M. Stern, “Adafactor: Adaptive learning rates with sublinear memory cost,” in *Proc. 35th Int. Conf. Machine Learning (ICML)*, Stockholm, Sweden, 2018, pp. 4596–4604.",
    "checkpoint": "T. Chen, B. Xu, C. Zhang, and C. Guestrin, “Training deep nets with sublinear memory cost,” arXiv:1604.06174, 2016.",
    "transformers": "T. Wolf *et al.*, “Transformers: State-of-the-art natural language processing,” in *Proc. 2020 Conf. Empirical Methods in Natural Language Processing: System Demonstrations*, 2020, pp. 38–45.",
    "pytorch": "A. Paszke *et al.*, “PyTorch: An imperative style, high-performance deep learning library,” in *Advances in Neural Information Processing Systems 32 (NeurIPS 2019)*, Vancouver, Canada, 2019, pp. 8024–8035.",
    "streamlit": "Streamlit Inc., “Streamlit documentation.” [Online]. Available: https://docs.streamlit.io (truy cập: 26/10/2026).",
    "websockets": "A. Augustin, “websockets: Library for building WebSocket servers and clients in Python.” [Online]. Available: https://websockets.readthedocs.io (truy cập: 09/11/2026).",
}

# ============================================================== bộ đánh số bảng/hình/công thức theo chương
_parts: list[str] = []
_chapter = 0
_count = {"T": 0, "F": 0, "E": 0}
_labels: dict[str, str] = {}


def H1(text):
    global _chapter
    _chapter += 1
    _count.update(T=0, F=0, E=0)
    _parts.append(heading(1, text))


_last_h2 = False   # phần vừa thêm có phải tiêu đề mục 1.1 không


def H2(text):
    global _last_h2
    _parts.append(heading(2, text))
    _last_h2 = text


def H3(text):
    global _last_h2
    if _last_h2:   # người dùng muốn mỗi mục 1.1 có đoạn giới thiệu trước khi xuống 1.1.1
        raise SystemExit(f"Mục '{_last_h2}' cần một đoạn giới thiệu trước mục con '{text}'")
    _parts.append(heading(3, text))


def P(text, **kw):
    global _last_h2
    _parts.append(para(text, **kw))
    _last_h2 = False


def B(items):
    global _last_h2
    _parts.append(bullets(items))
    _last_h2 = False


def _label(kind, key):
    _count[kind] += 1
    num = f"{_chapter}.{_count[kind]}"
    if key:
        _labels[f"{kind}:{key}"] = num
    return num


def T(key, title, header, rows, widths, align=None):
    global _last_h2
    _last_h2 = False
    num = _label("T", key)
    _parts.append(caption("bang", f"Bảng {num}. {title}"))
    _parts.append(table(header, rows, widths, align))


def F(key, path, title, width_cm=15.0):
    global _last_h2
    _last_h2 = False
    num = _label("F", key)
    _parts.append(figure(path, width_cm))
    _parts.append(caption("hinh", f"Hình {num}. {title}"))


def E(key, omml):
    global _last_h2
    _last_h2 = False
    num = _label("E", key)
    _parts.append(equation(omml, num))


def _flush() -> str:
    xml = "".join(_parts)
    _parts.clear()

    def repl(m):
        key = m.group(1)
        if key not in _labels:
            raise SystemExit(f"Chưa có nhãn {key}")
        return _labels[key]

    return re.sub(r"«([TFE]:[\w-]+)»", repl, xml)


# ============================================================== phần đầu
def front_matter(rubric_xml: str) -> str:
    teacher, title = INFO["teacher"], INFO["title"]
    # khối ký tên: ở nửa phải trang, các dòng căn giữa theo dòng ngày tháng; tên tự ký tay khi in
    sign = sign_block([("Tp. Hồ Chí Minh, ngày …… tháng …… năm 2026", {"i": True, "before": 240, "after": 0}),
                       ("Sinh viên", {"b": True, "after": 0}),
                       ("(Ký và ghi rõ họ tên)", {"i": True, "after": 0})], left=3400)

    out = [heading(1, "LỜI CAM ĐOAN", numbered=False, page_break_before=False)]
    for text in [
        f"Em xin cam đoan đồ án “{title}” là công trình do cá nhân em thực hiện trong khuôn khổ môn Xử lý ngôn ngữ tự "
        f"nhiên, dưới sự hướng dẫn của {teacher}. Nội dung báo cáo phản ánh đúng quá trình em tìm hiểu, phân tích, thiết "
        "kế, xây dựng và đánh giá hệ thống.",
        "Các số liệu, bảng biểu và kết quả thực nghiệm trong báo cáo được em đo trực tiếp từ mã nguồn của đồ án, trên các "
        "bộ dữ liệu đã nêu rõ nguồn gốc. Em không chỉnh sửa hay chọn lọc kết quả theo ý muốn; những thử nghiệm không đạt "
        "kỳ vọng cũng được giữ lại và trình bày trung thực trong báo cáo.",
        "Các bộ dữ liệu, mô hình huấn luyện sẵn, thư viện và tài liệu của những tác giả khác được sử dụng trong đồ án đều "
        "được ghi rõ nguồn và trích dẫn theo quy định, đồng thời tuân thủ giấy phép sử dụng của từng nguồn. Đồ án không sao "
        "chép trái phép công trình của người khác.",
        "Trong quá trình thực hiện, em có sử dụng công cụ AI và các công cụ tự động hóa để hỗ trợ lập trình, chạy thử "
        "nghiệm và soạn thảo tài liệu. Mọi quyết định về phương pháp, dữ liệu, cách đánh giá và việc chấm đánh giá thủ công "
        "đều do em thực hiện, kiểm tra lại và chịu trách nhiệm.",
        "Mã nguồn, cấu hình và các kết quả trung gian của đồ án được lưu trữ đầy đủ trên kho mã của dự án, có thể tái lập "
        "lại các thí nghiệm theo hướng dẫn ở phần phụ lục. Những nhận định và đánh giá trong báo cáo là quan điểm của cá "
        "nhân em, dựa trên kết quả thực nghiệm đã trình bày.",
        "Báo cáo này chưa từng được nộp cho bất kỳ môn học hay chương trình đào tạo nào khác. Nếu có bất kỳ sai phạm nào, "
        "em xin hoàn toàn chịu trách nhiệm trước nhà trường và giảng viên hướng dẫn."]:
        out.append(para(text, after=160))
    out.append(sign)

    out.append(heading(1, "LỜI CẢM ƠN", numbered=False))
    for text in [
        f"Lời đầu tiên, em xin gửi lời cảm ơn chân thành đến {teacher}, người đã trực tiếp giảng dạy môn Xử lý ngôn ngữ tự "
        "nhiên và hướng dẫn em trong suốt quá trình thực hiện đồ án. Những góp ý của thầy về cách đặt vấn đề, cách đánh "
        "giá kết quả và cách trình bày đã giúp em định hướng đúng và hoàn thiện đồ án.",
        "Em xin cảm ơn quý thầy cô Khoa Kỹ thuật & Khoa học Máy tính, Trường Đại học Tư thục Quốc tế Sài Gòn đã truyền đạt "
        "cho em những kiến thức nền tảng về lập trình, cấu trúc dữ liệu, học máy và xử lý ngôn ngữ tự nhiên. Đây là hành "
        "trang quan trọng để em có thể tự tìm hiểu và giải quyết một bài toán thực tế.",
        "Em cũng xin gửi lời cảm ơn đến các nhóm tác giả đã công bố công khai các bộ dữ liệu VSEC, ViLexNorm, ViSP, VEC, từ "
        "điển từ viết tắt tiếng Việt và mô hình ngôn ngữ ViT5. Nhờ những tài nguyên mở này, em có thể thực hiện đồ án "
        "trong phạm vi một học kỳ với điều kiện phần cứng của một máy tính cá nhân.",
        "Trong quá trình thực hiện, em đã học được nhiều điều, không chỉ về kiến thức chuyên môn như cách tinh chỉnh mô hình "
        "Transformer, cách xây dựng tập dữ liệu không rò rỉ hay cách đánh giá một hệ thống xử lý ngôn ngữ, mà còn về tinh "
        "thần làm việc nghiêm túc, trung thực với kết quả và kiên nhẫn khi gặp lỗi. Đây là những bài học quý giá cho quá "
        "trình học tập và làm việc sau này của em.",
        "Cuối cùng, em xin cảm ơn gia đình và bạn bè đã luôn động viên, hỗ trợ em trong quá trình học tập và thực hiện đồ án.",
        "Do thời gian và kinh nghiệm còn hạn chế, báo cáo khó tránh khỏi những thiếu sót. Em rất mong nhận được ý kiến đóng "
        "góp của quý thầy cô để em hoàn thiện hơn trong những đồ án tiếp theo. Em xin chân thành cảm ơn!"]:
        out.append(para(text, after=160))
    out.append(sign)

    out.append(page_break())
    out.append(rubric_xml)

    out.append(heading(1, "MỤC LỤC", numbered=False))
    out.append(field('TOC \\o "1-3" \\h \\z \\u', "Mở bằng Word và cập nhật trường (Ctrl+A, F9) để hiện mục lục."))

    out.append(heading(1, "DANH MỤC KÝ HIỆU, TỪ VIẾT TẮT", numbered=False))
    abbr = [
        ("BLEU", "Bilingual Evaluation Understudy: chỉ số so khớp n-gram"), ("CER", "Character Error Rate: tỉ lệ lỗi ký tự"),
        ("CUDA", "Compute Unified Device Architecture: nền tảng tính toán trên GPU NVIDIA"),
        ("EM", "Exact Match: tỉ lệ câu khớp hoàn toàn với câu chuẩn"), ("F0.5", "Trung bình điều hòa có trọng số, ưu tiên độ chính xác"),
        ("GĐ1, GĐ2", "Giai đoạn huấn luyện 1, giai đoạn huấn luyện 2"), ("GPU", "Graphics Processing Unit: bộ xử lý đồ họa"),
        ("iBLEU", "BLEU có phạt việc chép lại câu gốc"), ("JSONL", "JSON Lines: mỗi dòng một bản ghi JSON"),
        ("LLM", "Large Language Model: mô hình ngôn ngữ lớn"), ("MMR", "Maximal Marginal Relevance: xếp hạng có tính đa dạng"),
        ("MXH", "Mạng xã hội"), ("N-best", "N phương án tốt nhất của beam search"),
        ("NLI", "Natural Language Inference: suy diễn ngôn ngữ tự nhiên"), ("NLP", "Natural Language Processing: xử lý ngôn ngữ tự nhiên"),
        ("NSW", "Non-Standard Word: từ không chuẩn (viết tắt, teencode)"), ("RQ", "Research Question: câu hỏi nghiên cứu"),
        ("seq2seq", "Sequence-to-sequence: mô hình chuỗi sang chuỗi"), ("T5, ViT5", "Text-to-Text Transfer Transformer; bản tiếng Việt"),
        ("VRAM", "Bộ nhớ của GPU"), ("WER", "Word Error Rate: tỉ lệ lỗi từ"),
    ]
    out.append(table(["STT", "Ký hiệu chữ viết tắt", "Chữ viết đầy đủ"], [[str(i), a, b] for i, (a, b) in enumerate(abbr, 1)],
                     [0.6, 1.6, 5], ["center", "left", "left"]))

    out.append(heading(1, "DANH MỤC CÁC BẢNG", numbered=False))
    out.append(field('TOC \\h \\z \\t "Chu thich bang,1"', "Mở bằng Word và cập nhật trường để hiện danh mục bảng."))
    out.append(heading(1, "DANH MỤC HÌNH ẢNH, BIỂU ĐỒ, SƠ ĐỒ", numbered=False))
    out.append(field('TOC \\h \\z \\t "Chu thich hinh,1"', "Mở bằng Word và cập nhật trường để hiện danh mục hình."))
    return "".join(out)


# ============================================================== nội dung chính
def main_matter() -> str:
    chapter1()
    chapter2()
    chapter3()
    chapter4()
    chapter5()
    return _flush()


def chapter1():
    H1("TỔNG QUAN VỀ CHỦ ĐỀ NGHIÊN CỨU")
    P("Tin nhắn là hình thức giao tiếp bằng chữ phổ biến nhất hiện nay. Khi nhắn tin tiếng Việt, người dùng thường gõ nhanh "
      "trên điện thoại, bỏ dấu, viết tắt (*ko*, *dc*, *mn*), gõ Telex chưa chuyển (*nguowif*), bấm nhầm phím hoặc dùng "
      "teencode. Văn bản như vậy khó đọc, dễ gây hiểu lầm và không phù hợp khi cần gửi cho thầy cô, đồng nghiệp hay khách "
      "hàng. Đồ án xây dựng **hệ thống sửa lỗi tin nhắn tiếng Việt**: sửa lỗi chính tả, gợi ý từ đúng ngay trong lúc gõ và "
      "đề xuất cách diễn đạt khác cho câu đã sửa, với yêu cầu xuyên suốt là **không làm thay đổi ý của người viết**.")

    H2("Lý do chọn đồ án")
    P("Tiếng Việt dùng chữ Latinh có dấu: mỗi âm tiết mang một trong sáu thanh và nhiều nguyên âm có dấu phụ (ă, â, ê, ô, ơ, "
      "ư) cùng chữ đ. Chỉ cần bỏ dấu, một chuỗi như *con yeu qua* có thể là “con yêu quá”, “còn yêu quá” hay “con yếu quá”. "
      "Bàn phím điện thoại có sửa lỗi tự động nhưng chủ yếu dựa vào từ điển từng từ, nên khó xử lý câu bỏ dấu hoàn toàn và "
      "các từ viết tắt phụ thuộc ngữ cảnh. Ngược lại, các mô hình sinh văn bản lớn có thể viết lại cả câu nhưng dễ thêm, bớt "
      "hoặc đổi ý, điều không chấp nhận được với tin nhắn của chính người dùng.")
    P("Về mặt dữ liệu, các bộ dữ liệu sửa lỗi tiếng Việt công khai phần lớn là văn bản trang trọng (bài báo, luận văn), còn "
      "dữ liệu kiểu mạng xã hội mới xuất hiện gần đây [@vilexnorm]. Vì vậy, việc tìm hiểu cách đưa mô hình Transformer tiếng "
      "Việt vào bài toán sửa lỗi tin nhắn, đo đúng chất lượng trên dữ liệu đúng miền và xây dựng một ứng dụng chạy được trên "
      "máy cá nhân là có ý nghĩa thực tiễn, đồng thời phù hợp với yêu cầu của môn học về một bài toán xử lý ngôn ngữ tự nhiên "
      "cho tiếng Việt.")

    H2("Các nghiên cứu trước đây")
    P("**Sửa lỗi chính tả theo mô hình kênh nhiễu.** Hướng tiếp cận kinh điển coi văn bản lỗi là kết quả của từ đúng đi qua "
      "một “kênh” gây nhiễu, rồi chọn từ đúng có xác suất hậu nghiệm cao nhất [@kernighan; @brill]. Các thư viện như SymSpell "
      "[@symspell] tăng tốc bước tìm ứng viên bằng chỉ mục xóa ký tự. Ưu điểm của hướng này là nhanh và dễ giải thích, nhưng "
      "chỉ nhìn ngữ cảnh rất hẹp.")
    P("**Mô hình học sâu cho sửa lỗi.** Soft-Masked BERT [@softmasked] kết hợp mạng phát hiện lỗi với BERT để sửa lỗi chính "
      "tả; GECToR [@gector] và LaserTagger [@lasertagger] coi sửa lỗi là gán nhãn phép biến đổi cho từng từ thay vì sinh lại "
      "cả câu, giúp hạn chế việc mô hình tự viết lại. Với tiếng Việt, Tran và cộng sự dùng Transformer phân cấp mức ký tự và "
      "mức từ [@hierarchical]; VSEC [@vsec] dùng mô hình seq2seq Transformer với BPE và công bố bộ 9.341 câu có lỗi do người "
      "viết. Bộ ViLexNorm [@vilexnorm] là kho chuẩn hóa từ vựng đầu tiên cho bình luận mạng xã hội tiếng Việt (hơn 10.000 "
      "cặp câu do người gán nhãn); ViSoLex [@visolex] xây dựng công cụ tra cứu và chuẩn hóa từ không chuẩn.")
    P("**Mô hình sinh tiếng Việt và diễn đạt lại.** T5 [@t5] đưa mọi bài toán về dạng văn bản sang văn bản dựa trên kiến "
      "trúc Transformer [@vaswani]. ViT5 [@vit5] và BARTpho [@bartpho] là các mô hình mã hóa–giải mã được huấn luyện trước "
      "trên tiếng Việt. Với diễn đạt lại, ViSP [@visp] là bộ dữ liệu lớn gồm khoảng 1,2 triệu cặp câu đồng nghĩa từ nhiều "
      "lĩnh vực.")
    P("**Ứng dụng trong bàn phím.** Tính năng Proofread của Gboard [@proofread] dùng mô hình ngôn ngữ lớn chạy trên máy chủ để "
      "sửa cả câu bằng một lần chạm, cho thấy nhu cầu sửa lỗi ở mức câu thay vì từng từ. Tuy nhiên, các nghiên cứu trên chưa "
      "giải quyết trực tiếp ba vấn đề của đồ án: (1) đánh giá trên tin nhắn thật thay vì văn bản trang trọng, (2) gợi ý ngay "
      "khi gõ cho tiếng Việt mà vẫn để người dùng quyết định, và (3) kiểm soát việc đổi nghĩa khi diễn đạt lại.")

    H2("Mục đích nghiên cứu")
    P("Mục đích của đồ án là xây dựng và đánh giá một hệ thống chạy trên máy cá nhân, gồm ba chức năng: sửa lỗi chính tả cho "
      "tin nhắn tiếng Việt, gợi ý câu đúng ngay khi gõ, và đề xuất cách diễn đạt khác giữ nguyên ý. Đồ án trả lời ba câu hỏi "
      "nghiên cứu:")
    B(["**RQ1:** Mô hình Transformer tiếng Việt được tinh chỉnh cải thiện chất lượng sửa lỗi so với mốc đơn giản (chép nguyên "
       "đầu vào) và so với mô hình có sẵn đến mức nào, trên cả văn bản trang trọng lẫn tin nhắn?",
       "**RQ2:** Mô hình diễn đạt lại có tạo được câu tự nhiên mà vẫn giữ ý câu gốc không, và các chỉ số tự động có đo đúng "
       "điều đó không?",
       "**RQ3:** Quy trình hai bước (sửa lỗi rồi mới diễn đạt lại) có tốt hơn việc diễn đạt lại thẳng câu còn lỗi không?"])

    H2("Đối tượng nghiên cứu")
    P("Đối tượng nghiên cứu là các câu và tin nhắn tiếng Việt ngắn, ngữ cảnh nằm trong một tin nhắn, có các loại lỗi thường "
      "gặp khi gõ: thiếu hoặc sai dấu, bỏ dấu cả câu, viết tắt và teencode, gõ Telex chưa chuyển, bấm hụt, bấm nhầm phím bên "
      "cạnh, gõ đúp phím. Phạm vi gồm hai mô hình ViT5 được tinh chỉnh (sửa lỗi, diễn đạt lại), một từ điển trích tự động từ "
      "dữ liệu huấn luyện và một ứng dụng web chạy cục bộ.")
    P("**Ngoài phạm vi:** không huấn luyện mô hình ngôn ngữ từ đầu; không xử lý hội thoại nhiều lượt hay ngữ cảnh ngoài tin "
      "nhắn hiện tại; không cam kết sửa mọi lỗi ngữ pháp và tiếng lóng; không xây dựng bàn phím điện thoại thật.")

    H2("Nhiệm vụ nghiên cứu")
    B(["Khảo sát, làm sạch và chia tập bốn bộ dữ liệu (VSEC, ViLexNorm, VEC, ViSP), bảo đảm không rò rỉ dữ liệu giữa "
       "train/val/test.",
       "Xây dựng mốc so sánh và bộ chỉ số đánh giá phù hợp: CER, WER, tỉ lệ câu đúng hết, P/R/F0.5 trên phép sửa, tỉ lệ sửa "
       "quá tay, BLEU, iBLEU, độ tương đồng ngữ nghĩa.",
       "Tinh chỉnh ViT5 cho sửa lỗi (kèm dữ liệu lỗi nhân tạo và huấn luyện hai giai đoạn) và cho diễn đạt lại.",
       "Thiết kế bộ lọc và xếp hạng câu diễn đạt lại để không mất số, tên riêng, phủ định.",
       "Xây dựng từ điển và cơ chế gợi ý sau mỗi từ khi gõ; thử các cách kết hợp từ điển với mô hình.",
       "Xây dựng ứng dụng demo (chế độ tin nhắn và chế độ văn bản), kiểm thử tự động và đánh giá thủ công."])

    H2("Phương pháp nghiên cứu")
    P("Đồ án dùng phương pháp **thực nghiệm có đối chứng**. Mọi mô hình được so với mốc chép nguyên đầu vào và với mô hình có "
      "sẵn. Tham số chỉ được chọn trên tập validation; tập test chỉ dùng một lần để báo cáo. Với những thay đổi có thể làm tốt "
      "một phía nhưng tệ phía khác, **điều kiện giữ thay đổi được đặt trước khi chạy test** để tránh chọn kết quả theo ý muốn. "
      "Ngoài chỉ số tự động, đồ án dùng **stress test** sinh lỗi tự động theo từng kiểu, **giả lập người dùng gõ từng từ**, "
      "và **chấm thủ công** khi chỉ số tự động không đáng tin. Kết quả thử nghiệm không đạt (kết quả âm) cũng được ghi lại "
      "trung thực.")

    H2("Các kết quả dự kiến của đồ án")
    B(["Một mô hình sửa lỗi tiếng Việt chạy trên GPU 6 GB, có kết quả trên ba tập test và theo tám kiểu lỗi.",
       "Một mô hình diễn đạt lại kèm bộ lọc giữ nghĩa, có đánh giá tự động và thủ công.",
       "Ứng dụng web chạy cục bộ: gợi ý cả câu ngay khi gõ, sửa cả câu và diễn đạt lại khi gửi, có chế độ soạn văn bản.",
       "Báo cáo các phát hiện về dữ liệu và về cách đánh giá (rò rỉ dữ liệu, chỉ số tự động không đáng tin), cùng mã nguồn "
       "tái lập được trên GitHub."])

    H2("Kế hoạch tổ chức thực hiện đồ án")
    P("Đồ án được thực hiện trong khoảng năm tuần, theo các giai đoạn ở Bảng «T:ke-hoach». Mỗi giai đoạn kết thúc bằng một lần gộp "
      "mã vào nhánh chính và cập nhật kết quả vào tài liệu theo dõi của dự án.")
    T("ke-hoach", "Kế hoạch và tiến độ thực hiện",
      ["Giai đoạn", "Thời gian", "Công việc chính", "Kết quả"],
      [["1. Khảo sát", "19/10/2026", "Đọc tài liệu, kiểm tra giấy phép và cấu trúc dữ liệu", "Phạm vi, danh sách dataset"],
       ["2. Dữ liệu và mốc", "19–23/10", "Tải, làm sạch, chia tập, chống rò rỉ; mốc chép đầu vào", "Tập train/val/test"],
       ["3. Huấn luyện", "23–26/10", "Tinh chỉnh ViT5 sửa lỗi (v1, v2, GĐ2) và diễn đạt lại; lỗi nhân tạo", "Mô hình, nhật ký"],
       ["4. Tích hợp và demo", "25–26/10", "Bộ lọc, xếp hạng, demo Streamlit, chọn 1 trong 3 phương án", "Hệ thống chạy được"],
       ["5. Đánh giá", "26–27/10", "Stress test, RQ3, 20 lỗi tiêu biểu, chấm thủ công", "Bảng kết quả"],
       ["6. Gợi ý khi gõ", "09/11", "Từ điển, kết hợp từ điển và mô hình, giả lập gõ", "Bản thử, kết quả so sánh"],
       ["7. Giao diện và báo cáo", "22–24/11", "Khung tin nhắn, chế độ văn bản, báo cáo và slide", "Demo chính, báo cáo"]],
      [1.6, 1.2, 4, 2])

    H2("Bố cục báo cáo")
    P("Ngoài phần mở đầu, tài liệu tham khảo và phụ lục, báo cáo gồm năm chương. **Chương 1** giới thiệu bài toán, mục tiêu "
      "và phạm vi. **Chương 2** trình bày cơ sở lý thuyết (kênh nhiễu, Transformer, T5/ViT5, giải mã, biểu diễn câu) và công "
      "nghệ sử dụng. **Chương 3** phân tích yêu cầu và thiết kế hệ thống, dữ liệu, giao diện. **Chương 4** mô tả quá trình xây "
      "dựng, kiểm thử và đánh giá kết quả. **Chương 5** tổng kết, đánh giá tác động và đề xuất hướng phát triển.")


def chapter2():
    H1("CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ SỬ DỤNG")
    P("Chương này tổng hợp các kiến thức nền mà hệ thống sử dụng: bài toán sửa lỗi và diễn đạt lại, mô hình kênh nhiễu, kiến "
      "trúc Transformer và mô hình ViT5, các thuật toán giải mã, cách đo độ giống nghĩa giữa hai câu, cùng các công nghệ dùng "
      "để hiện thực.")

    H2("Cơ sở lý thuyết về bài toán")
    P("Mục này trình bày ba nội dung nền tảng của đề tài: bản chất của bài toán sửa lỗi chính tả và chuẩn hóa văn bản; "
      "những đặc điểm riêng của chữ viết tiếng Việt và văn bản tin nhắn khiến bài toán trở nên khó; và bài toán diễn đạt "
      "lại câu cùng những khó khăn khi đánh giá kết quả.")
    H3("Bài toán sửa lỗi chính tả và chuẩn hóa văn bản")
    P("Cho câu đầu vào *x* có thể chứa lỗi, bài toán sửa lỗi tìm câu *y* đúng chính tả mà người viết muốn gõ. Khi lỗi chỉ là "
      "sai chính tả, đây là bài toán sửa lỗi chính tả; khi đầu vào là văn bản mạng xã hội với viết tắt và teencode, bài toán "
      "gần với chuẩn hóa từ vựng (lexical normalization) [@vilexnorm]. Đồ án xử lý cả hai trong cùng một mô hình chuỗi sang "
      "chuỗi. Lỗi được chia thành: lỗi gõ phím (đảo, thiếu, thừa, nhầm ký tự), lỗi dấu (thiếu hoặc sai dấu thanh, dấu chữ), "
      "từ không chuẩn (viết tắt, teencode) và lỗi thành từ có thật (*gặt bỏ* thay vì *gạt bỏ*), loại khó nhất vì từ điển "
      "không phát hiện được.")
    H3("Đặc điểm chữ viết tiếng Việt và văn bản tin nhắn")
    P("Mỗi âm tiết tiếng Việt gồm phụ âm đầu, vần và một trong sáu thanh. Người dùng thường gõ bằng kiểu Telex (thêm chữ cái "
      "sau nguyên âm: *aa* → â, *ow* → ơ, chữ *s f r x j* cho thanh) hoặc VNI (dùng chữ số). Gõ nhanh trên điện thoại sinh ra "
      "các dạng đặc trưng ở Bảng «T:vi-du-loi». Các dạng này có thể chồng lên nhau trong cùng một câu, và nhiều từ viết tắt một chữ "
      "cái (*m*, *c*, *t*) ứng với nhiều đại từ khác nhau, chỉ ngữ cảnh hội thoại mới phân biệt được.")
    T("vi-du-loi", "Một số kiểu lỗi thường gặp trong tin nhắn tiếng Việt",
      ["Kiểu lỗi", "Ví dụ gõ", "Câu đúng"],
      [["Bỏ dấu cả câu", "mai di hoc ko", "mai đi học không"],
       ["Telex chưa chuyển", "nguowif", "người"],
       ["Viết tắt, teencode", "kcj, dc, ny", "không có gì, được, người yêu"],
       ["Đảo chữ, bấm hụt", "cnog, ngươ", "công, người"],
       ["Phím bên cạnh, phím đúp", "nhaf, ddiii", "nhà, đi"],
       ["Mơ hồ khi bỏ dấu", "con yeu qua", "con yêu quá / còn yêu quá / con yếu quá"]],
      [2.2, 2, 3.2])
    H3("Bài toán diễn đạt lại")
    P("Diễn đạt lại (paraphrasing) là sinh câu *c* khác cách nói của câu nguồn *x* nhưng mang cùng nghĩa. Hai yêu cầu này "
      "mâu thuẫn: câu càng giống câu gốc thì càng dễ giữ nghĩa nhưng càng vô ích. Vì vậy một câu diễn đạt tốt phải vừa giữ "
      "nghĩa, vừa đủ khác, vừa tự nhiên. Việc đánh giá tự động rất khó: chỉ số so khớp từ như BLEU [@bleu] thưởng cho việc "
      "chép lại câu gốc, nên cần thêm chỉ số phạt chép lại như iBLEU [@ibleu] và đánh giá thủ công.")

    H2("Các phương pháp và mô hình liên quan")
    P("Mục này giới thiệu các phương pháp và mô hình được dùng trong hệ thống, đi từ cách tiếp cận cổ điển dựa trên từ "
      "điển và mô hình kênh nhiễu đến kiến trúc Transformer, mô hình ViT5, các thuật toán giải mã và cách đo độ giống nghĩa "
      "giữa hai câu. Cuối mục là phần so sánh các hướng tiếp cận và lý do lựa chọn của đồ án.")
    H3("Mô hình kênh nhiễu và từ điển")
    P("Theo mô hình kênh nhiễu [@kernighan; @brill], với từ gõ *t*, từ đúng được chọn là ứng viên *c* trong tập ứng viên "
      "*C(t)* có tích xác suất kênh P(t|c) (khả năng gõ ra *t* khi muốn gõ *c*) và xác suất ngôn ngữ P(c) lớn nhất:")
    E("kenh-nhieu", hat(mr("c")) + mr("=") + lim_low("argmax", mr("c∈C(t)")) + mr("P(t|c)·P(c)"))
    P("Đồ án ước lượng xác suất ngôn ngữ bằng mô hình bigram có làm trơn nội suy, trong đó C(·) là số lần xuất hiện trong dữ "
      "liệu huấn luyện và N là tổng số từ:")
    E("bigram", sub(mr("P"), mt("bigram")) + paren(sub(mr("w"), mr("i")) + mr("|") + sub(mr("w"), mr("i−1")))
      + mr("=0,9·") + frac(mr("C(") + sub(mr("w"), mr("i−1")) + mr(",") + sub(mr("w"), mr("i")) + mr(")"),
                           mr("C(") + sub(mr("w"), mr("i−1")) + mr(")"))
      + mr("+0,1·") + frac(mr("C(") + sub(mr("w"), mr("i")) + mr(")+0,01"), mr("N+1")))
    P("Để tìm nhanh các từ gần giống (cách một lỗi đảo, thiếu, thừa hoặc thay ký tự), đồ án dùng ý tưởng chỉ mục xóa đối "
      "xứng của SymSpell [@symspell]: lưu sẵn mọi dạng bị xóa một ký tự của các từ trong từ điển, khi tra chỉ cần so khớp "
      "chuỗi. Khoảng cách giữa hai chuỗi được hiểu theo khoảng cách chỉnh sửa Levenshtein [@levenshtein].")
    H3("Kiến trúc Transformer")
    P("Transformer [@vaswani] thay mạng hồi quy bằng cơ chế tự chú ý (self-attention): mỗi vị trí trong câu tổng hợp thông "
      "tin từ mọi vị trí khác với trọng số học được. Với ma trận truy vấn Q, khóa K, giá trị V và số chiều khóa d_{k}:")
    E("attention", mt("Attention") + paren(mr("Q,K,V")) + mr("=") + mt("softmax")
      + paren(frac(mr("Q") + sup(mr("K"), mr("T")), sqrt(sub(mr("d"), mr("k"))))) + mr("V"))
    P("Mô hình mã hóa–giải mã gồm một khối mã hóa đọc câu nguồn và một khối giải mã sinh câu đích từng token, mỗi bước chú "
      "ý vào biểu diễn của câu nguồn. Nhờ tính song song khi huấn luyện, Transformer là nền tảng của hầu hết mô hình ngôn ngữ "
      "hiện nay.")
    H3("Mô hình T5 và ViT5")
    P("T5 [@t5] đưa mọi bài toán ngôn ngữ về dạng “văn bản vào, văn bản ra” trên kiến trúc mã hóa–giải mã, huấn luyện trước "
      "bằng cách che các đoạn văn bản rồi khôi phục. ViT5 [@vit5] áp dụng cách làm của T5 trên kho văn bản tiếng Việt lớn, "
      "dùng bộ tách từ con SentencePiece [@sentencepiece]. Bản *ViT5-base* có khoảng 226 triệu tham số. Mô hình sinh câu "
      "đích *y* = (y_{1}, …, y_{T}) từ câu nguồn *x* theo xác suất:")
    E("seq-prob", sub(mr("P"), mr("θ")) + paren(mr("y|x")) + mr("=") + nary("∏", mr("t=1"), mr("T"),
      sub(mr("P"), mr("θ")) + paren(sub(mr("y"), mr("t")) + mr("|") + sub(mr("y"), mr("<t")) + mr(",x"))))
    P("Khi tinh chỉnh trên các cặp (câu lỗi, câu đúng), tham số θ được cập nhật để cực tiểu hàm mất mát entropy chéo:")
    E("loss", mr("L") + paren(mr("θ")) + mr("=−") + nary("∑", mr("t=1"), mr("T"), mt("log ") + sub(mr("P"), mr("θ"))
      + paren(sub(mr("y"), mr("t")) + mr("|") + sub(mr("y"), mr("<t")) + mr(",x"))))
    H3("Giải mã: beam search, N-best và lấy mẫu nucleus")
    P("Khi suy luận, beam search giữ *k* câu dở dang có xác suất cao nhất ở mỗi bước, cuối cùng trả về danh sách N-best. "
      "Đồ án dùng N-best để đưa cho người dùng tối đa ba phương án sửa khi mô hình không chắc. Điểm của phương án *k* là "
      "log-xác suất cả câu s_{k}; xác suất hiển thị được chuẩn hóa bằng softmax:")
    E("softmax", sub(mr("p"), mr("k")) + mr("=") + frac(mt("exp") + paren(sub(mr("s"), mr("k"))),
                                                          nary("∑", mr("j"), "", mt("exp") + paren(sub(mr("s"), mr("j"))))))
    P("Với diễn đạt lại, beam search thường cho các câu rất giống nhau. Lấy mẫu nucleus [@nucleus] chỉ lấy ngẫu nhiên trong "
      "tập token nhỏ nhất có tổng xác suất vượt ngưỡng *p*, giúp ứng viên đa dạng hơn. Đồ án kết hợp cả hai: một nửa ứng "
      "viên từ beam search, một nửa từ lấy mẫu nucleus.")
    H3("Biểu diễn câu, suy diễn ngôn ngữ và xếp hạng đa dạng")
    P("Để kiểm tra câu diễn đạt có giữ nghĩa không, mỗi câu được biểu diễn bằng một vectơ nhúng câu theo cách của "
      "Sentence-BERT [@sbert], dùng mô hình đa ngôn ngữ *paraphrase-multilingual-MiniLM-L12-v2* [@multilingual]. Độ giống "
      "nghĩa là cosine giữa hai vectơ u và v:")
    E("cosine", mt("cos") + paren(mr("u,v")) + mr("=") + frac(mr("u·v"), mr("‖u‖ ‖v‖")))
    P("Độ tương đồng cosine không phân biệt tốt phủ định hay đảo vai, nên đồ án bổ sung mô hình suy diễn ngôn ngữ tự nhiên "
      "(NLI) mDeBERTa-v3 [@deberta] huấn luyện trên dữ liệu đa ngôn ngữ như XNLI [@xnli]: mô hình cho biết câu A có suy ra "
      "câu B hay không. Cuối cùng, các gợi ý được chọn lần lượt theo Maximal Marginal Relevance (MMR) [@mmr], cân bằng giữa "
      "điểm chất lượng và độ khác với các gợi ý đã chọn (chi tiết ở công thức («E:mmr»), Chương 3).")
    H3("So sánh và lý do lựa chọn")
    T("so-sanh-pp", "So sánh các hướng tiếp cận cho bài toán sửa lỗi",
      ["Hướng tiếp cận", "Ưu điểm", "Hạn chế", "Dùng trong đồ án"],
      [["Từ điển + kênh nhiễu [@kernighan; @symspell]", "Nhanh (dưới 1 ms), dễ giải thích, không cần GPU",
        "Ngữ cảnh hẹp, kém với câu bỏ dấu và từ mơ hồ", "Tầng gợi ý tức thì khi gõ"],
       ["Gán nhãn phép sửa [@gector; @lasertagger]", "Ít tự viết lại, chính xác cao", "Cần bộ nhãn phép sửa, ít mô hình tiếng Việt",
        "Không dùng"],
       ["Seq2seq Transformer [@t5; @vit5]", "Dùng toàn bộ câu, xử lý được câu bỏ dấu và viết tắt",
        "Có thể sửa quá tay, cần GPU", "Mô hình chính (ViT5-base)"],
       ["Mô hình ngôn ngữ lớn [@proofread]", "Rất linh hoạt", "Nặng, cần máy chủ, dễ đổi ý người viết", "Không dùng"]],
      [2.3, 2.3, 2.5, 1.7])
    P("ViT5-base được chọn vì: (1) được huấn luyện trước trên tiếng Việt và có dạng văn bản sang văn bản, dùng được cho cả "
      "sửa lỗi lẫn diễn đạt lại; (2) với bf16, bộ tối ưu Adafactor [@adafactor] và gradient checkpointing [@checkpoint], "
      "mô hình huấn luyện vừa GPU 6 GB; (3) có thể so sánh trực tiếp với mô hình sửa lỗi có sẵn dựa trên BARTpho [@bartpho]. "
      "Từ điển được giữ lại làm tầng gợi ý tức thì vì tốc độ, còn mô hình đảm nhận việc chọn theo cả câu.")

    H2("Ngôn ngữ lập trình và công nghệ sử dụng")
    B(["**Ngôn ngữ lập trình:** Python 3.14.7 cho toàn bộ xử lý dữ liệu, huấn luyện, đánh giá và máy chủ; HTML, CSS và "
       "JavaScript thuần cho giao diện web.",
       "**Framework và thư viện:** PyTorch 2.14.1 với CUDA 12.6 [@pytorch]; Hugging Face Transformers 5.20.1, Tokenizers, "
       "Datasets, Accelerate [@transformers]; sentence-transformers 6.1.0 [@sbert]; pandas, NumPy, Matplotlib; Streamlit 1.66 "
       "[@streamlit] cho demo dự phòng; websockets 17.2 [@websockets] cho máy chủ gợi ý khi gõ; pytest 9.1 cho kiểm thử.",
       "**Hệ quản trị cơ sở dữ liệu:** không sử dụng. Dữ liệu lưu dạng tệp JSONL, CSV và JSON (mỗi dòng một cặp câu), phù "
       "hợp với khối lượng vài trăm nghìn câu và dễ tái lập.",
       "**API, dịch vụ và nền tảng tích hợp:** Hugging Face Hub để tải mô hình và dữ liệu (đường dẫn được ghim theo commit); "
       "sau khi tải, hệ thống chạy hoàn toàn ngoại tuyến trên máy cá nhân, không gọi dịch vụ bên ngoài."])

    H2("Môi trường phát triển")
    P("Đồ án được phát triển trên máy tính xách tay chạy Windows 11 (cấu hình ở Bảng «T:phan-cung», Chương 4). Mã nguồn được quản "
      "lý bằng Git 2.54 và lưu trên GitHub (kho *vietnamese-message-assistant*), làm việc theo nhánh tính năng rồi gộp vào "
      "nhánh chính. Phân tích dữ liệu và vẽ hình dùng Jupyter Notebook; mô hình chạy trong môi trường ảo Python (*venv*). "
      "Giao diện được kiểm thử trên trình duyệt ở cả khổ máy tính và khổ điện thoại. Công cụ AI và các công cụ tự động hóa được "
      "dùng để hỗ trợ lập trình, chạy thí nghiệm và soạn tài liệu.")

    H2("Tổng kết chương")
    P("Chương 2 đã trình bày nền tảng của hệ thống: mô hình kênh nhiễu và từ điển cho tầng gợi ý nhanh, kiến trúc "
      "Transformer và ViT5 cho mô hình sửa lỗi và diễn đạt lại, các thuật toán giải mã, cùng biểu diễn câu, NLI và MMR cho "
      "bước lọc và xếp hạng. Đây là cơ sở để phân tích, thiết kế và xây dựng hệ thống ở các chương sau.")


def chapter3():
    H1("THIẾT KẾ ỨNG DỤNG")
    H2("Phân tích bài toán")
    P("Người dùng mục tiêu là người nhắn tin bằng tiếng Việt (gõ nhanh, hay bỏ dấu và viết tắt) và người soạn văn bản cần "
      "kiểm tra chính tả. Đầu vào là chuỗi ký tự người dùng đang gõ; đầu ra gồm các phương án câu đã sửa và một câu diễn đạt "
      "khác. Hệ thống phải giải quyết ba vấn đề: (1) gợi ý đúng ngay trong lúc gõ mà không làm gián đoạn; (2) không tự ý đổi "
      "ý người viết, nhất là số, tên riêng và phủ định; (3) chạy được trên máy cá nhân có GPU 6 GB. Nguyên tắc thiết kế là "
      "**hệ thống đề xuất, người dùng quyết định**: chỉ tự đổi khi chắc chắn (Telex giải mã ra đúng một từ có thật), còn lại "
      "gạch chân và đưa danh sách lựa chọn.")

    H2("Xác định yêu cầu hệ thống")
    P("Từ phân tích ở mục 3.1, yêu cầu của hệ thống được chia thành ba nhóm: yêu cầu chức năng (hệ thống phải làm được "
      "gì), yêu cầu phi chức năng (tốc độ, tài nguyên, độ tin cậy, khả năng sử dụng) và yêu cầu về dữ liệu, bảo mật, hiệu "
      "năng. Mỗi yêu cầu đều có cách kiểm tra tương ứng ở Chương 4.")
    H3("Yêu cầu chức năng")
    T("yc-chuc-nang", "Yêu cầu chức năng",
      ["Mã", "Chức năng", "Mô tả"],
      [["F1", "Gợi ý khi gõ", "Sau mỗi từ gõ xong, gạch chân từ chưa chắc, đưa tối đa 3 câu hoàn chỉnh đã sửa"],
       ["F2", "Tự đổi Telex chắc chắn", "Đổi ngay *nguowif* → người khi chỉ có một cách giải mã hợp lệ"],
       ["F3", "Gợi ý theo câu", "Gõ . ! ? hoặc xuống dòng là sang câu mới; bấm vào câu cũ để sửa riêng câu đó"],
       ["F4", "Sửa cả câu khi gửi", "Mô hình ViT5 sửa cả tin nhắn, đưa tối đa 3 phương án"],
       ["F5", "Diễn đạt lại", "Đưa 1 câu diễn đạt giữ nghĩa; không đưa nếu không đủ an toàn"],
       ["F6", "Chế độ văn bản", "Soạn nhiều đoạn như Word, chỉ sửa chính tả, không gửi"],
       ["F7", "Ghi nhật ký", "Lưu các lựa chọn của người dùng để phân tích lỗi"]],
      [0.7, 2, 6], ["center", "left", "left"])
    H3("Yêu cầu phi chức năng")
    T("yc-phi-chuc-nang", "Yêu cầu phi chức năng",
      ["Nhóm", "Yêu cầu", "Cách kiểm tra"],
      [["Hiệu năng", "Tầng từ điển dưới 20 ms; tầng mô hình dưới 500 ms mỗi lần chấm", "Giả lập 300 câu, đo p50/p95"],
       ["Tài nguyên", "Huấn luyện và chạy trên GPU 6 GB, RAM trống khoảng 4–5 GB", "Cấu hình bf16, Adafactor, đọc dữ liệu dạng luồng"],
       ["Độ tin cậy", "Không đổi số, tên riêng, phủ định; hạn chế sửa quá tay", "Tỉ lệ sửa quá tay, tập kiểm thử tích hợp"],
       ["Dễ dùng", "Giao diện tối giản, nền trắng; chọn được bằng chuột hoặc bàn phím", "Thử trên trình duyệt, khổ điện thoại"],
       ["Tái lập", "Dữ liệu ghim theo commit, tham số trong tệp cấu hình", "127 bài kiểm thử tự động"]],
      [1.4, 4, 3])
    H3("Yêu cầu về dữ liệu, bảo mật và hiệu năng")
    P("Về dữ liệu: dữ liệu test không được xuất hiện trong dữ liệu huấn luyện dưới bất kỳ hình thức nào (kể cả câu trùng nội "
      "dung giữa hai bộ dữ liệu khác nhau); phải tuân thủ giấy phép, ví dụ ViLexNorm chỉ dùng cho nghiên cứu (CC BY-NC-SA 4.0). "
      "Về bảo mật: tin nhắn là dữ liệu riêng tư, nên toàn bộ xử lý diễn ra trên máy người dùng; nhật ký chỉ lưu cục bộ và không "
      "gửi đi đâu. Về hiệu năng: máy chủ chỉ cho GPU chạy một việc một lúc, và bỏ kết quả cũ nếu người dùng đã gõ thêm.")

    H2("Phân tích chức năng hệ thống")
    P("Hệ thống có một tác nhân là **người dùng**. Các trường hợp sử dụng chính được mô tả ở Bảng «T:use-case».")
    T("use-case", "Các trường hợp sử dụng chính",
      ["Mã", "Trường hợp sử dụng", "Luồng chính"],
      [["UC1", "Gõ và nhận gợi ý", "Người dùng gõ → hệ thống gạch chân từ chưa chắc → danh sách câu gợi ý trồi lên"],
       ["UC2", "Chọn câu gợi ý", "Bấm hoặc dùng phím mũi tên + Enter → câu trong khung được thay, các từ đó được khóa"],
       ["UC3", "Sửa lại câu trước", "Bấm con trỏ vào câu cũ → danh sách hiện phương án cho riêng câu đó"],
       ["UC4", "Gửi tin nhắn", "Bấm Gửi/Enter → câu đã sửa hiện trước, câu diễn đạt hiện sau; chữ trong khung giữ nguyên"],
       ["UC5", "Dùng câu đã sửa/diễn đạt", "Bấm một dòng → khung đổi thành câu đó, tiếp tục sửa được"],
       ["UC6", "Đổi chế độ", "Bấm biểu tượng tin nhắn hoặc văn bản ở góc trên bên trái"],
       ["UC7", "Soạn văn bản", "Gõ nhiều đoạn; Enter xuống dòng; danh sách hiện dưới dòng có con trỏ"]],
      [0.7, 2.3, 6], ["center", "left", "left"])

    H2("Thiết kế kiến trúc hệ thống")
    P("Kiến trúc gồm ba tầng (xem Hình «F:kien-truc»): giao diện trên trình duyệt, máy chủ Python giữ một phiên cho mỗi kết nối, và "
      "tầng dữ liệu/mô hình trên máy. Giao diện và máy chủ trao đổi qua WebSocket với các thông điệp *update* (chữ thay đổi), "
      "*pause* (người dùng dừng tay), *pick* (chọn gợi ý) và *send* (gửi). Streamlit [@streamlit] chỉ nhận chữ khi rời ô nhập "
      "nên không dùng được cho gợi ý khi gõ; demo Streamlit được giữ làm bản dự phòng cho chức năng sửa và diễn đạt.")
    F("kien-truc", "reports/figures/04_kien_truc_he_thong.png", "Kiến trúc tổng thể của hệ thống", 15.5)
    H3("Luồng sửa lỗi và diễn đạt lại khi gửi")
    P("Tin nhắn được mô hình sửa lỗi sinh N-best (4 phương án), gộp các phương án chỉ khác chữ hoa hoặc dấu câu cuối, bỏ "
      "phương án dưới 2% và giữ tối đa 3. Câu đã sửa đầu tiên được đưa vào mô hình diễn đạt lại để sinh 8 ứng viên (4 beam "
      "search, 4 lấy mẫu nucleus). Ứng viên bị loại nếu: làm mất hoặc đổi số, mã, giờ, ngày, tên riêng hoặc thêm/bỏ phủ định; "
      "cosine với câu đã sửa dưới 0,8; độ trùng từ trên 0,9 (gần như chép lại); hoặc không suy ra nhau theo NLI hai chiều:")
    E("nli", mt("min") + paren(mr("P(x⇒c), P(c⇒x)")) + mr("≥0,17"))
    P("Ngưỡng 0,17 là phân vị 10% trên 1.000 cặp câu do người viết của ViSP val, nghĩa là 90% câu diễn đạt của người vượt "
      "qua được. Các ứng viên còn lại được chấm điểm ưu tiên giữ nghĩa nhưng khác cách nói, rồi chọn theo MMR với λ = 0,5:")
    E("diem-ung-vien", mt("score") + paren(mr("c")) + mr("=") + mt("cos") + paren(mr("c,x")) + mr("+0,3·")
      + paren(mr("1−") + mt("overlap") + paren(mr("c,x"))))
    E("mmr", sup(mr("c"), mr("*")) + mr("=") + lim_low("argmax", mr("c∈R∖S"))
      + paren(mt("score") + paren(mr("c")) + mr("−λ·") + lim_low("max", mr("s∈S")) + mt("overlap") + paren(mr("c,s")), "[", "]"))
    P("Nếu câu đã sửa vẫn còn từ lạ (không có trong từ điển lấy từ câu chuẩn của tập train), hệ thống không đưa câu diễn "
      "đạt, vì câu diễn đạt sinh từ câu còn lỗi gần như luôn vô nghĩa.")
    H3("Luồng gợi ý khi gõ")
    P("Phiên gợi ý chỉ xử lý những từ đã gõ xong (có dấu cách hoặc dấu câu theo sau); từ đang gõ dở không bị đụng tới. Với mỗi "
      "từ, **tầng từ điển** sinh tối đa 10 ứng viên từ bảng sửa lỗi trích từ dữ liệu train, từ điển viết tắt [@nsw], bộ giải "
      "mã Telex/VNI tự viết, các cách thêm/đổi dấu, các từ gần giống và cách tách dính chữ. Ứng viên được xếp bằng điểm kênh "
      "nhiễu cộng bigram với từ trước và từ sau, tức là chọn chuỗi c_{1}…c_{n} có điểm:")
    E("diem-duong", mr("S=") + nary("∑", mr("i=1"), mr("n"), paren(mr("α·") + mt("log ") + mr("P(") + sub(mr("t"), mr("i"))
      + mr("|") + sub(mr("c"), mr("i")) + mr(")+") + mt("log ") + mr("P(") + sub(mr("c"), mr("i")) + mr("|")
      + sub(mr("c"), mr("i−1")) + mr(")"), "[", "]")))
    P("Khi người dùng dừng tay 350 ms, **tầng ViT5** chấm lại các từ chưa khóa bằng log-xác suất câu ứng viên cho trước câu "
      "nguồn (một lượt tính, không cần giải mã). Một từ được **khóa** khi người dùng đã chọn hoặc khi đã cách từ đang gõ hai "
      "từ; từ đã khóa không bị xếp lại nữa để danh sách không nhảy liên tục, nhưng nếu gợi ý đầu vẫn khác chữ đang hiện thì "
      "người dùng vẫn sửa được. Danh sách gợi ý là tối đa 3 **câu hoàn chỉnh** ghép từ các phương án của những từ chưa chắc, "
      "xếp theo tổng độ lệch điểm so với phương án đầu; chỉ tính trong câu chứa con trỏ (tách theo . ! ? … và xuống dòng).")

    H2("Thiết kế dữ liệu")
    P("Đồ án không dùng cơ sở dữ liệu quan hệ. Dữ liệu đi qua một luồng xử lý cố định (xem Hình «F:luong-du-lieu») và được lưu "
      "dạng tệp: `data/raw` (dữ liệu tải về), `data/processed/<tên>/{train,val,test}.jsonl` (cột chuẩn *source*, *target*), "
      "`data/processed/correction` (tập gộp để huấn luyện sửa lỗi). Mọi bước được điều khiển bởi tệp cấu hình "
      "`configs/data.yaml`.")
    F("luong-du-lieu", "reports/figures/04_luong_du_lieu.png", "Luồng xử lý dữ liệu và chống rò rỉ", 15.5)
    H3("Các bộ dữ liệu và cách chia tập")
    T("du-lieu", "Các bộ dữ liệu sau khi làm sạch",
      ["Dataset", "Vai trò", "Số mẫu (train / val / test)", "Giấy phép, lưu ý"],
      [["VSEC [@vsec]", "Sửa lỗi, văn bản trang trọng", "9.341 (7.473 / 934 / 934)", "Không ghi giấy phép; trích dẫn bài báo"],
       ["ViLexNorm [@vilexnorm]", "Sửa lỗi kiểu tin nhắn; **tập test chính**", "10.458 (8.370 / 1.047 / 1.041)",
        "CC BY-NC-SA 4.0, chỉ cho nghiên cứu"],
       ["VEC [@vec]", "Chỉ bổ sung train (nhãn do LLM sinh)", "61.591 (49.454 / 6.079 / 6.058)", "MIT; đã bỏ phần trùng ViLexNorm"],
       ["ViSP [@visp]", "Diễn đạt lại", "46.922 cụm; 91.566 cặp (66.058 / 12.857 / 12.651)", "Trích dẫn NAACL Findings 2025"]],
      [1.6, 2.6, 2.6, 2.4])
    P("Tập test của từng bộ dữ liệu luôn được giữ riêng và báo cáo riêng; tập gộp để huấn luyện sửa lỗi gồm 65.297 cặp train "
      "và 8.060 cặp val, đã loại mọi câu nằm trong test của bất kỳ bộ dữ liệu nào. Hai phát hiện quan trọng trong bước này "
      "được trình bày ở mục 4.2.1. Ba bộ dữ liệu sửa lỗi bổ sung cho nhau về kiểu lỗi (Hình «F:kieu-loi»): VSEC chủ yếu là "
      "thiếu hoặc sai dấu (65%), ViLexNorm chủ yếu là viết tắt và teencode (60%), còn VEC trộn cả hai.")
    F("kieu-loi", "reports/figures/01_edit_types.png", "Phân bố kiểu lỗi trong ba bộ dữ liệu sửa lỗi (mẫu 8.000 câu mỗi bộ)", 14)
    H3("Dữ liệu lỗi nhân tạo")
    P("Để mô hình học được lỗi gõ nhanh, đồ án sinh tự động 89.190 câu lỗi từ 45.230 câu chuẩn kiểu tin nhắn **của tập train**, "
      "theo hai hồ sơ: *single* (25%, mỗi câu 1–2 lỗi như đổi dấu, xóa hoặc đảo ký tự, phím bên cạnh, nhầm phụ âm s/x, ch/tr) "
      "và *fast_typing* (75%, bỏ dấu cả câu hoặc một phần, chồng thêm 0–3 lỗi gõ, Telex chưa chuyển, dính chữ). Câu sinh ra "
      "trùng với câu val/test bị bỏ; từ có chữ số không bị gây lỗi.")
    H3("Từ điển gợi ý khi gõ")
    T("tu-dien", "Thành phần của từ điển `lexicon.json`",
      ["Thành phần", "Số mục", "Nguồn"],
      [["Unigram (từ và số lần xuất hiện)", "16.522", "Câu chuẩn của tập train sửa lỗi"],
       ["Bigram", "323.704", "Câu chuẩn của tập train sửa lỗi"],
       ["Bảng từ gốc → từ đúng", "35.593", "Các phép sửa trong cặp câu train (không dùng val/test)"],
       ["Từ điển viết tắt", "2.385", "vn-nsw-dictionary [@nsw] và 1 mục thêm tay (kcj)"]],
      [3.2, 1.3, 4.5], ["left", "center", "left"])
    P("Tệp từ điển có kích thước khoảng 7,3 MB. Danh sách âm tiết Viet74K đã được thử nhưng bị bỏ vì chỉ tăng độ phủ đáp án "
      "0,13 điểm phần trăm và không cải thiện F0.5 trên tập validation.")

    H2("Thiết kế giao diện người dùng")
    P("Giao diện được thiết kế theo nguyên tắc tối giản: người dùng chỉ thấy khung soạn thảo và danh sách gợi ý khi cần, "
      "không có nút bấm hay bảng điều khiển thừa. Mục này mô tả cấu trúc giao diện, hai chế độ sử dụng (tin nhắn và văn bản) "
      "và quy trình tương tác của người dùng.")
    H3("Sơ đồ điều hướng và cấu trúc giao diện")
    P("Ứng dụng là một trang duy nhất, nền trắng, không có lịch sử trò chuyện. Góc trên bên trái có hai biểu tượng để chuyển "
      "giữa **chế độ tin nhắn** và **chế độ văn bản**; trang ghi nhớ chế độ đã chọn. Mỗi chế độ chỉ có một khung soạn thảo và "
      "một danh sách gợi ý trồi lên khi cần.")
    H3("Giao diện chế độ tin nhắn")
    P("Một khung soạn tin bo tròn ở giữa phía dưới trang, bên phải là nút Gửi. Từ chưa chắc được gạch chân đỏ ngay trong "
      "khung bằng một lớp chữ trong suốt nằm dưới ô nhập. Danh sách “Gợi ý cho câu này” trồi lên ngay phía trên khung, mỗi dòng "
      "là cả câu, các từ khác với chữ đang gõ được in đậm. Sau khi gửi, danh sách gồm hai phần “Câu đã sửa” và “Diễn đạt lại "
      "ý”; chữ trong khung giữ nguyên để người dùng tự quyết định.")
    H3("Giao diện chế độ văn bản")
    P("Một trang giấy trắng rộng, chữ Times New Roman, gõ được nhiều đoạn như phần mềm soạn thảo. Chế độ này dùng đúng các "
      "tính năng gợi ý khi gõ nhưng không có nút Gửi, nên chỉ sửa chính tả và không diễn đạt lại; danh sách gợi ý hiện ngay dưới "
      "dòng có con trỏ. Chế độ này cho thấy hệ thống có thể tích hợp vào phần mềm soạn văn bản, không chỉ ô nhắn tin.")
    H3("Mô tả quy trình tương tác của người dùng")
    B(["Gõ một từ rồi nhấn dấu cách: từ chưa chắc được gạch chân, danh sách câu gợi ý trồi lên (hoặc tự đổi nếu là Telex chắc chắn).",
       "Chọn bằng chuột, hoặc phím mũi tên lên/xuống rồi Enter; Esc để ẩn danh sách.",
       "Gõ . ! ? hoặc xuống dòng để sang câu mới; bấm vào câu cũ để xem lại gợi ý cho câu đó.",
       "Ở chế độ tin nhắn, Enter hoặc nút Gửi để nhận câu đã sửa và câu diễn đạt; Shift+Enter để xuống dòng.",
       "Bấm một dòng trong kết quả để đưa câu đó vào khung và tiếp tục chỉnh sửa."])

    H2("Tổng kết chương")
    P("Chương 3 đã phân tích yêu cầu, xác định bảy chức năng chính và các yêu cầu phi chức năng về tốc độ, tài nguyên và độ "
      "tin cậy; thiết kế kiến trúc ba tầng với hai luồng xử lý (gợi ý khi gõ và sửa khi gửi); thiết kế luồng dữ liệu chống rò "
      "rỉ, dữ liệu lỗi nhân tạo, từ điển; và thiết kế giao diện tối giản với hai chế độ.")


def chapter4():
    H1("XÂY DỰNG, KIỂM THỬ VÀ ĐÁNH GIÁ ỨNG DỤNG")
    H2("Môi trường và công cụ triển khai")
    T("phan-cung", "Cấu hình phần cứng và phần mềm",
      ["Thành phần", "Cấu hình"],
      [["CPU", "Intel Core i5-12450HX (thế hệ 12)"], ["GPU", "NVIDIA GeForce RTX 3050 Laptop, 6 GB VRAM"],
       ["RAM", "16 GB (trống khoảng 4–5 GB khi chạy)"], ["Hệ điều hành", "Windows 11"],
       ["Phần mềm", "Python 3.14.7, PyTorch 2.14.1 + CUDA 12.6, Transformers 5.20.1, sentence-transformers 6.1.0, "
                    "websockets 17.2, Streamlit 1.66, pytest 9.1, Git 2.54"]],
      [2, 7])
    P("**Ước tính tài nguyên.** Giới hạn lớn nhất là 6 GB VRAM. ViT5-base được huấn luyện với bf16 (T5 dễ tràn số khi dùng "
      "fp16), bộ tối ưu Adafactor [@adafactor] và gradient checkpointing [@checkpoint], batch 16 với tích lũy gradient 2 (batch "
      "hiệu dụng 32), độ dài câu tối đa 128 token; khi đó việc huấn luyện chiếm khoảng 5 GB VRAM, nên mỗi lúc GPU chỉ chạy một "
      "việc nặng. RAM trống chỉ khoảng 4–5 GB, nên 1,18 triệu dòng thô của ViSP được đọc dạng luồng thay vì nạp hết vào bộ nhớ. "
      "Thời gian huấn luyện thực tế ở Bảng «T:tai-nguyen».")
    T("tai-nguyen", "Thời gian huấn luyện và sử dụng tài nguyên",
      ["Mô hình", "Dữ liệu", "Epoch", "Thời gian", "Val loss"],
      [["Sửa lỗi v1", "65.297 cặp thật", "3", "77 phút", "0,288"],
       ["Sửa lỗi v2 (GĐ1)", "154.487 cặp (thật + nhân tạo)", "2", "100 phút", "0,256"],
       ["Sửa lỗi v2 + GĐ2 (chọn)", "65.297 cặp thật, lr 1e-4", "1", "19 phút", "0,254"],
       ["Diễn đạt lại", "66.058 cặp ViSP", "2", "48 phút", "1,089"],
       ["Diễn đạt lại + 2 epoch (thử)", "66.058 cặp ViSP", "+2", "43,7 phút", "1,199"]],
      [2.6, 3, 0.8, 1.2, 1.1], ["left", "left", "center", "center", "center"])

    H2("Hiện thực hóa hệ thống")
    P("Mục này mô tả cách hiện thực từng thành phần theo thiết kế ở Chương 3, theo đúng thứ tự xây dựng: xử lý dữ liệu, "
      "huấn luyện mô hình sửa lỗi, mô hình diễn đạt lại, từ điển và gợi ý khi gõ, cuối cùng là ứng dụng demo. Mã nguồn tương "
      "ứng của từng phần được nêu kèm để có thể đối chiếu và tái lập.")
    H3("Tiền xử lý và chia dữ liệu")
    P("Bước làm sạch chỉ chuẩn hóa Unicode NFC và gộp khoảng trắng, **không** hạ chữ thường hay bỏ dấu vì lỗi dấu chính là "
      "thứ cần sửa. Hai phát hiện quan trọng khi khảo sát dữ liệu đã thay đổi cách làm:")
    B(["**ViSP là khoảng 47 nghìn cụm, không phải 1,2 triệu cặp độc lập.** Mỗi mã *original_id* là một cụm n câu đồng nghĩa "
       "(n = 2–12), và dữ liệu thô liệt kê mọi cặp có thứ tự n(n−1) trong cụm. Đồ án lấy 2 cặp mỗi cụm, các câu còn lại dùng "
       "làm tham chiếu khi đánh giá; đồng thời bỏ 1.001 dòng val và 1.275 dòng test có câu trùng với train.",
       "**VEC chứa 83% ViLexNorm.** 8.650/10.463 câu ViLexNorm nằm sẵn trong VEC với 99,8% nhãn giống hệt. Nếu giữ nguyên, mô "
       "hình huấn luyện trên VEC đã thấy phần lớn tập test ViLexNorm và dữ liệu CC BY-NC-SA bị phát hành lại dưới MIT. Đồ án "
       "bỏ 8.665 dòng VEC trùng ViLexNorm.",
       "Kiểm tra chéo sau khi gộp: 0 câu test nào nằm trong train của bộ dữ liệu khác; hàm chia tập dừng chương trình nếu còn "
       "phát hiện trùng lặp."])
    H3("Huấn luyện mô hình sửa lỗi hai giai đoạn")
    P("Bản v1 chỉ học dữ liệu thật. Thử demo cho thấy v1 gần như không sửa được lỗi gõ nhanh, nên bản v2 (giai đoạn 1) học "
      "thêm 89.190 câu lỗi nhân tạo. v2 sửa lỗi gõ tốt hơn hẳn nhưng lại “sửa hăng” trên tin nhắn thật (sai 88 câu mà v1 "
      "đúng, ví dụ *hường phấn* → *hưởng phấn*), vì lỗi nhân tạo dạng từ đúng → từ đúng khác dạy mô hình nghi ngờ cả từ "
      "đúng. Giai đoạn 2 tinh chỉnh tiếp v2 thêm 1 epoch chỉ trên dữ liệu thật với learning rate nhỏ, kéo kết quả trên tin "
      "nhắn thật về ngang v1 mà vẫn giữ gần hết khả năng sửa lỗi gõ. Ngoài ra, các ký tự ngoài bộ từ vựng của tokenizer ($, "
      "dấu ngoặc kép cong, emoji, “=))”) bị mã hóa thành `<unk>` khiến 6,6% câu chuẩn ViLexNorm test không thể tái tạo; "
      "chúng được khôi phục từ câu nguồn theo vị trí. Đường loss của các lần huấn luyện ở Hình «F:loss»: val loss của mô hình "
      "sửa lỗi giảm đều qua cả hai giai đoạn, còn khi huấn luyện thêm mô hình diễn đạt lại, val loss tăng ngay từ lần đo đầu "
      "trong khi train loss giảm mạnh, dấu hiệu mô hình bắt đầu học thuộc dữ liệu.")
    F("loss", "reports/figures/03_loss_curves.png", "Đường loss khi huấn luyện mô hình sửa lỗi và mô hình diễn đạt lại", 15.5)
    H3("Mô hình diễn đạt lại và bộ lọc")
    P("ViT5-base được tinh chỉnh 2 epoch trên 66.058 cặp ViSP. Bộ lọc và xếp hạng được cài trong `src/pipeline/ranker.py` theo "
      "thiết kế ở mục 3.4.1. Thử huấn luyện thêm 2 epoch làm val loss tăng từ 1,089 lên 1,199 và giảm BLEU, nên mô hình 2 epoch "
      "được giữ lại.")
    H3("Từ điển, gợi ý khi gõ và các cách kết hợp")
    P("Bảng sửa lỗi được trích từ các phép sửa mức từ trong cặp câu train; bộ giải mã Telex/VNI tự viết trả về mọi dạng hợp lệ "
      "(cả hai kiểu bỏ dấu *hòa*/*hoà*). Ngoài việc dùng từ điển cho gợi ý khi gõ, đồ án thử bốn cách dùng cho chức năng sửa "
      "cả câu: (A) mô hình hiện tại; (B) chỉ từ điển và bigram; (C) “lá chắn”: phép sửa của mô hình phải nằm trong ứng viên "
      "từ điển, nếu không thì giữ từ gốc; (D) “chọn lại”: gộp câu ghép từ từ điển với N-best của mô hình, mô hình chấm lại và "
      "cộng điểm từ điển:")
    E("chon-lai", mt("score") + paren(mr("c")) + mr("=") + mt("log ") + sub(mr("P"), mr("θ")) + paren(mr("c|x"))
      + mr("+β·") + mt("prior") + paren(mr("x,c")))
    P("trong đó prior(x, c) là tổng điểm kênh nhiễu của các phép biến *x* thành *c*, phép sửa ngoài từ điển bị phạt −8; tham "
      "số (k = 10, α = 2, β = 1) chỉ chọn trên 1.847 câu validation theo F0.5.")
    H3("Ứng dụng demo")
    P("Máy chủ `app/realtime/server.py` nạp một lần toàn bộ mô hình (sửa lỗi, diễn đạt lại, mô hình nhúng câu, NLI), giữ một "
      "đối tượng phiên cho mỗi kết nối WebSocket và đưa mọi việc dùng GPU vào một hàng đợi một luồng. Trang "
      "`app/realtime/index.html` viết bằng HTML/JavaScript thuần, không dùng thư viện ngoài. Lệnh chạy: "
      "`python -m app.realtime.server`, sau đó mở http://localhost:8765.")

    H2("Kết quả xây dựng ứng dụng")
    P("Hình «F:demo-go» đến «F:demo-van-ban» là ảnh chụp ứng dụng thực tế. Khi gõ *con yeu qua nguowif hok*, từ *nguowif* được "
      "tự đổi thành “người”, các từ chưa chắc được gạch chân và danh sách đưa ba câu hoàn chỉnh (Hình «F:demo-go»). Sau khi "
      "gửi, hệ thống trả ba câu đã sửa và một câu diễn đạt (Hình «F:demo-gui»). Ở chế độ văn bản, danh sách chỉ áp dụng cho "
      "đoạn đang gõ (Hình «F:demo-van-ban»).")
    F("demo-go", "reports/figures/demo_tin_nhan_dang_go.png", "Chế độ tin nhắn: gợi ý cả câu trong lúc gõ", 12.5)
    F("demo-gui", "reports/figures/demo_tin_nhan_sau_khi_gui.png", "Chế độ tin nhắn: câu đã sửa và câu diễn đạt sau khi gửi", 12.5)
    F("demo-van-ban", "reports/figures/demo_van_ban.png", "Chế độ văn bản: gợi ý cho đoạn đang gõ", 15.5)
    P("Hình «F:demo-gui» cũng cho thấy hạn chế còn lại của bước diễn đạt: câu “Con yêu quá mức, nên không đi chơi nha.” đã "
      "thêm quan hệ nguyên nhân không có trong câu gốc. Hạn chế này được định lượng ở mục 4.4.3.")

    H2("Kiểm thử hệ thống")
    P("Việc kiểm thử nhằm trả lời hai câu hỏi: hệ thống có hoạt động đúng như các yêu cầu ở Chương 3 không, và chất "
      "lượng sửa lỗi, diễn đạt lại đạt mức nào so với các mốc so sánh. Mục này trình bày phương pháp kiểm thử, các trường "
      "hợp kiểm thử, kết quả và các lỗi đã gặp cùng cách xử lý.")
    H3("Phương pháp và kế hoạch kiểm thử")
    P("Kiểm thử được tổ chức theo năm mức: (1) **kiểm thử đơn vị** tự động bằng pytest (127 bài, chạy dưới 10 giây) cho chỉ "
      "số đánh giá, chia tập, chống rò rỉ, sinh lỗi, giải mã Telex, từ điển và phiên gợi ý; (2) **đánh giá ngoại tuyến** trên "
      "ba tập test; (3) **stress test** gồm 400 câu chuẩn ViLexNorm test bị gây lỗi tự động theo 8 kiểu (seed 2026, khác seed "
      "tạo dữ liệu train); (4) **giả lập người dùng gõ** từng từ trên 300 câu; (5) **kiểm thử giao diện** trên trình duyệt và "
      "**chấm thủ công**. Mọi mẫu lỗi đều được sinh tự động.")
    P("**Chỉ số sửa lỗi.** WER và CER dựa trên khoảng cách chỉnh sửa [@levenshtein] ở mức từ và mức ký tự, với S, D, I là số "
      "phép thay, xóa, chèn và N là số từ của câu chuẩn:")
    E("wer", mt("WER") + mr("=") + frac(mr("S+D+I"), mr("N")))
    P("Vì phần lớn từ trong câu đã đúng sẵn, WER dễ cho kết quả đẹp giả tạo. Đồ án bổ sung độ chính xác P, độ phủ R và F0.5 "
      "trên từng phép sửa mức từ, theo tinh thần của ERRANT [@errant], với β = 0,5 để ưu tiên độ chính xác (sửa sai câu của "
      "người dùng tệ hơn bỏ sót một lỗi):")
    E("prf", mr("P=") + frac(mr("TP"), mr("TP+FP")) + mr(",  R=") + frac(mr("TP"), mr("TP+FN")) + mr(",  ")
      + sub(mr("F"), mr("β")) + mr("=") + frac(paren(mr("1+") + sup(mr("β"), mr("2"))) + mr("·P·R"), sup(mr("β"), mr("2")) + mr("·P+R")))
    P("Tỉ lệ sửa quá tay đo trên tập D gồm các câu chuẩn được đưa thẳng vào hệ thống f:")
    E("qua-tay", mt("OC") + mr("=") + frac(mr("1"), mr("|D|")) + nary("∑", mr("y∈D"), "", mr("1") + paren(mr("f(y)≠y"), "[", "]")))
    P("**Chỉ số diễn đạt lại.** BLEU [@bleu] tính trung bình nhân độ chính xác n-gram p_{n} (n = 1…4) nhân hệ số phạt câu ngắn "
      "BP; iBLEU [@ibleu] trừ đi độ giống với câu nguồn *x* để phạt việc chép lại, với R là tập câu tham chiếu:")
    E("bleu", mt("BLEU") + mr("=") + mt("BP") + mr("·") + mt("exp") + paren(nary("∑", mr("n=1"), mr("4"), frac(mr("1"), mr("4"))
      + mt("log ") + sub(mr("p"), mr("n")))))
    E("ibleu", mt("iBLEU") + mr("=0,8·") + mt("BLEU") + paren(mr("c,R")) + mr("−0,2·") + mt("BLEU") + paren(mr("c,x")))

    H3("Các trường hợp kiểm thử")
    T("test-case", "Một số trường hợp kiểm thử chức năng và kết quả",
      ["Mã", "Trường hợp", "Kết quả mong đợi", "Kết quả"],
      [["TC01", "Gõ *nguowif* + dấu cách", "Tự đổi thành “người”", "Đạt"],
       ["TC02", "Gõ *con yeu qua* + dấu cách", "Gạch chân, 3 câu gợi ý, không tự đổi", "Đạt"],
       ["TC03", "Gõ *kcj* rồi chọn gợi ý", "Thay bằng “không có gì”, gõ tiếp bình thường", "Đạt"],
       ["TC04", "Từ đang gõ dở (chưa có dấu cách)", "Không bị thay đổi", "Đạt"],
       ["TC05", "Gõ dấu chấm rồi gõ câu mới", "Danh sách chỉ cho câu mới", "Đạt"],
       ["TC06", "Bấm vào câu trước, chọn gợi ý", "Chỉ câu trước bị thay", "Đạt"],
       ["TC07", "Số thập phân *3.5*", "Không bị coi là hết câu", "Đạt"],
       ["TC08", "Gõ nhanh làm từ cũ bị khóa", "Vẫn sửa được từ đã khóa nếu gợi ý khác", "Đạt (sau khi sửa lỗi)"],
       ["TC09", "Gửi tin nhắn", "Câu đã sửa ~0,4 s, câu diễn đạt ~1,4 s", "Đạt"],
       ["TC10", "Chế độ văn bản, Enter", "Xuống dòng, không gửi; đoạn mới là câu mới", "Đạt"],
       ["TC11", "Khổ điện thoại 375 px", "Không tràn ngang, chữ tự xuống dòng", "Đạt"]],
      [0.8, 2.8, 3.6, 1.6], ["center", "left", "left", "center"])
    P("Ngoài ra, tập kiểm thử tích hợp gồm 41 câu kiểu tin nhắn chia bốn nhóm: A (lỗi dấu), B (viết tắt, không dấu), C (cần "
      "diễn đạt lại), D (đã đúng), có cột ghi số, tên, phủ định phải giữ nguyên. Các câu này do công cụ AI soạn nháp và được "
      "người làm đồ án duyệt lại toàn bộ; không dùng để huấn luyện.")

    H3("Kết quả kiểm thử")
    P("**Mốc chép nguyên đầu vào.** Bảng «T:moc» cho thấy chỉ cần không sửa gì, WER trên VSEC đã là 3,81%, nên WER chỉ có ý nghĩa "
      "khi so với mốc này. Trên ViSP, chép nguyên câu gốc có BLEU (76,1) cao hơn cả câu diễn đạt do người viết (74,2): BLEU "
      "không thể dùng một mình để đánh giá diễn đạt lại.")
    T("moc", "Kết quả của mốc chép nguyên đầu vào",
      ["Tập test", "CER", "WER", "Câu đúng hết"],
      [["VSEC (934 câu)", "1,12%", "3,81%", "0%"], ["ViLexNorm (1.041 câu)", "9,92%", "16,86%", "0%"],
       ["VEC (6.058 câu, tham khảo)", "14,13%", "40,45%", "17,45%"]],
      [3.5, 1.5, 1.5, 1.8], ["left", "center", "center", "center"])
    P("**So sánh các mô hình sửa lỗi (RQ1).** Bảng «T:mo-hinh» trình bày kết quả trên ba tập test, mỗi ô gồm WER / tỉ lệ câu đúng hết / "
      "tỉ lệ sửa quá tay. Mô hình được chọn giảm WER trên ViLexNorm từ 16,9% xuống 3,74% (bớt khoảng 4/5 số từ sai) và trên "
      "VSEC từ 3,81% xuống 1,16%. Mô hình có sẵn dựa trên BARTpho, học trên văn bản tin tức, không chuyển được sang miền tin "
      "nhắn: tự thêm dấu câu và viết hoa vào 94% câu đúng của ViLexNorm. F0.5 trên phép sửa của mô hình được chọn là 0,83 trên "
      "cả ViLexNorm và VSEC.")
    T("mo-hinh", "So sánh các mô hình sửa lỗi trên tập test (WER / câu đúng hết / sửa quá tay)",
      ["Hệ thống", "ViLexNorm (1.041)", "VSEC (934)", "VEC (6.058, tham khảo)"],
      [["Chép nguyên đầu vào", "16,9% / 0% / 0%", "3,81% / 0% / 0%", "40,5% / 17,5% / 0%"],
       ["v1 (dữ liệu thật)", "3,72% / 69,8% / 10,9%", "1,24% / 67,7% / 4,4%", "8,84% / 51,4% / 7,3%"],
       ["v2 (thêm lỗi nhân tạo)", "5,00% / 66,5% / 12,3%", "1,22% / 68,8% / 4,7%", "8,19% / 51,3% / 9,6%"],
       ["**v2 + GĐ2 (được chọn)**", "**3,74% / 68,4% / 14,3%**", "**1,16% / 70,1% / 4,1%**", "**7,69% / 52,6% / 9,1%**"],
       ["Mô hình có sẵn (BARTpho)", "31,0% / 0,3% / 93,9%", "3,87% / 13,2% / 19,6%", "40,9% / 5,4% / 53,7%"]],
      [2.6, 2.3, 2.2, 2.3], ["left", "center", "center", "center"])
    P("**Stress test theo kiểu lỗi.** Hình «F:stress» và Bảng «T:stress» cho thấy dữ liệu lỗi nhân tạo giúp rõ rệt với lỗi gõ: tỉ lệ câu "
      "“gõ nhanh” sửa đúng hết tăng từ 6,5% (v1) lên 26,5%. Khi cho người dùng chọn trong 3 phương án, tỉ lệ có câu đúng tăng "
      "thêm 5–14 điểm tùy kiểu lỗi (khoảng 8 điểm trên tập test thật).")
    F("stress", "reports/figures/03_stress_top1_top3.png", "Tỉ lệ câu sửa đúng hoàn toàn theo kiểu lỗi (top-1 và top-3)", 15.5)
    T("stress", "Stress test: câu đúng ở phương án đầu / có trong 3 phương án",
      ["Kiểu lỗi", "WER đầu vào", "v1", "v2 + GĐ2 (được chọn)"],
      [["Câu đã đúng (sửa quá tay)", "0%", "90,0% / 93,0%", "87,0% / 92,5%"],
       ["Không dấu cả câu", "74,3%", "23,8% / 36,8%", "45,8% / 59,5%"],
       ["Đảo chữ", "13,2%", "34,8% / 43,0%", "68,2% / 78,8%"],
       ["Bấm hụt/thiếu chữ", "12,8%", "22,2% / 27,5%", "42,0% / 50,7%"],
       ["Phím bên cạnh", "12,6%", "30,0% / 40,0%", "58,2% / 68,2%"],
       ["Phím đúp", "13,1%", "68,8% / 75,2%", "80,2% / 89,8%"],
       ["Sai dấu thanh/dấu chữ", "12,4%", "24,8% / 33,0%", "58,2% / 69,8%"],
       ["Gõ nhanh: không dấu + 1–2 lỗi gõ", "76,4%", "6,5% / 10,2%", "26,5% / 36,8%"]],
      [3.2, 1.4, 2, 2.2], ["left", "center", "center", "center"])
    P("**Diễn đạt lại (RQ2).** Trên 2.000 câu ViSP test (Bảng «T:dien-dat»), mô hình có BLEU gần bằng việc chép câu gốc nhưng "
      "self-BLEU 74,2 cho thấy câu sinh ra vẫn khá giống câu gốc; iBLEU 45,9 nằm giữa chép câu gốc (40,8) và câu do người viết "
      "(49,5).")
    T("dien-dat", "Kết quả diễn đạt lại trên 2.000 câu ViSP test",
      ["Hệ thống", "BLEU tham chiếu", "self-BLEU", "iBLEU", "Giống nghĩa"],
      [["Chép câu gốc", "76,0", "100", "40,8", "1,00"], ["ViT5-base tinh chỉnh", "75,9", "74,2", "45,9", "0,97"],
       ["Câu do người viết", "73,9", "47,9", "49,5", "0,92"]],
      [2.6, 1.6, 1.4, 1.2, 1.4], ["left", "center", "center", "center", "center"])
    P("Để biết câu diễn đạt có thật sự dùng được trên tin nhắn, người làm đồ án chấm thủ công 85 gợi ý của 40 tin nhắn thật "
      "từ ViLexNorm test (1 = đúng ý, tự nhiên, không thêm/bỏ ý). Kết quả ở Bảng «T:cham-tay» cho thấy **chỉ số tự động đánh giá "
      "quá cao khoảng 2,5 lần**: tự động cho đạt 87,1% còn người chỉ chấp nhận 34,1%; tương quan Spearman với điểm của người "
      "chỉ 0,27 (cosine) và 0,14 (NLI). Lý do bị chấm 0 chủ yếu là lạc ý (23 gợi ý) và câu lủng củng (19 gợi ý), vì mô hình "
      "học trên văn bản trang trọng của ViSP, không hợp với tin nhắn ngắn và văn nói.")
    T("cham-tay", "Đánh giá thủ công 85 gợi ý diễn đạt lại",
      ["Chỉ số", "Kết quả"],
      [["Gợi ý đầu đạt (Top-1)", "35,0%"], ["Có ít nhất 1 gợi ý đạt (Top-3)", "52,5%"],
       ["Tỉ lệ đạt mỗi gợi ý (người chấm)", "34,1%"], ["Tỉ lệ đạt theo chấm tự động (cosine ≥ 0,8 và NLI ≥ 0,17)", "87,1%"],
       ["Người và máy cùng kết luận", "44,7%"], ["Khi bước sửa lỗi đúng hoàn toàn: Top-1 / Top-3", "38,7% / 61,3%"],
       ["Khi bước sửa lỗi sai: Top-1 / Top-3", "22,2% / 22,2%"]],
      [6, 2.5], ["left", "center"])
    P("**Sửa lỗi trước hay diễn đạt thẳng (RQ3).** Dùng 150 câu của stress test, so ba cách: diễn đạt thẳng câu lỗi, sửa lỗi "
      "rồi diễn đạt (cách hệ thống dùng) và diễn đạt câu chuẩn (cận trên). Kết quả ở Bảng «T:rq3» (gợi ý đầu đạt / có ít nhất 1 "
      "gợi ý đạt, chấm tự động nên chỉ dùng để so sánh tương đối).")
    T("rq3", "So sánh diễn đạt thẳng câu lỗi và sửa lỗi trước",
      ["Kiểu lỗi", "Diễn đạt thẳng", "Sửa lỗi rồi diễn đạt", "Câu chuẩn (cận trên)"],
      [["Câu đã đúng", "78,0% / 78,0%", "75,3% / 75,3%", "80,0% / 80,0%"],
       ["Không dấu cả câu", "1,3% / 2,0%", "53,3% / 56,0%", "80,0% / 80,0%"],
       ["Bấm hụt/thiếu chữ", "36,0% / 41,3%", "58,0% / 61,3%", "80,0% / 80,0%"],
       ["Sai dấu thanh/dấu chữ", "28,0% / 32,7%", "66,0% / 67,3%", "80,0% / 80,0%"],
       ["Gõ nhanh", "1,3% / 1,3%", "38,7% / 46,7%", "80,0% / 80,0%"]],
      [2.6, 2, 2.4, 2.2], ["left", "center", "center", "center"])
    P("**Kết hợp từ điển và mô hình.** Bảng «T:ket-hop» so sánh bốn cách A–D (mục 4.2.3). Điều kiện giữ C hoặc D được đặt trước "
      "khi chạy test: WER ViLexNorm không tệ hơn A, sửa quá tay ViLexNorm thấp hơn A, tỉ lệ câu “gõ nhanh” giảm không quá 1 "
      "điểm. C trượt hai điều kiện; D tốt hơn rõ trên tin nhắn thật (WER 3,25%, câu đúng 72,3%) nhưng giảm 5,6 điểm ở câu gõ "
      "nhanh và tệ hơn trên VSEC, nên **chức năng sửa cả câu giữ mô hình A**.")
    T("ket-hop", "So sánh các cách kết hợp từ điển và mô hình (WER / câu đúng hết / sửa quá tay)",
      ["Tập", "A. Mô hình", "B. Từ điển", "C. Lá chắn", "D. Chọn lại"],
      [["ViLexNorm test", "3,74% / 68,4% / 14,3%", "5,59% / 58,0% / 29,1%", "3,76% / 69,6% / 10,6%", "3,25% / 72,3% / 11,1%"],
       ["VSEC test", "1,16% / 70,1% / 4,1%", "2,14% / 53,9% / 19,5%", "1,25% / 68,0% / 3,2%", "1,40% / 62,7% / 2,1%"],
       ["Stress không dấu (câu đúng)", "45,8%", "28,5%", "46,5%", "43,5%"],
       ["Stress gõ nhanh (câu đúng)", "26,8%", "9,8%", "22,8%", "21,2%"]],
      [2.2, 1.9, 1.9, 1.9, 1.9], ["left", "center", "center", "center", "center"])
    P("Đồ án thử tiếp một cách “chia đường”: dùng A cho câu gần như không dấu hoặc có từ lạ hoàn toàn, còn lại dùng D. Tỉ lệ "
      "từ có dấu của câu *x* được tính như sau:")
    E("ti-le-dau", mr("r(x)=") + frac(mr("|{w∈x : w có dấu}|"), mr("|{w∈x}|")))
    P("Cách chia chỉ được chọn trên tập validation (val thật và 200 câu ViLexNorm val × 8 kiểu lỗi, seed 7), với quy tắc đặt "
      "trước là không kiểu lỗi nào được tụt quá 1 điểm so với A. Không cách chia nào đạt, vì điểm yếu thật của D là lỗi gõ "
      "phím trong câu **có dấu** (val: bấm hụt 43,5% → 33,5%, phím bên cạnh 57,0% → 46,5%), mà dấu hiệu theo dấu không tách "
      "được. Đây là một kết quả âm nhưng chỉ rõ hướng cải thiện tiếp theo.")
    P("**Gợi ý khi gõ.** Giả lập phát lại từng từ của 300 câu ViLexNorm test (4–25 từ), với tầng từ điển và tầng ViT5. “Chọn "
      "đúng” giả định người dùng luôn nhận ra đáp án nên là cận trên.")
    T("gia-lap", "Giả lập gợi ý khi gõ trên 300 câu",
      ["Đầu vào", "Chưa sửa: WER", "Nhận gợi ý đầu: WER / câu đúng", "Chọn đúng: WER / câu đúng", "Từ sai: top-1 / top-3",
       "Chạm mỗi câu"],
      [["ViLexNorm test", "18,4%", "3,5% / 73,3%", "2,4% / 88,0%", "90,1% / 96,6%", "1,7"],
       ["Bỏ hết dấu", "74,9%", "14,0% / 31,7%", "3,6% / 71,0%", "84,0% / 95,1%", "8,2"],
       ["Gõ nhanh", "77,2%", "20,4% / 13,3%", "9,6% / 35,0%", "76,1% / 87,7%", "7,7"]],
      [1.7, 1.3, 2, 1.8, 1.8, 1.1], ["left", "center", "center", "center", "center", "center"])
    P("Về tốc độ, tầng từ điển có p95 dưới 0,5 ms (mục tiêu 20 ms), tầng ViT5 có p50 khoảng 60–92 ms và p95 khoảng 76–121 ms "
      "tùy lần đo (mục tiêu 500 ms). Trên giao diện thật, lần chấm đầu tiên sau khi nạp mô hình mất 640–720 ms, các lần sau "
      "65–211 ms. Với tin nhắn bình thường, đáp án nằm trong 3 gợi ý ở 96,6% từ sai và chỉ cần khoảng 2 lần chạm mỗi câu; với "
      "câu bỏ hết dấu hoặc gõ nhanh, cần khoảng 8 lần chạm.")
    H3("Các lỗi và cách xử lý")
    P("**Lỗi kỹ thuật trong quá trình xây dựng.** Các lỗi chính đã gặp và cách xử lý được tổng hợp ở Bảng «T:loi-ky-thuat».")
    T("loi-ky-thuat", "Các lỗi kỹ thuật đã gặp và cách xử lý",
      ["Lỗi", "Nguyên nhân", "Cách xử lý"],
      [["Transformers 5 lỗi khi chuyển tokenizer T5", "Thay đổi trong phiên bản mới", "Nạp trực tiếp tệp tokenizer.json"],
       ["6,6% câu chuẩn không tái tạo được", "Ký tự ngoài từ vựng thành <unk>", "Khôi phục ký tự từ câu nguồn theo vị trí"],
       ["Rò rỉ test qua VEC", "VEC chứa 83% ViLexNorm", "Bỏ 8.665 dòng trùng; kiểm tra chéo tự động"],
       ["Mô hình v2 sửa quá hăng", "Lỗi nhân tạo từ đúng → từ đúng khác", "Huấn luyện giai đoạn 2 chỉ trên dữ liệu thật"],
       ["Bảng từ điển thiếu phép sửa liền nhau (*ko di* → *không đi*)", "Chỉ ghép phép thay 1 từ", "Ghép từng cặp khi số từ bằng nhau"],
       ["Gõ nhanh làm mất gợi ý của từ đã khóa", "Từ khóa không còn được gạch chân", "Khóa chỉ dừng xếp lại, vẫn cho chọn"],
       ["Hết bộ nhớ GPU khi chấm nhiều câu", "Lô chấm quá lớn", "Giảm kích thước lô, GPU chạy một việc một lúc"]],
      [3, 2.8, 3.2])
    P("**Lỗi còn lại của mô hình.** Phân tích thủ công 20 lỗi tiêu biểu (chi tiết ở Phụ lục B) cho thấy các nhóm: viết tắt mơ "
      "hồ (4 ví dụ, *m* = mình/mày, *c* = chị/cậu), sửa thành từ có thật nhưng sai (4), sửa quá tay (4, như *ruby* → *rực rỡ*), "
      "mất/đổi nội dung (3), bỏ sót lỗi thành từ có thật (2) và lỗi nhãn của dữ liệu (3). Lỗi còn lại chủ yếu cần ngữ cảnh hội "
      "thoại hoặc kiến thức thế giới; lỗi nguy hiểm nhất là đổi nội dung, là lý do hệ thống luôn để người dùng chọn.")

    H2("Đánh giá kết quả")
    T("doi-chieu", "Đối chiếu kết quả với mục tiêu ban đầu",
      ["Mục tiêu", "Kết quả", "Đánh giá"],
      [["Mô hình sửa lỗi có kết quả trên test", "3 tập test + stress test 8 kiểu lỗi, top-1/top-3", "Đạt"],
       ["Mô hình diễn đạt lại từ ViSP", "Có, kèm bộ lọc giữ nghĩa", "Đạt một phần (35% gợi ý đầu đạt)"],
       ["Pipeline hai bước chạy trên đầu vào mới", "Có; RQ3 xác nhận sửa lỗi trước tốt hơn", "Đạt"],
       ["So sánh mốc, chỉ số phù hợp", "Mốc chép đầu vào, mô hình có sẵn, F0.5, sửa quá tay, iBLEU", "Đạt"],
       ["Phân tích 10–20 lỗi tiêu biểu", "20 lỗi có phân loại", "Đạt"],
       ["Demo", "Gợi ý khi gõ, hai chế độ, sửa và diễn đạt khi gửi", "Đạt, vượt kế hoạch"],
       ["Tốc độ gợi ý khi gõ", "Từ điển < 0,5 ms; ViT5 p95 ≤ 121 ms", "Đạt"]],
      [3.2, 4, 2])
    P("**Trả lời các câu hỏi nghiên cứu.** *RQ1:* mô hình ViT5 tinh chỉnh giảm khoảng 4/5 số từ sai trên tin nhắn thật so với "
      "mốc, vượt xa mô hình có sẵn; dữ liệu lỗi nhân tạo cùng huấn luyện hai giai đoạn giúp sửa lỗi gõ nhanh mà không làm tệ "
      "tin nhắn thật. *RQ2:* mô hình diễn đạt lại chỉ đạt 35% gợi ý đầu theo người chấm, và chỉ số tự động (embedding, NLI) "
      "đánh giá quá cao khoảng 2,5 lần, nên không thể kết luận về diễn đạt lại chỉ bằng chỉ số tự động. *RQ3:* sửa lỗi trước "
      "tốt hơn hẳn ở mọi kiểu lỗi; với câu không dấu hoặc gõ nhanh, diễn đạt thẳng gần như không cho gợi ý dùng được (1–2%).")
    P("**Điểm mạnh** của đồ án là quy trình đánh giá chặt (chống rò rỉ, mốc so sánh, điều kiện giữ đặt trước, chấm thủ công) "
      "và hệ thống chạy hoàn toàn trên máy cá nhân với tốc độ đáp ứng gợi ý khi gõ. **Điểm yếu** là chất lượng diễn đạt lại "
      "trên tin nhắn còn thấp, câu bỏ hết dấu vẫn cần nhiều lần chạm, và đánh giá thủ công chỉ có một người chấm.")

    H2("Tổng kết chương")
    P("Chương 4 đã trình bày môi trường triển khai và ước tính tài nguyên, quá trình hiện thực từng thành phần, ứng dụng hoàn "
      "chỉnh với hai chế độ, kế hoạch và kết quả kiểm thử ở năm mức. Kết quả cho thấy mô hình sửa lỗi đạt mục tiêu trên tin "
      "nhắn thật, gợi ý khi gõ đủ nhanh, còn diễn đạt lại là phần cần cải thiện nhất; các thử nghiệm kết hợp từ điển cho kết "
      "quả âm nhưng chỉ ra rõ nguyên nhân.")


def chapter5():
    H1("KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN")
    H2("Kết luận")
    P("Đồ án đã xây dựng hoàn chỉnh hệ thống sửa lỗi tin nhắn tiếng Việt chạy trên máy cá nhân với GPU 6 GB. Mô hình sửa lỗi "
      "ViT5-base tinh chỉnh hai giai đoạn giảm WER trên tin nhắn thật (ViLexNorm) từ 16,9% xuống 3,74%, sửa đúng hoàn toàn "
      "68,4% câu (76,5% khi cho chọn trong 3 phương án), và vượt xa mô hình có sẵn. Ứng dụng gợi ý cả câu ngay khi gõ, tách "
      "theo từng câu, có chế độ tin nhắn và chế độ văn bản; đáp án đúng nằm trong 3 gợi ý ở 96,6% từ sai với độ trễ dưới "
      "150 ms.")
    P("**Đóng góp chính:** (1) quy trình dữ liệu chống rò rỉ, phát hiện VEC chứa 83% ViLexNorm và ViSP là các cụm câu chứ không "
      "phải cặp độc lập; (2) cách kết hợp lỗi nhân tạo với huấn luyện hai giai đoạn để cải thiện lỗi gõ mà không làm tệ dữ "
      "liệu thật; (3) bằng chứng định lượng rằng BLEU thưởng việc chép câu gốc và chỉ số embedding/NLI đánh giá quá cao diễn "
      "đạt lại khoảng 2,5 lần so với người chấm; (4) cơ chế gợi ý khi gõ “từ điển đề xuất, mô hình chọn, người dùng quyết "
      "định” cho tiếng Việt.")
    P("**Hạn chế:** câu diễn đạt lại còn hay lạc ý vì không có dữ liệu diễn đạt lại theo văn phong tin nhắn; viết tắt một chữ "
      "cái và lỗi thành từ có thật vẫn khó; dữ liệu lỗi nhân tạo có thể dễ hơn lỗi gõ thật; ViLexNorm là bình luận công khai, "
      "chưa hoàn toàn giống tin nhắn riêng tư; đánh giá thủ công chỉ có một người chấm trên 40 tin nhắn; gợi ý khi gõ mới thử "
      "bằng giả lập, chưa thử với nhiều người dùng thật.")

    H2("Tác động tích cực và tiêu cực của hệ thống")
    P("**Tích cực.** Ở phạm vi địa phương, hệ thống giúp người Việt viết tin nhắn rõ ràng, đúng chính tả khi giao tiếp với thầy "
      "cô, đồng nghiệp hay khách hàng, hỗ trợ người lớn tuổi hoặc người không quen gõ dấu, và có thể tích hợp vào phần mềm soạn "
      "văn bản. Vì chạy hoàn toàn trên máy, tin nhắn riêng tư không bị gửi ra ngoài. Ở phạm vi toàn cầu, đồ án góp thêm công "
      "cụ, kết quả đánh giá và mã nguồn mở cho một ngôn ngữ ít tài nguyên hơn tiếng Anh, đồng thời chỉ ra những cạm bẫy đánh "
      "giá (rò rỉ dữ liệu giữa các bộ dữ liệu, chỉ số tự động cho diễn đạt lại) có giá trị cho các ngôn ngữ khác.")
    P("**Tiêu cực và cách giảm thiểu.** Hệ thống có thể đổi ý người viết (ví dụ đổi đại từ *mình* thành *mày*, thêm quan hệ "
      "nguyên nhân khi diễn đạt), gây hiểu lầm; vì vậy mọi thay đổi chỉ là gợi ý để người dùng chọn. Mô hình có thể mang thiên "
      "lệch của dữ liệu (văn phong trang trọng của ViSP, từ ngữ thô tục trong bình luận mạng xã hội) và có thể chuẩn hóa mất "
      "nét riêng của tiếng lóng, phương ngữ. Sự phụ thuộc vào công cụ sửa lỗi có thể làm giảm thói quen tự kiểm tra chính tả. "
      "Về pháp lý, dữ liệu ViLexNorm chỉ được dùng cho nghiên cứu, nên hệ thống hiện tại không thể thương mại hóa nếu chưa thay "
      "dữ liệu. Về môi trường, huấn luyện tiêu tốn điện năng GPU, nhưng đồ án chỉ tinh chỉnh mô hình cỡ vừa trong tổng cộng "
      "khoảng bốn giờ thay vì huấn luyện từ đầu.")

    H2("Hướng phát triển")
    B(["Xây dựng dữ liệu diễn đạt lại theo văn phong tin nhắn (sinh bằng mô hình lớn rồi duyệt thủ công) để cải thiện bước "
       "diễn đạt; thử phát hiện đảo vai trong câu gợi ý.",
       "Bộ chia đường học từ dữ liệu (dự đoán khi nào nên tin từ điển), hoặc sinh ứng viên tốt hơn cho lỗi gõ trong câu có dấu.",
       "Gợi ý theo từng ký tự (hoàn thành từ), xử lý lỗi đảo chữ chồng Telex (*cnof* → *còn*), học thói quen viết tắt riêng "
       "của từng người dùng và dùng ngữ cảnh các tin nhắn trước.",
       "Thử mô hình mức ký tự (ByT5) và mô hình nhẹ hơn để chạy trên điện thoại; đóng gói thành bàn phím hoặc phần mở rộng "
       "cho trình duyệt và phần mềm soạn thảo.",
       "Bộ test lỗi tự nhiên do nhiều người gõ thật và đánh giá với nhiều người chấm để đo độ đồng thuận."])


# ============================================================== phần cuối
def back_matter(refs_xml: str) -> str:
    out = [heading(1, "TÀI LIỆU THAM KHẢO", numbered=False), refs_xml, heading(1, "PHỤ LỤC", numbered=False)]
    out.append(para("**Phụ lục A. Lệnh tái lập kết quả** (chạy ở thư mục gốc kho mã, dùng Python của môi trường ảo):",
                    keep_next=True))
    out.append(bullets([
        "Dữ liệu: `python -m src.data.download_data`; `python -m src.data.preprocess_vsec --all`; `python -m src.data.preprocess_visp`; "
        "`python -m src.data.split_data`; `python -m src.data.build_correction_mix`; `python -m src.data.augment_errors`.",
        "Huấn luyện: `python -m src.correction.train`; `python -m src.correction.train --config configs/correction_stage2.yaml`; "
        "`python -m src.paraphrase.train`.",
        "Đánh giá: `python -m src.correction.evaluate`; `python -m src.correction.stress_test`; `python -m src.pipeline.rq3`; "
        "`python -m src.pipeline.manual_eval score`; `python -m src.lexicon.evaluate_hybrid tune|route|test`; "
        "`python -m src.realtime.simulate --n 300`.",
        "Kiểm thử tự động: `python -m pytest -q` (127 bài). Ứng dụng: `python -m app.realtime.server` → http://localhost:8765.",
        "Mã nguồn: https://github.com/EDinhquocbao/vietnamese-message-assistant"]))
    out.append(para("**Phụ lục B. Hai mươi lỗi tiêu biểu của mô hình sửa lỗi** (đoạn trích, phân loại thủ công):",
                    keep_next=True, before=240))
    rows = [
        ["Viết tắt mơ hồ", "…cho m rồi, m cũng k ăn…", "…cho mày…, mày cũng…", "…cho mình…, mình cũng…"],
        ["Viết tắt mơ hồ", "Việc c cần làm…", "Việc chị cần làm…", "Việc cậu cần làm…"],
        ["Viết tắt mơ hồ", "váy body k ck", "không chồng", "không chị"],
        ["Viết tắt mơ hồ", "thịt mỡ nk thay vì", "nữa", "nhưng"],
        ["Sửa thành từ có thật", "còn ít xịu à", "chịu", "xịt"],
        ["Sửa thành từ có thật", "Nước dăng xuyên màn hình", "đang", "văng"],
        ["Sửa thành từ có thật", "Còn dzú của tôi", "vợ", "vú"],
        ["Sửa thành từ có thật", "Luống thay thế…", "Lượng", "Luồng"],
        ["Sửa quá tay", "màu đỏ ruby", "rực rỡ", "ruby"],
        ["Sửa quá tay", "xe lớn lane xe máy", "lăn", "lane"],
        ["Sửa quá tay", "quá hời", "quá trời", "quá hời"],
        ["Sửa quá tay", "hê thống đơn giá", "hệ thống đơn giản", "hệ thống đơn giá"],
        ["Mất/đổi nội dung", "Kinh tế tuấn hoàn", "kiệt quệ", "tuần hoàn"],
        ["Mất/đổi nội dung", "tư duy tựu lực", "nỗ lực", "tự lực"],
        ["Mất/đổi nội dung", "mượn Mi nơ kh em", "Mixi", "Mi nơ"],
        ["Bỏ sót lỗi", "để gặt bỏ những thách thức", "gặt bỏ", "gạt bỏ"],
        ["Bỏ sót lỗi", "độ tuổi dạy thì", "dạy thì", "dậy thì"],
        ["Lỗi nhãn", "Chăc e nay sn 2005", "…sinh năm 2005", "…sinh năm 2006 (nhãn sai)"],
        ["Lỗi nhãn", "còn có 2tr thôi", "2 triệu", "2tr (nhãn bỏ sót)"],
        ["Lỗi nhãn", "tại Hà nội?", "Hà Nội", "Hà nội (nhãn bỏ sót)"],
    ]
    out.append(table(["Loại lỗi", "Đầu vào (trích)", "Mô hình sửa", "Nhãn"], rows, [2.2, 2.8, 2.2, 2.2]))
    out.append(para("**Phụ lục C. Cấu trúc mã nguồn chính:**", keep_next=True, before=240))
    out.append(table(["Thư mục / tệp", "Nội dung"], [
        ["configs/", "Cấu hình dữ liệu, huấn luyện, pipeline, từ điển"],
        ["src/data/", "Tải, làm sạch, chia tập, gộp tập, sinh lỗi nhân tạo"],
        ["src/correction/", "Huấn luyện, dự đoán (N-best, chấm câu), đánh giá, stress test"],
        ["src/paraphrase/", "Huấn luyện và sinh câu diễn đạt lại"],
        ["src/pipeline/", "Bộ lọc, xếp hạng, pipeline hai bước, RQ3, chấm thủ công"],
        ["src/lexicon/", "Từ điển, giải mã Telex/VNI, sinh ứng viên, các cách kết hợp"],
        ["src/realtime/", "Phiên gợi ý khi gõ, giả lập người dùng"],
        ["app/realtime/", "Máy chủ WebSocket và giao diện (chế độ tin nhắn, chế độ văn bản)"],
        ["app/streamlit_app.py", "Demo dự phòng bằng Streamlit"],
        ["tests/", "127 bài kiểm thử tự động"],
        ["reports/", "Hình, bảng, script dựng báo cáo"]], [3, 6]))
    return "".join(out)
