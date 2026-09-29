"""Materi Minna no Nihongo 1 — Bab 1 (perkenalan diri, kopula です).

Berdasarkan kurikulum standar Minna no Nihongo Bab 1 yang mencakup pola
N は N です / じゃありません / ですか, partikel も, dan の kepemilikan.
Struktur DSL identik dengan bab02_09.py agar bisa dimuat oleh loader yang sama.
"""

from seed_data.dsl import BUNPO, CHAPTER, KAIWA, KANJI, KOTOBA, QB, QB_ID, QS


BAB1 = CHAPTER(
    1, "わたし は マイクです。", "Saya Mike.",
    bunpo=[
        BUNPO(
            "b1-1", "N1 は N2 です — Kopula Afirmatif",
            "[N1] は [N2] です",
            [
                "は = [Partikel] penanda topik (dibaca 'wa')",
                "です = kopula, setara 'adalah'",
                "urutan: TOPIK dulu, baru info",
            ],
            "Pola paling dasar Bahasa Jepang. は menandai topik kalimat dan dibaca 'wa'. "
            "です di akhir berfungsi seperti 'adalah' dalam Bahasa Indonesia, tetapi wajib "
            "hadir walaupun kalimatnya sangat pendek. Nada です sopan; teman akrab bisa "
            "menghilangkannya, tapi untuk pembelajar pemula gunakan です dulu.",
            [
                ("わたし は マイク です。", "Saya Mike."),
                ("ミラーさん は アメリカ人|じん です。", "Pak Miller orang Amerika."),
                ("わたし は 学生|がくせい です。", "Saya mahasiswa."),
            ],
        ),
        BUNPO(
            "b1-2", "N1 は N2 じゃありません — Kopula Negatif",
            "[N1] は [N2] じゃありません",
            [
                "じゃありません = bentuk negatif santai",
                "ではありません = bentuk negatif formal (tulis)",
                "pengucapan じゃ = ringkasan では",
            ],
            "Untuk menyatakan 'bukan', ganti です menjadi じゃありません. Dalam tulisan resmi "
            "atau saat menulis surat, gunakan ではありません. Kedua bentuk sama artinya, "
            "hanya berbeda tingkat formalitas.",
            [
                ("わたし は 先生|せんせい じゃありません。", "Saya bukan guru."),
                ("サントスさん は 学生|がくせい じゃありません。", "Pak Santos bukan mahasiswa."),
                ("あの 人|ひと は 医者|いしゃ ではありません。", "Orang itu bukan dokter."),
            ],
        ),
        BUNPO(
            "b1-3", "N1 は N2 ですか — Kalimat Tanya",
            "[N1] は [N2] ですか",
            [
                "か = [Partikel] tanda tanya, letakkan di akhir",
                "はい／いいえ untuk menjawab",
                "intonasi naik pada か",
            ],
            "Menambahkan か di akhir kalimat pernyataan mengubahnya menjadi pertanyaan. "
            "Bahasa Jepang tidak memakai tanda tanya '?' dalam tulisan formal karena か sudah "
            "menandakannya, tetapi dalam tulisan santai kadang tetap ditulis '?'.",
            [
                ("ミラーさん は 会社員|かいしゃいん ですか。", "Apakah Pak Miller karyawan?"),
                ("はい、 会社員|かいしゃいん です。", "Ya, dia karyawan."),
                ("いいえ、 会社員|かいしゃいん じゃありません。", "Bukan, dia bukan karyawan."),
            ],
        ),
        BUNPO(
            "b1-4", "N1 も N2 です — 'Juga'",
            "[N1] も [N2] です",
            [
                "も menggantikan は saat info sama seperti sebelumnya",
                "も = 'juga'",
                "hanya bisa dipakai bila predikat identik",
            ],
            "Partikel も dipakai ketika subjek baru memiliki predikat yang sama dengan "
            "kalimat sebelumnya. Jangan pakai も bila predikatnya berbeda—kembali ke は.",
            [
                ("ミラーさん は 会社員|かいしゃいん です。", "Pak Miller karyawan."),
                ("グプタさん も 会社員|かいしゃいん です。", "Pak Gupta juga karyawan."),
                ("わたし も 日本人|にほんじん じゃありません。", "Saya juga bukan orang Jepang."),
            ],
        ),
        BUNPO(
            "b1-5", "N1 の N2 — Kepemilikan / Afiliasi",
            "[N1] の [N2]",
            [
                "の = [Partikel] penghubung milik/afiliasi",
                "arah: pemilik + の + benda/instansi",
                "IMC の 社員|しゃいん = karyawan IMC",
            ],
            "Partikel の menghubungkan dua kata benda dengan hubungan milik, asal, atau "
            "afiliasi. Pemilik/instansi induk ditulis LEBIH DAHULU, lalu の, lalu benda/orang. "
            "Berbeda dengan Bahasa Indonesia yang urutannya kebalikan ('buku saya' → わたし の 本).",
            [
                ("わたし は IMC の 社員|しゃいん です。", "Saya karyawan IMC."),
                ("マイクさん は さくら 大学|だいがく の 先生|せんせい です。", "Mike guru Universitas Sakura."),
                ("この 本|ほん は わたし の です。", "Buku ini milik saya."),
            ],
        ),
    ],
    kotoba=[
        KOTOBA("k1-1", "わたし", "わたし", "watashi", "saya", "Kata Ganti",
               ("わたし は マイク です。", "Saya Mike.")),
        KOTOBA("k1-2", "わたしたち", "わたしたち", "watashitachi", "kami; kita", "Kata Ganti",
               ("わたしたち は 学生|がくせい です。", "Kami mahasiswa.")),
        KOTOBA("k1-3", "あなた", "あなた", "anata", "Anda", "Kata Ganti",
               ("あなた は 先生|せんせい ですか。", "Apakah Anda guru?")),
        KOTOBA("k1-4", "あの 人|ひと", "あのひと", "ano hito", "orang itu (jauh)", "Kata Ganti",
               ("あの 人|ひと は だれ ですか。", "Siapa orang itu?"),
               display="あの 人|ひと"),
        KOTOBA("k1-5", "~さん", "さん", "-san", "Tuan/Nyonya (netral)", "Sufiks",
               ("ミラー さん は アメリカ人|じん です。", "Pak Miller orang Amerika.")),
        KOTOBA("k1-6", "~ちゃん", "ちゃん", "-chan", "sufiks akrab (anak/teman dekat)", "Sufiks",
               ("あきこ ちゃん は 学生|がくせい です。", "Akiko mahasiswa.")),
        KOTOBA("k1-7", "先生|せんせい", "せんせい", "sensei", "guru; dosen", "Kata Benda",
               ("わたし の 先生|せんせい は 田中|たなか さん です。", "Guru saya Pak Tanaka.")),
        KOTOBA("k1-8", "学生|がくせい", "がくせい", "gakusei", "mahasiswa; pelajar", "Kata Benda",
               ("わたし は 学生|がくせい です。", "Saya mahasiswa.")),
        KOTOBA("k1-9", "会社員|かいしゃいん", "かいしゃいん", "kaishain", "karyawan perusahaan", "Kata Benda",
               ("ミラー さん は 会社員|かいしゃいん です。", "Pak Miller karyawan.")),
        KOTOBA("k1-10", "銀行員|ぎんこういん", "ぎんこういん", "ginkouin", "pegawai bank", "Kata Benda",
               ("グプタ さん は 銀行員|ぎんこういん です。", "Pak Gupta pegawai bank.")),
        KOTOBA("k1-11", "医者|いしゃ", "いしゃ", "isha", "dokter", "Kata Benda",
               ("わたし の 父|ちち は 医者|いしゃ です。", "Ayah saya dokter.")),
        KOTOBA("k1-12", "研究者|けんきゅうしゃ", "けんきゅうしゃ", "kenkyuusha", "peneliti", "Kata Benda",
               ("あの 人|ひと は 研究者|けんきゅうしゃ です。", "Orang itu peneliti.")),
        KOTOBA("k1-13", "エンジニア", "エンジニア", "enjinia", "insinyur; engineer", "Kata Benda",
               ("わたし は エンジニア です。", "Saya insinyur.")),
        KOTOBA("k1-14", "大学|だいがく", "だいがく", "daigaku", "universitas", "Kata Benda",
               ("さくら 大学|だいがく の 先生|せんせい です。", "Guru Universitas Sakura.")),
        KOTOBA("k1-15", "だれ", "だれ", "dare", "siapa (netral)", "Kata Tanya",
               ("あの 人|ひと は だれ ですか。", "Siapa orang itu?")),
        KOTOBA("k1-16", "どなた", "どなた", "donata", "siapa (sopan)", "Kata Tanya",
               ("あの かた は どなた ですか。", "Beliau siapa?")),
        KOTOBA("k1-17", "~歳|さい", "さい", "-sai", "…tahun (umur)", "Sufiks",
               ("わたし は 25 歳|さい です。", "Saya berusia 25 tahun.")),
        KOTOBA("k1-18", "はい", "はい", "hai", "ya", "Kata Seru",
               ("はい、 そう です。", "Ya, benar.")),
        KOTOBA("k1-19", "いいえ", "いいえ", "iie", "tidak; bukan", "Kata Seru",
               ("いいえ、 ちがいます。", "Bukan, salah.")),
        KOTOBA("k1-20", "はじめまして", "はじめまして", "hajimemashite", "salam kenal", "Ungkapan",
               ("はじめまして。 マイク です。", "Salam kenal. Saya Mike.")),
    ],
    kanji=[
        KANJI(
            "j1-1", "私", "シ", "わたし", "saya", 7,
            [
                ("私", "わたし", "saya"),
                ("私立|しりつ", "しりつ", "swasta (institusi)"),
            ],
        ),
        KANJI(
            "j1-2", "人", "ジン・ニン", "ひと", "orang", 2,
            [
                ("人", "ひと", "orang"),
                ("日本人", "にほんじん", "orang Jepang"),
                ("三人", "さんにん", "tiga orang"),
            ],
        ),
        KANJI(
            "j1-3", "学", "ガク", "まな(ぶ)", "belajar; ilmu", 8,
            [
                ("学生", "がくせい", "mahasiswa"),
                ("大学", "だいがく", "universitas"),
                ("学ぶ", "まなぶ", "belajar"),
            ],
        ),
        KANJI(
            "j1-4", "生", "セイ・ショウ", "い(きる)・う(まれる)", "hidup; lahir", 5,
            [
                ("学生", "がくせい", "mahasiswa"),
                ("先生", "せんせい", "guru"),
                ("生まれる", "うまれる", "lahir"),
            ],
        ),
        KANJI(
            "j1-5", "先", "セン", "さき", "sebelumnya; ujung", 6,
            [
                ("先生", "せんせい", "guru"),
                ("先週", "せんしゅう", "minggu lalu"),
                ("先|さきに", "さき", "duluan; sebelumnya"),
            ],
        ),
    ],
    kaiwa=KAIWA(
        "はじめまして",
        "Mike Miller pindah ke Jepang untuk bekerja di IMC. Ia bertemu Yamada dari IMC di kantornya.",
        [
            ("ミラー", "Miller", "はじめまして。 マイク・ミラー です。",
             "Salam kenal. Saya Mike Miller."),
            ("山田|やまだ", "Yamada", "はじめまして。 山田|やまだ 一郎|いちろう です。",
             "Salam kenal. Saya Ichiro Yamada."),
            ("ミラー", "Miller", "アメリカ から 来|き ました。 どうぞ よろしく お願|ねが いします。",
             "Saya dari Amerika. Mohon bantuannya."),
            ("山田|やまだ", "Yamada", "こちら こそ、 よろしく お願|ねが いします。",
             "Sama-sama, mohon bantuannya juga."),
            ("ミラー", "Miller", "山田|やまだ さん は 会社員|かいしゃいん ですか。",
             "Pak Yamada, apakah Anda karyawan?"),
            ("山田|やまだ", "Yamada", "はい、 IMC の 社員|しゃいん です。",
             "Ya, saya karyawan IMC."),
        ],
    ),
    quiz_bunpo=[
        QB(
            "qb1-1", "わたし ＿＿ マイク です。",
            ["を", "は", "が", "も"], 1,
            "わたし は マイク です。", "は",
            "[N1] は [N2] です",
            "Partikel penanda topik adalah は (dibaca 'wa'). を dipakai untuk objek, "
            "が untuk subjek fokus, も untuk 'juga'.",
        ),
        QB(
            "qb1-2", "サントスさん は 学生|がくせい ＿＿ 。",
            ["です", "じゃありません", "ですか", "と"], 1,
            "サントスさん は 学生|がくせい じゃありません。", "じゃありません",
            "[N1] は [N2] じゃありません",
            "Untuk menyatakan 'bukan', gunakan じゃありません (santai) atau ではありません "
            "(formal). です adalah bentuk afirmatif.",
        ),
        QB(
            "qb1-3", "ミラーさん は 会社員|かいしゃいん です。 グプタさん ＿＿ 会社員|かいしゃいん です。",
            ["は", "の", "も", "が"], 2,
            "グプタさん も 会社員|かいしゃいん です。", "も",
            "[N1] も [N2] です",
            "Ketika subjek berikutnya memiliki predikat SAMA seperti kalimat sebelumnya, "
            "pakai partikel も yang berarti 'juga'.",
        ),
        QB_ID(
            "qb1-4", "Manakah kalimat tanya yang BENAR untuk menanyakan pekerjaan Pak Miller?",
            ["ミラーさん が 会社員 です。",
             "ミラーさん は 会社員 ですか。",
             "ミラーさん の 会社員 ですか。",
             "ミラーさん を 会社員 です。"], 1,
            "ミラーさん は 会社員|かいしゃいん ですか。", "ですか",
            "[N1] は [N2] ですか",
            "Kalimat tanya dibentuk dengan menambahkan か di akhir kalimat pernyataan. "
            "Partikel topik tetap は.",
        ),
        QB(
            "qb1-5", "この 本|ほん は わたし ＿＿ です。",
            ["は", "の", "が", "も"], 1,
            "この 本|ほん は わたし の です。", "の",
            "[N] は [pemilik] の です",
            "の di akhir kalimat menggantikan kata benda yang sudah disebut (buku). "
            "Menyatakan 'milik saya' tanpa mengulang kata 本.",
        ),
    ],
    quiz_susun=[
        QS(
            "qs1-1", "Saya Mike Miller.",
            "わたし は マイク・ミラー です。",
            "が を の",
        ),
        QS(
            "qs1-2", "Pak Miller karyawan IMC.",
            "ミラーさん は IMC の 社員|しゃいん です。",
            "を も 学生|がくせい",
        ),
        QS(
            "qs1-3", "Saya bukan orang Jepang.",
            "わたし は 日本人|にほんじん じゃありません。",
            "を も です",
        ),
        QS(
            "qs1-4", "Pak Gupta juga karyawan.",
            "グプタさん も 会社員|かいしゃいん です。",
            "は を の",
        ),
    ],
)


CHAPTERS = [BAB1]
