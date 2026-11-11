"""Internationalization (i18n) dictionary and helpers for CetakKira.

Supports Malay ('ms') and English ('en') with functional translation helpers.
"""

from __future__ import annotations

from typing import Any

TRANSLATIONS: dict[str, dict[str, str]] = {
    "ms": {
        # App identity
        "app_name": "CetakKira",
        "brand_footer": "cetakkira",
        "app_tagline": "Lembaran Kerja Matematik Rendah Boleh Cetak",
        # Hero & Intro
        "hero_title": "Jana Lembaran Kerja Matematik A4 Boleh Cetak",
        "hero_subtitle": (
            "Percuma, mudah, dan sedia dicetak untuk murid Tahun 1 hingga 3. "
            "Latihan dijana segar setiap kali bersama skema jawapan lengkap."
        ),
        "presets_label": "Pilihan Pantas (Pratetap):",
        "preset_t1_badge": "Tahun 1",
        "preset_t2_badge": "Tahun 2",
        "preset_t3_badge": "Tahun 3",
        # Document header & footer labels
        "label_name": "Nama:",
        "label_date": "Tarikh:",
        "label_score": "Markah:",
        "label_instruction": "Arahan:",
        "page_format": "Halaman {current} / {total}",
        # Answer key
        "answer_key_title": "SKEMA JAWAPAN",
        "answer_key_instruction": "Semak jawapan anda dengan teliti.",
        "label_answer_target": "Untuk guru / ibu bapa",
        # Alt text for illustrations
        "alt_mascot": "Maskot CetakKira, kancil pintar memegang pensel dan lembaran kerja",
        "alt_topic_grid": "Ikon carta nombor 100",
        "alt_topic_count": "Ikon kira dan tulis objek",
        "alt_topic_add": "Ikon operasi tambah bentuk lazim",
        "alt_topic_sub": "Ikon operasi tolak bentuk lazim",
        "alt_topic_sifir_ref": "Ikon rujukan jadual sifir",
        "alt_topic_sifir": "Ikon latihan darab sifir",
        "alt_topic_div": "Ikon operasi bahagi bentuk lazim",
        # Topic: Grid (Carta Nombor 100)
        "topic_grid_name": "Carta Nombor 100",
        "grid_title": "CARTA NOMBOR 100",
        "grid_subtitle": "Isi Tempat Kosong ({start} hingga {end})",
        "grid_instruction": "Isi nombor yang tertinggal dalam petak mengikut urutan yang betul.",
        "grid_answer_subtitle": "Jawapan Carta Nombor ({start} hingga {end})",
        # Topic: Count (Kira dan Tulis)
        "topic_count_name": "Kira dan Tulis",
        "count_title": "KIRA DAN TULIS",
        "count_subtitle": "Bilang Objek dan Tulis Nombor (1 hingga {max})",
        "count_instruction": "Kira bilangan objek dalam setiap petak dan tulis jawapan yang betul.",
        "count_answer_subtitle": "Jawapan Kira dan Tulis (1 hingga {max})",
        # Topic: Addition (Operasi Tambah)
        "topic_add_name": "Operasi Tambah",
        "add_title": "LATIHAN TAMBAH",
        "add_subtitle_no_regroup": "Tambah Bentuk Lazim ({digits} Digit Tanpa Kumpul Semula)",
        "add_subtitle_regroup": "Tambah Bentuk Lazim ({digits} Digit Kumpul Semula)",
        "add_instruction": "Selesaikan operasi tambah berikut dalam bentuk lazim.",
        "add_answer_subtitle": "Jawapan Tambah ({digits} Digit)",
        # Topic: Subtraction (Operasi Tolak)
        "topic_sub_name": "Operasi Tolak",
        "sub_title": "LATIHAN TOLAK",
        "sub_subtitle_no_borrow": "Tolak Bentuk Lazim ({digits} Digit Tanpa Kumpul Semula)",
        "sub_subtitle_borrow": "Tolak Bentuk Lazim ({digits} Digit Kumpul Semula)",
        "sub_instruction": "Selesaikan operasi tolak berikut dalam bentuk lazim.",
        "sub_answer_subtitle": "Jawapan Tolak ({digits} Digit)",
        # Topic: Sifir Ref (Jadual Sifir)
        "topic_sifir_ref_name": "Jadual Sifir",
        "sifir_ref_title": "JADUAL SIFIR",
        "sifir_ref_subtitle": "Sifir {tables}",
        "sifir_ref_instruction": "Rujuk jadual sifir ini untuk membina kefahaman operasi darab.",
        "sifir_table_header": "SIFIR {table}",
        # Topic: Sifir Practice (Latihan Sifir)
        "topic_sifir_name": "Latihan Sifir",
        "sifir_title": "LATIHAN SIFIR",
        "sifir_subtitle": "Darab Bentuk Lazim (Sifir {tables})",
        "sifir_instruction": "Selesaikan operasi darab berikut dalam bentuk lazim.",
        "sifir_answer_subtitle": "Jawapan Sifir ({tables})",
        # Topic: Division
        "topic_div_name": "Operasi Bahagi",
        "div_title": "LATIHAN BAHAGI",
        "div_subtitle_exact": "Bahagi Tepat ({digits} Digit)",
        "div_subtitle_remainder": "Bahagi dengan Baki ({digits} Digit)",
        "div_instruction": "Bahagi dalam bentuk lazim. Tunjukkan langkah pengiraan dan baki.",
        "div_answer_subtitle": "Jawapan Bahagi ({digits} Digit)",
        "div_result": "{dividend} ÷ {divisor} = {quotient}, baki {remainder}",
        # Presets descriptions
        "preset_t1_desc": "Gaya Tahun 1: nombor hingga 100, tambah dan tolak tanpa kumpul semula",
        "preset_t2_desc": (
            "Gaya Tahun 2: nombor hingga 200, tambah dan tolak dengan kumpul semula, sifir 2, 3, 4,"
            " 5, 10"
        ),
        "preset_t3_desc": (
            "Gaya Tahun 3: tambah dan tolak 3 digit kumpul semula, sifir 6, 7, 8, 9, bahagi 2 digit"
            " tepat"
        ),
        # Form section titles & hints
        "section_topics": "1. Pilih Topik Latihan",
        "section_topics_hint": "Tandakan sekurang-kurangnya satu topik yang ingin dimuatkan.",
        "section_options": "2. Tetapan Terperinci Topik",
        "section_general": "3. Tetapan Lembaran & Halaman",
        # Form field labels & hints
        "label_grid_start": "Nombor Mula Carta:",
        "hint_grid_start": "Pilih julat 100 nombor (contohnya 1-100 atau 101-200).",
        "label_grid_blanks": "Bilangan Petak Kosong (15 - 60):",
        "hint_grid_blanks": "Berapa banyak petak yang perlu diisi murid.",
        "label_count_max": "Had Bilangan Objek (Maksimum):",
        "hint_count_max": "Maksimum objek dalam setiap petak.",
        "label_count_shapes": "Pilihan Bentuk Objek:",
        "shape_star": "Bintang",
        "shape_circle": "Bulatan",
        "shape_apple": "Epal",
        "shape_fish": "Ikan",
        "shape_flower": "Bunga",
        "label_add_digits": "Bilangan Digit Tambah:",
        "label_add_regroup": "Kumpul Semula (Tambah):",
        "opt_add_no_regroup": "0 — Tanpa kumpul semula",
        "opt_add_regroup": "1 — Perlu kumpul semula",
        "label_sub_digits": "Bilangan Digit Tolak:",
        "label_sub_borrow": "Kumpul Semula / Pinjam (Tolak):",
        "opt_sub_no_borrow": "0 — Tanpa pinjam",
        "opt_sub_borrow": "1 — Perlu pinjam (memerlukan 2 atau 3 digit)",
        "label_sifir_tables": "Pilihan Sifir:",
        "table_num": "Sifir {n}",
        "label_sifir_n": "Soalan Sifir Setiap Halaman:",
        "hint_sifir_n": "Antara 1 hingga 24 soalan.",
        "label_div_digits": "Bilangan Digit Dibahagi:",
        "label_div_divisors": "Pilihan Pembahagi (2 - 9):",
        "label_div_rem": "Baki Bahagi:",
        "opt_div_exact": "0 — Bahagi tepat (tiada baki)",
        "opt_div_rem": "1 — Mempunyai baki",
        "label_pages": "Jumlah Halaman Soalan (1 - 20):",
        "hint_pages": "Halaman latihan sahaja; skema jawapan ditambah berasingan.",
        "label_lang": "Bahasa Lembaran:",
        "lang_ms": "Bahasa Melayu",
        "lang_en": "English",
        "label_ans": "Skema Jawapan:",
        "opt_ans_yes": "Sertakan skema jawapan",
        "opt_ans_no": "Tanpa skema jawapan",
        "label_seed": "Nombor Benih (Seed):",
        "hint_seed": (
            "Nombor unik untuk menghasilkan soalan yang sama apabila dijana semula."
        ),
        "btn_new_seed": "Soalan Baharu",
        # Form buttons & feedback
        "btn_generate": "Jana PDF",
        "btn_generate_disclosure": "(buka dalam tab baharu)",
        "btn_share": "Salin Pautan",
        "share_copied": "Pautan disalin!",
        "share_fallback_label": "Salin pautan lembaran ini:",
        # Accessibility & errors
        "skip_to_content": "Langkau ke kandungan utama",
        "error_summary_title": "Sila perbetulkan ralat berikut:",
        "field_error_prefix": "Ralat: ",
        # Footer & disclaimer
        "disclaimer_curriculum": (
            "Bukan produk kurikulum rasmi. Soalan dijana secara dinamik dan "
            "diilhamkan daripada topik Tahun 1 hingga 3."
        ),
        "footer_source": "GitHub",
        "footer_rights": "Hak cipta terpelihara.",
        # Error pages
        "error_page_title": "Ralat {code}",
        "error_400_heading": "Permintaan Tidak Sah",
        "error_400_message": (
            "Permintaan tidak dapat diproses. Sila semak semula tetapan yang dipilih."
        ),
        "error_401_heading": "Log Masuk Diperlukan",
        "error_401_message": "Sila log masuk untuk meneruskan.",
        "error_403_heading": "Akses Ditolak",
        "error_403_message": "Anda tidak mempunyai kebenaran untuk mengakses halaman ini.",
        "error_404_heading": "Halaman Tidak Dijumpai",
        "error_404_message": "Halaman yang anda minta tidak wujud.",
        "error_429_heading": "Terlalu Banyak Permintaan",
        "error_429_message": (
            "Anda telah mencapai had jana PDF (30 seminit). Sila tunggu sebentar dan cuba lagi."
        ),
        "error_500_heading": "Ralat Pelayan",
        "error_500_message": "Sesuatu ralat tidak dijangka berlaku. Sila cuba sebentar lagi.",
        "error_502_heading": "Pintu Gerbang Tidak Sah",
        "error_502_message": "Respons tidak sah daripada pelayan hulu.",
        "error_503_heading": "Perkhidmatan Tidak Tersedia",
        "error_503_message": "Perkhidmatan sedang sibuk atau dalam penyelenggaraan.",
        "btn_go_home": "Kembali ke Laman Utama",
        # Spec validation error keys
        "error_repeated": "Parameter tidak boleh diulang.",
        "error_empty": "Nilai tidak boleh kosong.",
        "error_invalid_preset": "Pilihan pratetap tidak sah.",
        "error_empty_topic": "Nama topik tidak boleh kosong.",
        "error_unknown_topic": "Topik tidak dikenali.",
        "error_required": "Medan ini diperlukan.",
        "error_out_of_range": "Nilai di luar julat yang dibenarkan.",
        "error_invalid_integer": "Sila masukkan nombor bulat yang sah.",
        "error_invalid_choice": "Pilihan tidak sah.",
        "error_invalid_boolean": "Nilai boolean tidak sah (gunakan 0 atau 1).",
        "error_borrow_requires_two_digits": (
            "Operasi tolak dengan kumpul semula memerlukan sekurang-kurangnya 2 digit."
        ),
        "error_empty_tables": "Sila pilih sekurang-kurangnya satu sifir.",
        "error_empty_divisors": "Sila pilih sekurang-kurangnya satu pembahagi.",
        "error_empty_shapes": "Sila pilih sekurang-kurangnya satu bentuk.",
        "error_below_minimum": (
            "Jumlah halaman kurang daripada bilangan minimum yang diperlukan."
        ),
        "ref_pages_mismatch": (
            "Halaman mesti sama dengan bilangan helaian jadual sifir apabila hanya jadual dipilih."
        ),
        "error_ref_pages_mismatch": (
            "Halaman mesti sama dengan bilangan helaian jadual sifir apabila hanya jadual dipilih."
        ),
    },
    "en": {
        # App identity
        "app_name": "CetakKira",
        "brand_footer": "cetakkira",
        "app_tagline": "Printable Primary Math Worksheets",
        # Hero & Intro
        "hero_title": "Generate Printable A4 Math Worksheets",
        "hero_subtitle": (
            "Free, calm, and ready to print for Year 1 to 3 primary pupils. "
            "Generates fresh problems every time with matching answer keys."
        ),
        "presets_label": "Quick Presets:",
        "preset_t1_badge": "Year 1",
        "preset_t2_badge": "Year 2",
        "preset_t3_badge": "Year 3",
        # Document header & footer labels
        "label_name": "Name:",
        "label_date": "Date:",
        "label_score": "Score:",
        "label_instruction": "Instruction:",
        "page_format": "Page {current} of {total}",
        # Answer key
        "answer_key_title": "ANSWER KEY",
        "answer_key_instruction": "Check your answers carefully.",
        "label_answer_target": "For teachers and parents",
        # Alt text for illustrations
        "alt_mascot": "CetakKira mascot, a friendly mouse-deer holding a pencil and worksheet",
        "alt_topic_grid": "100-number grid icon",
        "alt_topic_count": "Count and write objects icon",
        "alt_topic_add": "Vertical addition icon",
        "alt_topic_sub": "Vertical subtraction icon",
        "alt_topic_sifir_ref": "Multiplication tables reference icon",
        "alt_topic_sifir": "Multiplication practice icon",
        "alt_topic_div": "Long division icon",
        # Topic: Grid (100-Number Grid)
        "topic_grid_name": "100-Number Grid",
        "grid_title": "100-NUMBER GRID",
        "grid_subtitle": "Fill in the Blanks ({start} to {end})",
        "grid_instruction": "Fill in the missing numbers in the grid in the correct order.",
        "grid_answer_subtitle": "Number Grid Answers ({start} to {end})",
        # Topic: Count (Count and Write)
        "topic_count_name": "Count and Write",
        "count_title": "COUNT AND WRITE",
        "count_subtitle": "Count the Objects and Write the Number (1 to {max})",
        "count_instruction": "Count the objects in each box and write the correct number.",
        "count_answer_subtitle": "Count and Write Answers (1 to {max})",
        # Topic: Addition (Vertical Addition)
        "topic_add_name": "Addition",
        "add_title": "ADDITION PRACTICE",
        "add_subtitle_no_regroup": "Vertical Addition ({digits}-Digit Without Regrouping)",
        "add_subtitle_regroup": "Vertical Addition ({digits}-Digit With Regrouping)",
        "add_instruction": "Solve the following addition problems in vertical form.",
        "add_answer_subtitle": "Addition Answers ({digits}-Digit)",
        # Topic: Subtraction (Vertical Subtraction)
        "topic_sub_name": "Subtraction",
        "sub_title": "SUBTRACTION PRACTICE",
        "sub_subtitle_no_borrow": "Vertical Subtraction ({digits}-Digit Without Regrouping)",
        "sub_subtitle_borrow": "Vertical Subtraction ({digits}-Digit With Regrouping)",
        "sub_instruction": "Solve the following subtraction problems in vertical form.",
        "sub_answer_subtitle": "Subtraction Answers ({digits}-Digit)",
        # Topic: Sifir Ref (Multiplication Tables)
        "topic_sifir_ref_name": "Multiplication Tables",
        "sifir_ref_title": "MULTIPLICATION TABLES",
        "sifir_ref_subtitle": "Tables {tables}",
        "sifir_ref_instruction": (
            "Use these multiplication tables as a reference to help you learn."
        ),
        "sifir_table_header": "TABLE {table}",
        # Topic: Sifir Practice (Multiplication Practice)
        "topic_sifir_name": "Multiplication Practice",
        "sifir_title": "MULTIPLICATION PRACTICE",
        "sifir_subtitle": "Vertical Multiplication (Tables {tables})",
        "sifir_instruction": "Solve the following multiplication problems in vertical form.",
        "sifir_answer_subtitle": "Multiplication Answers ({tables})",
        # Topic: Division
        "topic_div_name": "Division",
        "div_title": "DIVISION PRACTICE",
        "div_subtitle_exact": "Exact Division ({digits}-Digit)",
        "div_subtitle_remainder": "Division with Remainders ({digits}-Digit)",
        "div_instruction": "Use long division. Show your working and the remainder.",
        "div_answer_subtitle": "Division Answers ({digits}-Digit)",
        "div_result": "{dividend} ÷ {divisor} = {quotient}, remainder {remainder}",
        # Presets descriptions
        "preset_t1_desc": "Tahun 1 style: numbers to 100, add and subtract without regrouping",
        "preset_t2_desc": (
            "Tahun 2 style: numbers to 200, add and subtract with regrouping, tables 2, 3, 4, 5, 10"
        ),
        "preset_t3_desc": (
            "Tahun 3 style: 3-digit add and subtract with regrouping, tables 6, 7, 8, 9, exact"
            " 2-digit division"
        ),
        # Form section titles & hints
        "section_topics": "1. Choose Practice Topics",
        "section_topics_hint": "Check at least one topic to include in the worksheet.",
        "section_options": "2. Topic Options & Difficulty",
        "section_general": "3. Worksheet & Page Settings",
        # Form field labels & hints
        "label_grid_start": "Grid Start Number:",
        "hint_grid_start": "Select the 100-number range (e.g. 1-100 or 101-200).",
        "label_grid_blanks": "Blank Cells (15 - 60):",
        "hint_grid_blanks": "Number of blank squares the pupil fills in.",
        "label_count_max": "Maximum Object Count:",
        "hint_count_max": "Maximum number of items per box.",
        "label_count_shapes": "Object Shapes:",
        "shape_star": "Star",
        "shape_circle": "Circle",
        "shape_apple": "Apple",
        "shape_fish": "Fish",
        "shape_flower": "Flower",
        "label_add_digits": "Addition Digits:",
        "label_add_regroup": "Addition Regrouping (Carry):",
        "opt_add_no_regroup": "0 — Without regrouping",
        "opt_add_regroup": "1 — Regrouping required",
        "label_sub_digits": "Subtraction Digits:",
        "label_sub_borrow": "Subtraction Borrowing:",
        "opt_sub_no_borrow": "0 — Without borrowing",
        "opt_sub_borrow": "1 — Borrowing required (requires 2 or 3 digits)",
        "label_sifir_tables": "Multiplication Tables:",
        "table_num": "Table {n}",
        "label_sifir_n": "Questions Per Page:",
        "hint_sifir_n": "Between 1 and 24 questions.",
        "label_div_digits": "Dividend Digits:",
        "label_div_divisors": "Divisors (2 - 9):",
        "label_div_rem": "Division Remainder:",
        "opt_div_exact": "0 — Exact division (no remainder)",
        "opt_div_rem": "1 — With remainder",
        "label_pages": "Content Pages (1 - 20):",
        "hint_pages": "Practice pages only; answer key pages are appended.",
        "label_lang": "Worksheet Language:",
        "lang_ms": "Bahasa Melayu",
        "lang_en": "English",
        "label_ans": "Answer Key:",
        "opt_ans_yes": "Include answer key sheets",
        "opt_ans_no": "Without answer key sheets",
        "label_seed": "Random Seed:",
        "hint_seed": (
            "A unique integer that reproduces the exact same worksheet when shared."
        ),
        "btn_new_seed": "New Questions",
        # Form buttons & feedback
        "btn_generate": "Generate PDF",
        "btn_generate_disclosure": "(opens in a new tab)",
        "btn_share": "Copy Share Link",
        "share_copied": "Link copied!",
        "share_fallback_label": "Copy this worksheet link:",
        # Accessibility & errors
        "skip_to_content": "Skip to main content",
        "error_summary_title": "Please fix the following errors:",
        "field_error_prefix": "Error: ",
        # Footer & disclaimer
        "disclaimer_curriculum": (
            "Not an official curriculum product. Questions are dynamically generated "
            "inspired by Year 1 to 3 primary math topics."
        ),
        "footer_source": "GitHub",
        "footer_rights": "All rights reserved.",
        # Error pages
        "error_page_title": "Error {code}",
        "error_400_heading": "Bad Request",
        "error_400_message": (
            "The request could not be understood. Please verify your selected settings."
        ),
        "error_401_heading": "Sign In Required",
        "error_401_message": "Please sign in to continue.",
        "error_403_heading": "Access Forbidden",
        "error_403_message": "You do not have permission to access this page.",
        "error_404_heading": "Page Not Found",
        "error_404_message": "The page you requested does not exist.",
        "error_429_heading": "Too Many Requests",
        "error_429_message": (
            "You have reached the PDF generation limit (30 per minute). "
            "Please slow down and try again shortly."
        ),
        "error_500_heading": "Internal Server Error",
        "error_500_message": "An unexpected error occurred on our end. Please try again shortly.",
        "error_502_heading": "Bad Gateway",
        "error_502_message": "Invalid upstream response.",
        "error_503_heading": "Service Unavailable",
        "error_503_message": "The service is temporarily unavailable. Please try again shortly.",
        "btn_go_home": "Back to Home",
        # Spec validation error keys
        "error_repeated": "Parameter cannot be repeated.",
        "error_empty": "Value cannot be empty.",
        "error_invalid_preset": "Invalid preset option.",
        "error_empty_topic": "Topic name cannot be empty.",
        "error_unknown_topic": "Unknown topic.",
        "error_required": "This field is required.",
        "error_out_of_range": "Value is out of the allowed range.",
        "error_invalid_integer": "Please enter a valid integer.",
        "error_invalid_choice": "Invalid choice.",
        "error_invalid_boolean": "Invalid boolean value (use 0 or 1).",
        "error_borrow_requires_two_digits": (
            "Subtraction with regrouping requires at least 2 digits."
        ),
        "error_empty_tables": "Please select at least one multiplication table.",
        "error_empty_divisors": "Please select at least one divisor.",
        "error_empty_shapes": "Please select at least one shape.",
        "error_below_minimum": "Page count is less than the minimum required.",
        "ref_pages_mismatch": (
            "Pages must equal the number of sifir table sheets when only tables are selected."
        ),
        "error_ref_pages_mismatch": (
            "Pages must equal the number of sifir table sheets when only tables are selected."
        ),
    },
}


def t(key: str, lang: str = "ms", **kwargs: Any) -> str:
    """Translate a message key to the specified language with optional format variables."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["ms"])
    text = lang_dict.get(key)
    if text is None:
        text = TRANSLATIONS["ms"].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


def get_error_message(message_key: str, lang: str = "ms") -> str:
    """Translate a spec validation error message key."""
    lookup_key = f"error_{message_key}"
    return t(lookup_key, lang=lang)
