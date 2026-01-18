import getpass
import math
import os
import re
import shutil
import sys
import textwrap

# Terminal

def suporta_ansi() -> bool:
    if not sys.stdout.isatty():
        return False
    term = os.environ.get("TERM", "")
    return term not in ("", "dumb")

ANSI = suporta_ansi()

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def remover_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)

def tamanho_visivel(s: str) -> int:
    return len(remover_ansi(s))

def _esc(code: str) -> str:
    return f"\033[{code}m" if ANSI else ""

def cor(texto: str, code: str) -> str:
    return f"{_esc(code)}{texto}{_esc('0')}" if ANSI else texto

def negrito(s: str) -> str: return cor(s, "1")
def fraco(s: str) -> str: return cor(s, "2")
def vermelho(s: str) -> str: return cor(s, "31")
def amarelo(s: str) -> str: return cor(s, "33")
def verde(s: str) -> str: return cor(s, "32")
def ciano(s: str) -> str: return cor(s, "36")

def largura_terminal(padrao: int = 92) -> int:
    try:
        w = shutil.get_terminal_size((padrao, 24)).columns
        return max(64, min(150, w))
    except Exception:
        return padrao

def limpar_tela() -> None:
    if sys.stdout.isatty():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

def ler_senha_mascarada() -> str:
    if os.name == "nt":
        import msvcrt
        buf = []
        while True:
            ch = msvcrt.getwch()

            if ch in ("\r", "\n"):
                return "".join(buf)

            if ch == "\x03":
                raise KeyboardInterrupt

            if ch in ("\b", "\x7f"):
                if buf:
                    buf.pop()
                    print("\b \b", end="", flush=True)
                continue

            if ch in ("\x00", "\xe0"):
                msvcrt.getwch()
                continue

            buf.append(ch)
            print("*", end="", flush=True)
    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        buf = []
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)

                if ch in ("\r", "\n"):
                    return "".join(buf)

                if ch == "\x03":
                    raise KeyboardInterrupt

                if ch in ("\x7f", "\b"):
                    if buf:
                        buf.pop()
                        print("\b \b", end="", flush=True)
                    continue

                buf.append(ch)
                print("*", end="", flush=True)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

# Layout / boxes

def quebrar_visivel(texto: str, width: int) -> list[str]:
    """
    Quebra texto respeitando largura 'visível' (sem ANSI).
    Simples e robusto: remove ANSI para wrap, mas mantém a string original
    quando não tem ANSI (nossos casos longos não têm ANSI mesmo).
    """
    plain = remover_ansi(texto)

    if plain != texto and tamanho_visivel(texto) > width:
        texto = plain
    return textwrap.wrap(texto, width=max(8, width)) or [""]

def preencher_ate(s: str, width: int) -> str:
    # padding baseado no comprimento visível
    pad = width - tamanho_visivel(s)
    if pad <= 0:
        return s
    return s + (" " * pad)

def caixa(titulo: str, linhas: list[str], width: int) -> list[str]:
    width = max(24, width)
    inner_w = width - 2

    # Topo com título
    if titulo:
        t = f" {titulo} "
        if len(t) > inner_w:
            t = t[:inner_w]
        top = "┌" + t + "─" * (inner_w - len(t)) + "┐"
    else:
        top = "┌" + "─" * inner_w + "┐"
    bottom = "└" + "─" * inner_w + "┘"

    out = [top]
    for ln in linhas:
        wrapped = quebrar_visivel(ln, inner_w)
        for wln in wrapped:
            if tamanho_visivel(wln) > inner_w:
                wln = remover_ansi(wln)[:inner_w]
            out.append("│" + preencher_ate(wln, inner_w) + "│")
    out.append(bottom)
    return out

def juntar_lado(esq: list[str], dir_: list[str], gap: int = 2) -> list[str]:
    lh, rh = len(esq), len(dir_)
    h = max(lh, rh)
    l_w = len(esq[0]) if esq else 0
    r_w = len(dir_[0]) if dir_ else 0
    left_pad = esq + [" " * l_w] * (h - lh)
    right_pad = dir_ + [" " * r_w] * (h - rh)
    spacer = " " * gap
    return [left_pad[i] + spacer + right_pad[i] for i in range(h)]

def centralizar_linha(texto: str, width: int) -> str:
    plain = remover_ansi(texto)
    if len(plain) >= width:
        return plain[:width]
    pad = (width - len(plain)) // 2
    return " " * pad + texto

# Tempo

def pluralizar(n: int, singular: str, plural_: str) -> str:
    return singular if n == 1 else plural_

def formatar_anos_grandes(anos: float) -> str:
    y = float(anos)

    if y < 1_000_000:
        mil = int(round(y / 1_000))
        if mil <= 0:
            mil = 1
        return f"{mil} mil anos"

    escalas = [
        (1_000_000, "milhão", "milhões"),
        (1_000_000_000, "bilhão", "bilhões"),
        (1_000_000_000_000, "trilhão", "trilhões"),
        (1_000_000_000_000_000, "quatrilhão", "quatrilhões"),
        (1_000_000_000_000_000_000, "quintilhão", "quintilhões"),
        (1_000_000_000_000_000_000_000, "sextilhão", "sextilhões"),
        (1_000_000_000_000_000_000_000_000, "septilhão", "septilhões"),
        (1_000_000_000_000_000_000_000_000_000, "octilhão", "octilhões"),
        (1_000_000_000_000_000_000_000_000_000_000, "nonilhão", "nonilhões"),
        (1_000_000_000_000_000_000_000_000_000_000_000, "decilhão", "decilhões"),
        (1_000_000_000_000_000_000_000_000_000_000_000_000, "undecilhão", "undecilhões"),
        (1_000_000_000_000_000_000_000_000_000_000_000_000_000, "duodecilhão", "duodecilhões"),
    ]

    idx = 0
    for i, (b, _, _) in enumerate(escalas):
        if y >= b:
            idx = i
        else:
            break

    while True:
        base, sing, plur_ = escalas[idx]
        valor = int(round(y / base))
        if valor >= 1000 and idx + 1 < len(escalas):
            idx += 1
            continue
        unidade = sing if valor == 1 else plur_
        return f"{valor} {unidade} de anos"

def formatar_duracao(segundos: float) -> str:
    if segundos <= 0:
        return "< 1 picosegundo"

    ano_sec = 31536000.0
    if segundos >= ano_sec:
        anos = segundos / ano_sec
        if anos < 1.5:
            return "1 ano"
        if anos < 1000:
            a = int(round(anos))
            return f"{a} {pluralizar(a, 'ano', 'anos')}"
        return formatar_anos_grandes(anos)

    unidades = [
        ("picosegundo", "picosegundos", 1e-12),
        ("nanossegundo", "nanossegundos", 1e-9),
        ("microssegundo", "microssegundos", 1e-6),
        ("milissegundo", "milissegundos", 1e-3),
        ("segundo", "segundos", 1.0),
        ("minuto", "minutos", 60.0),
        ("hora", "horas", 3600.0),
        ("dia", "dias", 86400.0),
        ("semana", "semanas", 604800.0),
    ]

    escolhida = unidades[0]
    for u in unidades:
        if segundos >= u[2]:
            escolhida = u
        else:
            break

    sing, plur_, base = escolhida
    valor = int(round(segundos / base))
    if valor <= 0:
        valor = 1
    return f"{valor} {pluralizar(valor, sing, plur_)}"

def formatar_taxa_texto(rps: int) -> str:
    if rps >= 1_000_000_000:
        return f"{rps // 1_000_000_000} bilhões tentativas/seg"
    if rps >= 1_000_000:
        return f"{rps // 1_000_000} milhões tentativas/seg"
    if rps >= 1_000:
        return f"{rps // 1_000} mil tentativas/seg"
    return f"{rps} tentativas/seg"

# Senha (análise / pontuação)

def analisar_senha(senha: str) -> dict:
    return {
        "length": len(senha),
        "upper": any(ch.isupper() for ch in senha),
        "lower": any(ch.islower() for ch in senha),
        "digit": any(ch.isdigit() for ch in senha),
        "symbol": any(not ch.isalnum() for ch in senha),
        "spaces": any(ch.isspace() for ch in senha),
    }

def entropia_bits(senha: str) -> float:
    pool = 0
    if any(ch.islower() for ch in senha): pool += 26
    if any(ch.isupper() for ch in senha): pool += 26
    if any(ch.isdigit() for ch in senha): pool += 10
    if any((not ch.isalnum()) and (not ch.isspace()) for ch in senha): pool += 32
    if pool == 0:
        return 0.0
    return len(senha) * math.log2(pool)

def pontuar_senha(dados: dict, ent: float) -> int:
    s = 0
    if dados["length"] >= 16:
        s += 3
    elif dados["length"] >= 12:
        s += 2
    elif dados["length"] >= 8:
        s += 1

    s += int(dados["upper"])
    s += int(dados["lower"])
    s += int(dados["digit"])
    s += int(dados["symbol"])

    if dados["spaces"]:
        s -= 1

    if ent >= 60:
        s += 2
    elif ent >= 40:
        s += 1

    return max(0, min(s, 8))

def nivel_forca(pontos: int) -> str:
    if pontos <= 3:
        return "FRACA"
    if pontos <= 6:
        return "MÉDIA"
    return "FORTE"

def cor_forca(nivel: str):
    return vermelho if nivel == "FRACA" else amarelo if nivel == "MÉDIA" else verde

def barra_forca(pontos: int, max_pontos: int = 8, width: int = 22) -> str:
    filled = int(round((pontos / max_pontos) * width))
    blocks = "█" * filled + "░" * (width - filled)
    if pontos <= 3:
        return vermelho(blocks)
    if pontos <= 6:
        return amarelo(blocks)
    return verde(blocks)

def segundos_para_quebrar(ent: float, tentativas_por_seg: int) -> float:
    tentativas_medias = 2 ** max(ent - 1.0, 0.0)
    return tentativas_medias / tentativas_por_seg

# Feedback

def montar_feedback(dados: dict, ent: float, pontos: int) -> list[str]:
    positivos = []
    dicas = []

    if dados["length"] >= 16:
        positivos.append("Comprimento excelente (16+).")
    elif dados["length"] >= 12:
        positivos.append("Comprimento bom (12+).")
    elif dados["length"] >= 8:
        positivos.append("Comprimento ok (8+).")
    else:
        positivos.append("Boa iniciativa — dá pra fortalecer rápido.")

    if dados["lower"]: positivos.append("Tem minúsculas.")
    if dados["upper"]: positivos.append("Tem maiúsculas.")
    if dados["digit"]: positivos.append("Tem números.")
    if dados["symbol"]: positivos.append("Tem símbolos.")
    if not dados["spaces"]:
        positivos.append("Sem espaços (bom).")

    if ent >= 60:
        positivos.append("Entropia alta.")
    elif ent >= 40:
        positivos.append("Entropia razoável.")

    if dados["length"] < 8:
        dicas.append("Aumente o comprimento para pelo menos 8 (ideal 12+).")
    if not dados["lower"]:
        dicas.append("Adicione letras minúsculas.")
    if not dados["upper"]:
        dicas.append("Adicione letras maiúsculas.")
    if not dados["digit"]:
        dicas.append("Inclua números.")
    if not dados["symbol"]:
        dicas.append("Inclua símbolos.")
    if dados["spaces"]:
        dicas.append("Evite espaços (copy/paste costuma dar ruim).")
    if ent < 30:
        dicas.append("Aumente a entropia (mais comprimento + variedade).")

    out = []
    out.append("Pontos fortes: " + " ".join(positivos))
    if dicas:
        out.append("Para melhorar: " + " ".join(dicas))
    else:
        out.append("Para melhorar: Nada crítico detectado. Só evite reutilizar a mesma senha.")
    if pontos == 8:
        out.append("Resumo: Forte e bem montada.")
    elif pontos >= 5:
        out.append("Resumo: Boa base; com pequenos ajustes fica ótima.")
    else:
        out.append("Resumo: Com essas dicas, você sobe o nível fácil.")
    return out

# Telas

def imprimir_cabecalho(linha_ctrl: str, w: int) -> None:
    print(ciano("═" * w))
    print(ciano(centralizar_linha("Verificador de Robustez de Senhas", w)))
    print(fraco(centralizar_linha(linha_ctrl, w)))
    print(ciano("═" * w))

def tela_entrada() -> tuple[int, int, int]:
    w = largura_terminal()
    limpar_tela()
    imprimir_cabecalho("Ctrl+C = sair | Enter = confirmar", w)
    print()

    bw = min(76, w - 4)
    bw = max(30, bw)
    inner_w = bw - 2
    left_pad = (w - bw) // 2

    title = " Entrada "
    top = "┌" + title + "─" * (inner_w - len(title)) + "┐"

    lines = [
        "Digite sua senha abaixo (será exibido como *):",
        "",
    ]

    print(" " * left_pad + top)
    for ln in lines:
        for wln in quebrar_visivel(ln, inner_w):
            print(" " * left_pad + "│" + preencher_ate(wln, inner_w) + "│")

    prefix = "Senha: "
    print(" " * left_pad + "│" + prefix, end="", flush=True)

    return w, left_pad, bw

def ler_senha_bonita() -> str:
    w, left_pad, bw = tela_entrada()
    inner_w = bw - 2
    prefix = "Senha: "

    typed = ler_senha_mascarada()

    stars = "*" * len(typed)
    used = len(prefix) + len(stars)
    remaining = max(0, inner_w - used)
    print(" " * remaining + "│")
    print(" " * left_pad + "└" + "─" * inner_w + "┘")

    return typed

def tela_resultado(dados: dict, ent: float, pontos: int, nivel: str,
                   rps_online: int, rps_offline: int) -> None:
    w = largura_terminal()
    gap = 2
    two_cols = w >= 96
    col_w = (w - gap) // 2 if two_cols else min(86, w - 4)
    col_w = max(30, col_w)

    sec_on = segundos_para_quebrar(ent, rps_online)
    sec_off = segundos_para_quebrar(ent, rps_offline)
    t_on = formatar_duracao(sec_on)
    t_off = formatar_duracao(sec_off)
    headline = f"Levaria cerca de {t_off} para quebrar sua senha (offline)."

    nivel_colorido = cor_forca(nivel)(nivel)
    mix = []
    if dados["lower"]: mix.append("a-z")
    if dados["upper"]: mix.append("A-Z")
    if dados["digit"]: mix.append("0-9")
    if dados["symbol"]: mix.append("!@#")
    if dados["spaces"]: mix.append("␠")
    mix_txt = ", ".join(mix) if mix else "—"

    result_lines = [
        f"{negrito('Força:')} {nivel_colorido}   {barra_forca(pontos)} {fraco(f'({pontos}/8)')}",
        f"{negrito('Entropia:')} {ent:.2f} bits",
        f"{negrito('Conjunto:')} {mix_txt}",
    ]
    result_card = caixa("Resultado", result_lines, col_w)

    time_lines = [
        f"Online  ({formatar_taxa_texto(rps_online)}):  {t_on}",
        f"Offline ({formatar_taxa_texto(rps_offline)}): {t_off}",
    ]
    time_card = caixa("Tempo estimado (média)", time_lines, col_w)

    checks = [
        ("Comprimento (12+)", dados["length"] >= 12),
        ("Minúsculas", dados["lower"]),
        ("Maiúsculas", dados["upper"]),
        ("Números", dados["digit"]),
        ("Símbolos", dados["symbol"]),
        ("Sem espaços", not dados["spaces"]),
    ]
    check_lines = []
    for name, ok in checks:
        mark = verde("✓") if ok else vermelho("✗")
        check_lines.append(f"{mark} {name}")
    checklist_card = caixa("Checklist", check_lines, col_w)

    feedback_lines = montar_feedback(dados, ent, pontos)
    feedback_card = caixa("Feedback", feedback_lines, col_w)

    limpar_tela()
    imprimir_cabecalho("Ctrl+C = sair | Enter = nova senha", w)
    print()
    print(negrito(centralizar_linha(headline, w)))
    print()

    if two_cols:
        left = result_card + [""] + time_card
        right = checklist_card + [""] + feedback_card
        for ln in juntar_lado(left, right, gap=gap):
            print(ln)
    else:
        for block in (result_card, time_card, checklist_card, feedback_card):
            for ln in block:
                print(ln)
            print()

    print(fraco(centralizar_linha("Dica: use senhas únicas e, se possível, um gerenciador de senhas.", w)))
    print()

# Main loop

def main():
    ONLINE_RPS = 10
    OFFLINE_RPS = 10_000_000_000

    while True:
        senha = ler_senha_bonita()
        if not senha:
            limpar_tela()
            print(vermelho("Senha vazia. Tenta de novo."))
            try:
                input(fraco("Pressione Enter para voltar... "))
            except EOFError:
                return
            continue

        dados = analisar_senha(senha)
        ent = entropia_bits(senha)
        pontos = pontuar_senha(dados, ent)
        nivel = nivel_forca(pontos)

        tela_resultado(dados, ent, pontos, nivel, ONLINE_RPS, OFFLINE_RPS)

        try:
            input()
        except EOFError:
            return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaindo.")
