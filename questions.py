"""Isi kuesioner kompetensi: pertanyaan, panduan, kata kunci, dan rubrik."""

KOMPETENSI = [
    {
        "kode": "A",
        "nama": "Komunikasi Efektif",
       # "definisi": (
         #   "Kemampuan menyampaikan ide secara jelas, mendengarkan aktif, dan "
         #   "menyesuaikan cara komunikasi dengan lawan bicara agar pesan dipahami "
           # "dan ditindaklanjuti."
      #  ),
        "pertanyaan": (
            "Ceritakan pengalaman ketika Anda harus menjelaskan hal yang rumit atau "
            "penting kepada orang yang memiliki latar belakang atau pandangan berbeda "
            "dengan Anda."
        ),
        "panduan": [
            "Apa situasinya dan siapa lawan bicara Anda?",
            "Bagaimana Anda menyesuaikan cara penyampaian agar mudah dipahami?",
            "Bagaimana Anda memastikan pesan Anda benar-benar dipahami dan diterima?",
        ],
        "kata_kunci": [
            "menjelaskan", "menyampaikan", "mendengarkan", "memahami", "dipahami",
            "bahasa", "contoh", "analogi", "diskusi", "bertanya", "pertanyaan",
            "umpan balik", "feedback", "presentasi", "meyakinkan", "sederhana",
            "menyesuaikan", "klarifikasi", "konfirmasi", "sudut pandang", "visual",
            "gambar", "diagram", "rapat", "dialog", "empati",
        ],
    },
    {
        "kode": "B",
        "nama": "Integritas & Etika Kerja",
       # "definisi": (
        #    "Konsistensi antara ucapan dan tindakan, kejujuran, kepatuhan pada aturan "
          #  "dan nilai organisasi, serta tanggung jawab atas tindakan sendiri, termasuk "
          #  "ketika tidak ada yang mengawasi."
      #  ),
        "pertanyaan": (
            "Ceritakan situasi ketika Anda diminta atau tergoda melakukan sesuatu yang "
            "bertentangan dengan aturan atau nilai-nilai Anda."
        ),
        "panduan": [
            "Apa situasinya dan apa yang membuat Anda tergoda atau tertekan?",
            "Apa keputusan yang Anda ambil, dan apa risikonya bagi Anda?",
            "Bagaimana dampak keputusan tersebut terhadap pekerjaan dan hubungan Anda "
            "dengan orang lain?",
        ],
        "kata_kunci": [
            "jujur", "kejujuran", "menolak", "aturan", "prosedur", "sop", "etika",
            "nilai", "melapor", "melaporkan", "transparan", "terbuka", "tanggung jawab",
            "risiko", "integritas", "kode etik", "benar", "konsekuensi", "rahasia",
            "kepatuhan", "atasan", "tegas", "prinsip", "suap", "gratifikasi", "manipulasi",
        ],
    },
    {
        "kode": "C",
        "nama": "Kemauan Belajar (Learning Agility)",
      #  "definisi": (
      #      "Keinginan dan kemampuan untuk cepat mempelajari hal baru, mengambil "
        #    "pelajaran dari pengalaman, terbuka terhadap umpan balik, dan menerapkannya "
      #      "pada situasi yang berbeda."
     #   ),
        "pertanyaan": (
            "Ceritakan pengalaman ketika Anda harus menguasai keterampilan, sistem, atau "
            "pekerjaan baru dalam waktu singkat."
        ),
        "panduan": [
            "Apa yang harus Anda pelajari dan mengapa?",
            "Langkah dan sumber belajar apa yang Anda gunakan?",
            "Kesalahan atau kesulitan apa yang Anda alami, dan apa pelajarannya?",
            "Bagaimana Anda menerapkan hal yang dipelajari itu dalam pekerjaan berikutnya?",
        ],
        "kata_kunci": [
            "belajar", "mempelajari", "pelatihan", "kursus", "tutorial", "membaca",
            "bertanya", "mentor", "praktik", "mencoba", "latihan", "kesalahan",
            "pelajaran", "menerapkan", "sistem baru", "keterampilan", "skill",
            "umpan balik", "feedback", "evaluasi", "memperbaiki", "adaptasi",
            "menguasai", "sertifikasi", "catatan", "video",
        ],
    },
    {
        "kode": "D",
        "nama": "Motivasi Berprestasi & Loyalitas Organisasi",
    #    "definisi": (
      #      "Dorongan untuk mencapai hasil terbaik melebihi standar, menetapkan target "
      #      "yang menantang, serta keterikatan dan komitmen untuk berkontribusi jangka "
       #     "panjang bagi kemajuan organisasi."
     #   ),
        "pertanyaan": "Ceritakan pencapaian kerja yang paling Anda banggakan.",
        "panduan": [
            "Apa pencapaiannya dan apa peran Anda secara spesifik?",
            "Apakah hasilnya melebihi target yang diminta? Mengapa Anda mengejarnya?",
            "Hambatan apa yang Anda atasi untuk mencapainya?",
            "Apa arti pencapaian itu bagi organisasi, dan apa yang membuat Anda ingin "
            "terus berkontribusi di sana?",
        ],
        "kata_kunci": [
            "target", "melebihi", "pencapaian", "prestasi", "berhasil", "hasil",
            "meningkat", "peningkatan", "persen", "penghargaan", "kontribusi",
            "organisasi", "perusahaan", "tim", "komitmen", "tantangan", "hambatan",
            "inisiatif", "bangga", "efisiensi", "penjualan", "kualitas", "visi",
            "misi", "jangka panjang", "karier",
        ],
    },
    {
        "kode": "E",
        "nama": "Ketahanan & Pengendalian Diri (Resilience)",
       # "definisi": (
         #   "Kemampuan tetap tenang, fokus, dan efektif di bawah tekanan, mengelola "
       #     "emosi secara sehat, serta bangkit kembali dengan cepat dari hambatan atau "
         #   "kegagalan."
       # ),
        "pertanyaan": (
            "Ceritakan periode kerja paling menekan yang pernah Anda alami, misalnya "
            "tenggat ketat, beban kerja berlebih, atau menghadapi orang yang sulit."
        ),
        "panduan": [
            "Apa situasinya dan apa yang membuatnya menekan?",
            "Apa yang Anda rasakan, dan bagaimana Anda mengendalikan emosi?",
            "Bagaimana Anda menjaga kualitas kerja dan kondisi diri selama periode itu?",
            "Apa hasilnya, dan apa yang Anda lakukan untuk bangkit jika hasilnya tidak "
            "sesuai harapan?",
        ],
        "kata_kunci": [
            "tekanan", "stres", "tenang", "emosi", "sabar", "fokus", "prioritas",
            "tenggat", "deadline", "lembur", "istirahat", "bangkit", "gagal",
            "kegagalan", "mengatur", "mengelola", "menarik napas", "olahraga",
            "dukungan", "keseimbangan", "marah", "kecewa", "positif", "jadwal",
            "beban kerja", "bertahan",
        ],
    },
]

KOMPETENSI_BY_KODE = {k["kode"]: k for k in KOMPETENSI}

RUBRIK = {
    5: "Sangat kuat: contoh spesifik dan lengkap (situasi, peran, tindakan, hasil), "
       "perilaku jelas mencerminkan kompetensi, ada hasil terukur dan refleksi matang.",
    4: "Kuat: contoh spesifik dengan tindakan dan hasil jelas, refleksi cukup baik.",
    3: "Memadai: ada contoh nyata, tetapi tindakan atau hasilnya kurang rinci.",
    2: "Kurang: jawaban umum atau hipotetis ('saya biasanya...'), sedikit bukti "
       "perilaku nyata.",
    1: "Sangat kurang: tidak ada contoh, menghindar, tidak relevan, atau perilaku yang "
       "diceritakan bertentangan dengan kompetensi.",
}

LABEL_SKOR = {5: "Sangat kuat", 4: "Kuat", 3: "Memadai", 2: "Kurang", 1: "Sangat kurang"}
