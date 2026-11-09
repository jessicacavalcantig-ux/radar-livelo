"""Atualiza dados.json com as pontuações públicas dos parceiros Livelo.

Lê https://www.livelo.com.br/juntar-pontos/todos-os-parceiros, extrai cada
parceiro (nome, pontuação de hoje, taxa do Clube, taxa anterior em promoção,
link) e grava dados.json. Mantém as categorias que já estão no arquivo.
Se a leitura trouxer bem menos parceiros do que o arquivo atual, não grava
nada e termina com erro, para não apagar a página por causa de uma falha.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.livelo.com.br/juntar-pontos/todos-os-parceiros"
RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados.json"

TAXA = re.compile(r"(?:(Até)\s+)?(\d+)\s+pontos?\s+por\s+(R\$|U\$)\s*(\d+)", re.I)
ANTES = re.compile(r"Eram?\s+(\d+)\s+pontos?", re.I)


def baixar() -> str:
    resp = requests.get(
        URL,
        timeout=60,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9",
        },
    )
    resp.raise_for_status()
    return resp.text


def taxa(m):
    ate, pts, moeda, por = m.groups()
    return round(int(pts) / int(por), 3), bool(ate), "US$" if moeda.upper() == "U$" else "R$"


def extrair(html: str):
    sopa = BeautifulSoup(html, "html.parser")
    vistos, saida = set(), []
    for a in sopa.find_all("a", href=True):
        texto = " ".join(a.get_text(" ", strip=True).split())
        if "Ir para regras do parceiro" not in texto and "pontos por" not in texto and "ponto por" not in texto:
            continue
        taxas = list(TAXA.finditer(texto))
        if not taxas:
            continue
        nome = None
        img = a.find("img", alt=True)
        if img and img["alt"].strip():
            nome = re.sub(r"^Logo\s+", "", img["alt"].strip(), flags=re.I)
        if not nome:
            m = re.search(r"Logo\s+(.+?)\s+(?:Até\s+)?\d+\s+pontos?\s+por", texto)
            nome = m.group(1).strip() if m else None
        if not nome:
            continue
        nome = re.sub(r"^(Promoção|Nova)\s+", "", nome).strip()
        link = a["href"]
        if link.startswith("/"):
            link = "https://www.livelo.com.br" + link
        if link in vistos:
            continue
        vistos.add(link)

        atual, ate, unidade = taxa(taxas[0])
        clube = None
        mclube = re.search(r"Clube\s+((?:Até\s+)?\d+\s+pontos?\s+por\s+(?:R\$|U\$)\s*\d+)", texto)
        if mclube:
            clube = taxa(TAXA.search(mclube.group(1)))[0]
        antes = ANTES.search(texto)
        promo = antes is not None
        normal = int(antes.group(1)) if promo else atual
        base = clube if (promo and clube and atual <= normal) else atual
        saida.append({
            "parceiro": nome,
            "taxa_atual": atual,
            "taxa_normal": normal,
            "taxa_clube": clube,
            "unidade": unidade,
            "ate": ate,
            "promocao": promo,
            "multiplicador": round(base / normal, 2) if normal else 1,
            "link": link,
        })
    return saida


def chave(link: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", link).split("?")[0].rstrip("/").lower()


def main():
    antigo = json.loads(DADOS.read_text(encoding="utf-8")) if DADOS.exists() else {}
    antigos = antigo.get("parceiros", []) if isinstance(antigo, dict) else antigo
    por_link = {chave(p["link"]): p for p in antigos}
    por_nome = {p["parceiro"].lower(): p for p in antigos}

    novos = extrair(baixar())
    minimo = int(len(antigos) * 0.8) if antigos else 50
    if len(novos) < minimo:
        print(f"Leitura trouxe só {len(novos)} parceiros (mínimo {minimo}). Nada foi alterado.")
        sys.exit(1)

    for p in novos:
        velho = por_link.get(chave(p["link"])) or por_nome.get(p["parceiro"].lower())
        p["categoria"] = velho["categoria"] if velho else "Outros"
        if velho:
            p["parceiro"] = velho["parceiro"]

    dados = {
        "atualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": os.environ.get("GITHUB_REPOSITORY", antigo.get("repo", "") if isinstance(antigo, dict) else ""),
        "parceiros": sorted(novos, key=lambda p: p["parceiro"].lower()),
    }
    DADOS.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    promos = sum(p["promocao"] for p in novos)
    print(f"{len(novos)} parceiros, {promos} em promoção.")


if __name__ == "__main__":
    main()
