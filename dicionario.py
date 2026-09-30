import json
import re
from difflib import get_close_matches
import pyttsx3
import requests
import speech_recognition as sr
import unicodedata


# ==========================
# NORMALIZAÇÃO (remove acentos, minúsculas)
# ==========================

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).lower().strip()

# ==========================
# CARREGANDO O DICIONÁRIO
# ==========================

with open("Data.json", "r", encoding="utf-8") as arquivo:
    data = json.load(arquivo)


# ==========================
# FUNÇÃO PARA FALAR
# ==========================

def falar(texto):
    print("Assistente:", texto)
    engine = pyttsx3.init()
    engine.setProperty("voice", engine.getProperty("voices")[0].id)
    engine.setProperty("rate", 170)
    engine.say(texto)
    engine.runAndWait()
    engine.stop()


# ==========================
# RECONHECIMENTO DA VOZ
# ==========================

def comando():
    r = sr.Recognizer()

    with sr.Microphone() as source:

        print("Escutando...")

        r.pause_threshold = 1
        r.energy_threshold = 500

        r.adjust_for_ambient_noise(
            source,
            duration=1.5
        )

        audio = r.listen(source)

    try:

        print("Reconhecendo...")

        query = r.recognize_google(
            audio,
            language="pt-br"
        )

        print(f"Usuário falou: {query}\n")

        return query.lower()

    except Exception as e:

        print(e)
        print("Fale de novo por favor...")

        return "none"


# ==========================
# EXTRAI A PALAVRA DA FRASE
# ==========================

def extrair_palavra(frase):
    frase = frase.lower().strip()

    # Remove pontuação
    for char in ["?", ".", ",", "!", ";"]:
        frase = frase.replace(char, "")

    palavras = frase.split()

    if not palavras:
        return frase

    # Se a palavra "palavra" foi dita, pega tudo depois da última ocorrência
    if "palavra" in palavras:
        indice = len(palavras) - 1 - palavras[::-1].index("palavra")
        resto = palavras[indice + 1:]
        if resto:
            return " ".join(resto)

    # Caso contrário (ex: usuário só falou "carro"), a própria
    # última palavra da frase é a palavra buscada
    return palavras[-1]


# ==========================
# PROCURA NO DICIONÁRIO LOCAL
# ==========================

def procurar_localmente(palavra):
    palavra_norm = normalizar(palavra)

    for item in data:

        palavra_json = normalizar(item.get("word", ""))

        if palavra_json == palavra_norm:

            xml = item.get(
                "xml",
                ""
            )

            resultado = re.search(
                r"<def>(.*?)</def>",
                xml,
                re.DOTALL
            )

            if resultado:
                return resultado.group(1).strip()

    return None


# ==========================
# PROCURA ONLINE
# ==========================

def procurar_online(palavra):
    try:
        # URL da Dicio API
        url = f"https://dicio-api-ten.vercel.app/words/{palavra.lower().strip()}"

        resposta = requests.get(url, timeout=10)

        if resposta.status_code != 200:
            return None

        resultado = resposta.json()

        # A API retorna uma lista de definições para a palavra
        significados = []

        if isinstance(resultado, list):
            for item in resultado:
                # Extrai os significados da palavra
                meanings = item.get("meanings", [])
                for m in meanings:
                    # Limpa espaços extras
                    m_limpo = m.strip()
                    if m_limpo:
                        significados.append(m_limpo)

        return significados if significados else None

    except Exception as e:
        print(f"Erro na busca online: {e}")
        return None


# ==========================
# PROCURA PALAVRAS PARECIDAS
# ==========================

def procurar_parecida(palavra):
    palavra_norm = normalizar(palavra)

    mapa = {
        normalizar(item.get("word", "")): item.get("word", "")
        for item in data
    }

    parecidas = get_close_matches(
        palavra_norm,
        list(mapa.keys()),
        n=1,
        cutoff=0.8
    )

    if parecidas:
        return mapa[parecidas[0]]

    return None


# ==========================
# FUNÇÃO PRINCIPAL DO DICIONÁRIO
# ==========================

def traduzir(palavra):
    palavra = palavra.lower().strip()

    print(
        "\nPalavra pesquisada:",
        palavra
    )

    # --------------------------
    # 1. PROCURA NO JSON
    # --------------------------

    significado = procurar_localmente(
        palavra
    )

    if significado:
        falar(
            f"O significado de {palavra} é:"
        )

        falar(significado)

        return

    # --------------------------
    # 2. PROCURA PALAVRA PARECIDA
    # --------------------------

    sugestao = procurar_parecida(
        palavra
    )

    if sugestao:

        falar(
            f"Não encontrei a palavra {palavra}."
        )

        falar(
            f"Você quis dizer {sugestao}?"
        )

        resposta = comando()

        if "sim" in resposta:
            traduzir(sugestao)

            return

    # --------------------------
    # 3. PROCURA NA INTERNET
    # --------------------------

    falar(
        "Essa palavra não está no meu "
        "dicionário local. Vou procurar na internet."
    )

    resultados = procurar_online(
        palavra
    )

    if resultados:

        falar(
            "Encontrei a palavra desejada!"
        )

        # Limita a 3 definições
        for numero, significado in enumerate(
                resultados[:3],
                start=1
        ):
            falar(
                f"Significado {numero}:"
            )

            falar(significado)

        return

    # --------------------------
    # 4. PALAVRA NÃO ENCONTRADA
    # --------------------------

    falar(
        f"Não encontrei nenhuma definição "
        f"para {palavra}."
    )


# ==========================
# PROGRAMA PRINCIPAL
# ==========================

falar(
    "Olá! Diga uma palavra e eu vou mostrar o significado!"
)

frase = comando()

if frase != "none":
    palavra = extrair_palavra(

        frase
    )




    traduzir(palavra)