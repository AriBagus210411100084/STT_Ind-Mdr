import streamlit as st
import pandas as pd
import re
import speech_recognition as sr

# Fungsi untuk membaca CSV
def load_csv(file_path):
    return pd.read_csv(file_path)

# Fungsi untuk menentukan filter tingkatan
def determineTingkatFilter(tingkat):
    if tingkat == "1":
        filter_tingkatan = ["lomrah", None]
    elif tingkat == "2":
        filter_tingkatan = ["tengngaan", "alos", None]
    elif tingkat == "3":
        filter_tingkatan = ["alos tengghi", None]
    else:
        filter_tingkatan = []  # Jika tingkat tidak sesuai, tidak ada filter tingkatan khusus.
    return filter_tingkatan

# Fungsi untuk menerjemahkan n-gram
def translateNGram(input, tingkat):
    kamus = load_csv('kamus.csv')
    input = input.strip().lower()
    inputWords = input.split(" ")
    translatedArray = []
    filter_tingkatan = determineTingkatFilter(tingkat)

    i = 0
    while i < len(inputWords):
        if i + 1 < len(inputWords):
            bigram = " ".join(inputWords[i:i+2])
            filtered_kamus = kamus[
                (kamus['indonesia'].str.startswith(bigram)) & 
                (kamus['tingkatan'].isin(filter_tingkatan) | kamus['tingkatan'].isna())
            ]
            if not filtered_kamus.empty:
                if i + 2 < len(inputWords):
                    trigram = " ".join(inputWords[i:i+3])
                    trigram_result = filtered_kamus[filtered_kamus['indonesia'] == trigram]
                    if not trigram_result.empty:
                        translatedArray.append(trigram_result.iloc[0]['madura'])
                        i += 3
                        continue
                bigram_result = filtered_kamus[filtered_kamus['indonesia'] == bigram]
                if not bigram_result.empty:
                    translatedArray.append(bigram_result.iloc[0]['madura'])
                    i += 2
                    continue
        unigram = inputWords[i]
        unigram_result = kamus[
            (kamus['indonesia'] == unigram) & 
            (kamus['tingkatan'].isin(filter_tingkatan) | kamus['tingkatan'].isna())
        ]
        if not unigram_result.empty:
            translatedArray.append(unigram_result.iloc[0]['madura'])
        else:
            translatedArray.append(unigram)
        i += 1

    return " ".join(translatedArray)

# Fungsi FSA untuk memecah teks menjadi suku kata
def fsa_tingkat_satu(kata):
    vocal = ["a", "â", "e", "è", "i", "o", "u", "'", "È", "Â"]
    konsonan2 = ["b", "g", "d", "j", "k"]
    kata = kata.lower()
    kata = re.sub(r'[\\-]', '', kata)
    huruf = list(kata)
    hasil1 = []
    pola = []
    i = 0

    while i < len(huruf):
        if huruf[i] == "n":
            if (i + 1 < len(huruf) and (huruf[i + 1] == "g" or huruf[i + 1] == "y") and
                (i + 2 < len(huruf) and huruf[i + 2] in vocal)):
                hasil1.append(huruf[i] + huruf[i + 1] + huruf[i + 2])
                pola.append(3)
                i += 2
            elif (i + 1 < len(huruf) and (huruf[i + 1] == "g" or huruf[i + 1] == "y")):
                hasil1.append(huruf[i] + huruf[i + 1])
                pola.append(2)
                i += 1
            elif (i + 1 < len(huruf) and huruf[i + 1] in vocal):
                hasil1.append(huruf[i] + huruf[i + 1])
                pola.append(3)
                i += 1
            else:
                hasil1.append(huruf[i])
                pola.append(2)
            hasil1.append("-")
        elif huruf[i] in konsonan2:
            if (i + 1 < len(huruf) and huruf[i + 1] == "h" and
                (i + 2 < len(huruf) and huruf[i + 2] in vocal)):
                hasil1.append(huruf[i] + huruf[i + 1] + huruf[i + 2])
                pola.append(3)
                i += 2
            elif (i + 1 < len(huruf) and huruf[i + 1] == "h"):
                hasil1.append(huruf[i] + huruf[i + 1])
                pola.append(2)
                i += 1
            elif (i + 1 < len(huruf) and huruf[i + 1] in vocal):
                hasil1.append(huruf[i] + huruf[i + 1])
                pola.append(3)
                i += 1
            else:
                hasil1.append(huruf[i])
                pola.append(2)
            hasil1.append("-")
        elif huruf[i] in vocal:
            hasil1.append(huruf[i])
            hasil1.append("-")
            pola.append(1 if huruf[i] != "'" else 4)
        else:
            if (i + 1 < len(huruf) and huruf[i + 1] in vocal):
                hasil1.append(huruf[i] + huruf[i + 1])
                pola.append(3)
                i += 1
            else:
                hasil1.append(huruf[i])
                pola.append(2)
            hasil1.append("-")
        i += 1

    return [s.strip('-') for s in ''.join(hasil1).split('-') if s.strip('-')]

# Fungsi untuk memulai Speech-to-Text dan menerjemahkan
def speech_to_text_translate(tingkat_value):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("### Silakan berbicara...")
        st.info("Mikrofon aktif, berbicaralah sekarang!")
        try:
            audio = recognizer.listen(source)
            st.write("### Mengenali suara...")
            text = recognizer.recognize_google(audio, language="id-ID")
            st.write("### Teks Bahasa Indonesia:")
            st.text(text)

            translated_text = translateNGram(text, tingkat_value)
            st.write("### Teks Bahasa Madura:")
            st.text(translated_text)

            suku_kata = fsa_tingkat_satu(translated_text)
            st.write("### Pecahan Suku Kata:")
            st.text(", ".join(suku_kata))

        except sr.UnknownValueError:
            st.error("Suara tidak dapat dikenali, coba lagi.")
        except sr.RequestError as e:
            st.error(f"Kesalahan pada layanan pengenalan suara: {e}")

# Tampilan Streamlit
st.set_page_config(page_title="Sistem Penerjemah Indonesia-Madura", layout="wide")

st.markdown("""
    <style>
    .title {
        text-align: center;
        font-size: 2.5em;
        font-weight: bold;
        color: #4CAF50;
        margin-bottom: 20px;
        padding: 10px;
        border: 2px solid #4CAF50;
        border-radius: 10px;
    }
    .info-section {
        background-color: #f9f9f9;
        padding: 20px;
        margin: 20px 0;
        border-radius: 10px;
    }
    .footer {
        text-align: center;
        font-size: 1em;
        color: #777;
        margin-top: 20px;
    }
    .sidebar-menu {
        display: flex;
        flex-direction: column;
        background-color: #f8f8f8;
        padding: 10px;
        border-radius: 8px;
    }
    .sidebar-menu a {
        padding: 10px 20px;
        text-decoration: none;
        color: #333;
        border-radius: 5px;
        margin-bottom: 5px;
        background-color: #e1e1e1;
        text-align: center;
    }
    .sidebar-menu a:hover {
        background-color: #c7c7c7;
    }
    </style>
""", unsafe_allow_html=True)

# Navigasi menggunakan elemen HTML untuk menu
menu_options = ["Bahasa Madura", "Sistem Penerjemah", "Profil Pengembang"]
menu = st.sidebar.selectbox("Navigasi", menu_options)
if menu == "Bahasa Madura":
    st.markdown("""<div class='title'>Bahasa Madura</div>""", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-section'>
        <h2>Mengenal Bahasa Madura: Warisan Budaya Nusantara</h2>
    </div>
    """, unsafe_allow_html=True)

    st.image("madura.jpg", caption="Bahasa Madura", width=300)

    st.markdown("""
    <p style="text-align: justify;">Bahasa Madura adalah salah satu bahasa daerah di Indonesia yang digunakan oleh masyarakat Madura, 
                    terutama di Pulau Madura dan beberapa wilayah di Jawa Timur, seperti Surabaya, Situbondo, Bondowoso, dan Probolinggo. 
                    Bahasa ini termasuk dalam rumpun bahasa Austronesia dan memiliki keunikan dalam struktur tata bahasa, kosakata, dan pengucapannya. 
                    Bahasa Madura juga memiliki beberapa dialek, seperti dialek Bangkalan, Sumenep, dan Pamekasan, yang sedikit berbeda satu sama lain. Tulisan dalam bahasa Madura menggunakan aksara Latin, tetapi dahulu juga ditulis dengan aksara Jawa yang dimodifikasi.</p>
    <p style="text-align: justify;">Bahasa Madura memiliki peran penting dalam budaya masyarakat Madura, karena menjadi sarana utama untuk menyampaikan nilai-nilai, tradisi, dan kearifan lokal. 
                    Penggunaan bahasa ini meluas dalam kehidupan sehari-hari, baik dalam komunikasi formal maupun informal. Meski demikian, keberadaan bahasa Madura menghadapi tantangan dari pengaruh bahasa Indonesia sebagai bahasa nasional. 
                    Oleh karena itu, upaya pelestarian bahasa Madura terus dilakukan, termasuk melalui pengajaran di sekolah dan dokumentasi dalam bentuk karya tulis serta digital.</p>
    <h2>Urgensi Pelestarian Bahasa Madura dalam Kebudayaan Lokal</h2>
    <p style="text-align: justify;">Bahasa Madura memiliki peran yang sangat penting sebagai identitas budaya masyarakat Madura. 
                Sebagai bahasa daerah, Bahasa Madura tidak hanya menjadi alat komunikasi, tetapi juga sebagai wadah untuk melestarikan 
                nilai-nilai tradisional dan kearifan lokal. Melalui bahasa ini, masyarakat dapat mewariskan cerita rakyat, adat istiadat, 
                dan tradisi leluhur yang menjadi bagian tak terpisahkan dari kehidupan sosial dan spiritual mereka. Bahasa Madura juga 
                mencerminkan jati diri masyarakat Madura, memperkuat rasa kebersamaan, dan memupuk rasa bangga terhadap warisan budaya mereka.</p>
    <p style="text-align: justify;">Selain itu, Bahasa Madura berkontribusi dalam keragaman budaya nasional Indonesia. Pelestariannya berarti 
                menjaga salah satu unsur keanekaragaman budaya yang menjadi kekuatan bangsa. Di tengah arus globalisasi dan dominasi 
                bahasa nasional, melestarikan Bahasa Madura menjadi tantangan yang signifikan. Upaya ini penting untuk mencegah hilangnya 
                identitas lokal akibat homogenisasi budaya. Dengan demikian, Bahasa Madura menjadi bagian dari kekayaan budaya dunia yang 
                layak untuk dipertahankan dan dikembangkan.</p>
    <h2>Tingkatan Bahasa Madura: Cerminan Kesopanan dan Hierarki Sosial</h2>
    <p style="text-align: justify;">Bahasa Madura memiliki sistem tingkatan bahasa yang mencerminkan hubungan sosial, tingkat kesopanan, 
                dan penghormatan terhadap lawan bicara. Sistem ini mirip dengan beberapa bahasa daerah lain di Indonesia, seperti bahasa Jawa 
                dan Sunda, yang menggunakan tingkatan bahasa untuk menunjukkan status sosial dan keakraban. Ada tiga tingkatan utama dalam 
                bahasa Madura, yaitu <strong>"lomrah"</strong>, <strong>"tengngaan"</strong>, dan <strong>"alos"</strong>.</p>
    <p style="text-align: justify;"><strong>1. Lomrah (Tingkat Informal)</strong><br>
                Tingkatan ini digunakan dalam situasi yang santai dan akrab, terutama di antara teman sebaya, anggota keluarga dekat, 
                atau orang-orang yang memiliki hubungan sosial setara. Bahasa pada tingkat ini cenderung lugas, tidak berbelit-belit, dan 
                bebas dari unsur formalitas. Contoh kalimat dalam tingkat lomrah adalah: <em>"Ko are' makan apa?"</em> (Kamu sudah makan apa?). 
                Tingkat ini paling sering digunakan dalam percakapan sehari-hari di lingkungan informal.</p>
    <p style="text-align: justify;"><strong>2. Tengngaan (Tingkat Formal)</strong><br>
                Tingkatan tengngaan digunakan untuk percakapan yang lebih formal, biasanya dengan orang yang dihormati, seperti orang yang 
                lebih tua, atasan, atau dalam situasi resmi. Dalam tingkat ini, pemilihan kata menjadi lebih sopan dan terstruktur. 
                Contoh kalimat: <em>"Sampeyan are' ngakan apa?"</em> (Anda sudah makan apa?). Tingkatan ini mencerminkan rasa hormat tetapi 
                tidak setinggi tingkatan alos.</p>
    <p style="text-align: justify;"><strong>3. Alos atau Alos Tengghi (Tingkat Sangat Formal)</strong><br>
                Tingkat alos merupakan tingkatan tertinggi dalam bahasa Madura yang digunakan untuk menunjukkan rasa hormat yang mendalam 
                kepada orang-orang yang memiliki kedudukan tinggi dalam masyarakat, seperti tokoh agama, pejabat, atau tamu kehormatan. 
                Bahasa ini sangat terikat pada aturan kesopanan dan tata krama. Contoh kalimat: <em>"Panjenengan sare' dhahar napa?"</em> (Apakah Anda sudah makan?). 
                Tingkatan ini lebih jarang digunakan dalam kehidupan sehari-hari kecuali dalam acara-acara resmi atau saat berbicara dengan tokoh yang 
                sangat dihormati.</p>
    <p style="text-align: justify;">Sistem tingkatan ini menunjukkan bagaimana masyarakat Madura sangat menghargai sopan santun dan hierarki 
                sosial. Dengan memahami dan menggunakan tingkatan bahasa ini, seseorang dapat menunjukkan penghormatan yang sesuai kepada 
                lawan bicara berdasarkan usia, status sosial, atau hubungan mereka. Selain itu, sistem ini juga berfungsi sebagai alat untuk 
                menjaga harmoni sosial dan memperkuat ikatan antarindividu di masyarakat Madura.</p>
    <h2>Tantangan Pelestarian Bahasa Madura</h2>
    <p style="text-align: justify;">Pelestarian Bahasa Madura menghadapi berbagai tantangan, terutama dalam konteks modernisasi dan 
                globalisasi. Salah satu tantangan terbesar adalah dominasi Bahasa Indonesia sebagai bahasa nasional yang digunakan di 
                berbagai aspek kehidupan, seperti pendidikan, media, dan pemerintahan. Hal ini menyebabkan penutur asli Bahasa Madura, 
                terutama generasi muda, cenderung lebih memilih menggunakan Bahasa Indonesia dalam komunikasi sehari-hari. 
                Akibatnya, penggunaan Bahasa Madura menjadi semakin terbatas dan rentan ditinggalkan.</p>
    <p style="text-align: justify;">Selain itu, perubahan gaya hidup masyarakat Madura yang semakin modern juga memengaruhi minat terhadap 
                penggunaan Bahasa Madura. Banyak keluarga muda yang tidak lagi mengajarkan Bahasa Madura kepada anak-anak mereka, 
                karena merasa lebih praktis atau lebih modern menggunakan Bahasa Indonesia. Faktor lain adalah kurangnya materi pembelajaran 
                yang menarik dan tersedia secara luas, baik dalam bentuk buku, media digital, maupun program pendidikan formal. 
                Tanpa dukungan yang memadai, Bahasa Madura berisiko kehilangan relevansinya di tengah perkembangan zaman.</p>
    <p style="text-align: justify;">Tantangan lainnya adalah kurangnya dokumentasi dan penelitian tentang Bahasa Madura, seperti gramatika, 
                kosakata, atau sastra tradisionalnya. Dokumentasi yang terbatas membuat pelestarian Bahasa Madura sulit dilakukan secara 
                komprehensif, terutama jika dibandingkan dengan bahasa daerah lain yang sudah lebih terdokumentasi. Untuk mengatasi 
                tantangan ini, diperlukan langkah-langkah strategis seperti memasukkan Bahasa Madura ke dalam kurikulum lokal, 
                menciptakan konten digital berbahasa Madura, dan mendorong generasi muda untuk bangga menggunakan bahasa ibu mereka.</p>
                <br>
    """, unsafe_allow_html=True)

    st.image("banner.jpg", caption="Lestarikan Bahasa Daerah", width=1100)

elif menu == "Sistem Penerjemah":
    st.markdown("""<div class='title'>Sistem Penerjemah Bahasa Indonesia ke Bahasa Madura</div>""", unsafe_allow_html=True)
    st.header("Penerjemah Bahasa Indonesia ke Bahasa Madura")
    st.image("STT.jpg", caption="Speech To Text", width=300)
    st.markdown("""
    <p style="text-align: justify;">
        Sistem Penerjemah Bahasa Indonesia ke Bahasa Madura ini memungkinkan Anda untuk berbicara dalam Bahasa Indonesia, 
        dan sistem akan mengonversi suara Anda menjadi teks kemudian menerjemahkannya ke dalam Bahasa Madura. 
        Untuk memulai, cukup tekan tombol <strong>"Mulai Rekam Suara"</strong> di bawah ini. 
        Sistem akan merekam suara Anda dan menerjemahkan teks yang dihasilkan ke dalam Bahasa Madura berdasarkan tingkat formalitas percakapan.
    </p>
    """, unsafe_allow_html=True)
    st.title("Speech-to-Text Translator for Madurese Language")
    tingkat = st.selectbox(
        "Pilih tingkat bahasa Madura:",
        ("1 - Lomrah", "2 - Tengngaan", "3 - Alos Tengghi")
    )
    tingkat_value = tingkat.split(" - ")[0]

    if st.button("Rekam dan Terjemahkan"):
        speech_to_text_translate(tingkat_value)

    st.markdown("""<div class='info-section'>
    <h2>Deskripsi Sistem Penerjemahan Bahasa Indonesia-Madura</h2>
    <p style="text-align: justify;">Implementasi teknologi speech-to-text (STT) dalam sistem penerjemah Bahasa Indonesia-Madura dapat 
                meningkatkan efisiensi dan aksesibilitas dalam proses penerjemahan. Dengan menggunakan algoritma pengenalan suara, 
                sistem ini mampu mengonversi ucapan dalam Bahasa Indonesia ke dalam teks secara otomatis, yang kemudian diterjemahkan 
                ke dalam Bahasa Madura. Teknologi STT memanfaatkan model deep learning yang dilatih dengan data suara untuk mengenali 
                berbagai variasi aksen dan dialek, serta memahami konteks kalimat. Dengan begitu, pengguna cukup berbicara dalam 
                Bahasa Indonesia, dan sistem akan mengubahnya menjadi teks yang dapat diterjemahkan dengan cepat.</p>
    <p style="text-align: justify;">Selain itu, penerapan speech-to-text juga memudahkan interaksi langsung antara penutur Bahasa Indonesia 
                dan penerjemah Bahasa Madura, terutama dalam situasi komunikasi sehari-hari, seperti percakapan antar masyarakat Madura dan 
                non-Madura. Penggunaan STT memungkinkan proses penerjemahan yang lebih praktis tanpa perlu menulis teks secara manual, 
                sehingga menghemat waktu dan usaha. Hal ini juga membuka peluang untuk menciptakan aplikasi berbasis suara yang lebih ramah 
                pengguna, khususnya bagi mereka yang kesulitan mengetik atau memiliki keterbatasan dalam penggunaan perangkat elektronik. 
                Dengan sistem ini, pelestarian dan penyebaran Bahasa Madura juga dapat lebih mudah diakses dan dipelajari oleh masyarakat luas.</p>
    </div>""", unsafe_allow_html=True)

elif menu == "Profil Pengembang":

    col1, col2 = st.columns([1, 2])

    with col1:
        # Menggunakan st.image untuk menampilkan foto
        st.image("ari.png", width=250, caption="Ari Bagus Firmansyah")

    with col2:
        st.markdown("""
            <div class='title'>Profil Pengembang</div>
            <div class='info-section'>
                <p>Nama: Ari Bagus Firmansyah</p>
                <p>NIM: 210411100084</p>  
                <p>Universitas: Universitas Trunojoyo Madura</p>
                <p>Fokus Penelitian: Penerjemahan Bahasa Daerah menggunakan Teknologi</p>
            </div>
        """, unsafe_allow_html=True)
