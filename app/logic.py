import random
from typing import Optional
from app.schemas import Cell, Position, SetupResponse, PlayerTurnResponse

TAMANHO_TABULEIRO = 5

PROFESSORES_POR_TIME = {
    1: ["CLARO", "REY"],
    2: ["KARIN", "BEATRIZ"],
}

def celulas_adjacentes(linha: int, coluna: int) -> list[tuple[int, int]]:
    vizinhos = []
    for dl in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dl == 0 and dc == 0:
                continue
            nova_linha, nova_coluna = linha + dl, coluna + dc
            if 0 <= nova_linha < TAMANHO_TABULEIRO and 0 <= nova_coluna < TAMANHO_TABULEIRO:
                vizinhos.append((nova_linha, nova_coluna))
    return vizinhos

def encontrar_professor(tabuleiro: list[list[Cell]], nome: str) -> Optional[tuple[int, int]]:
    for l in range(TAMANHO_TABULEIRO):
        for c in range(TAMANHO_TABULEIRO):
            if tabuleiro[l][c].professor == nome:
                return (l, c)
    return None

# Heurística

def avaliar_jogada(tabuleiro: list[list[Cell]], jogada: PlayerTurnResponse, professores_oponente: list[str]) -> int:
    score = 0
    nivel_dst = tabuleiro[jogada.move_to.row][jogada.move_to.col].level
    nivel_men = tabuleiro[jogada.mentor_at.row][jogada.mentor_at.col].level
    score += nivel_dst * 20
    distancia_centro = abs(jogada.move_to.row - 2) + abs(jogada.move_to.col - 2)
    score -= distancia_centro * 2
    if (jogada.mentor_at.row, jogada.mentor_at.col) in celulas_adjacentes(jogada.move_to.row, jogada.move_to.col):
        score += 5
    if nivel_men == 2:
        for prof_oponente in professores_oponente:
            pos_oponente = encontrar_professor(tabuleiro, prof_oponente)
            if pos_oponente:
                nivel_atual_oponente = tabuleiro[pos_oponente[0]][pos_oponente[1]].level
                if (jogada.mentor_at.row, jogada.mentor_at.col) in celulas_adjacentes(*pos_oponente):
                    if nivel_atual_oponente >= 2:
                        score -= 1000 
    return score

# Fase de posicionamento

def choose_setup(tabuleiro: list[list[Cell]]) -> SetupResponse:
    candidatas = [
        (l, c)
        for l in range(TAMANHO_TABULEIRO)
        for c in range(TAMANHO_TABULEIRO)
        if tabuleiro[l][c].level == 0 and tabuleiro[l][c].professor is None
    ]
    melhor_posicao = min(candidatas, key=lambda pos: abs(pos[0] - 2) + abs(pos[1] - 2))
    return SetupResponse(row=melhor_posicao[0], col=melhor_posicao[1])

# Fase de turnos normais

def choose_turn(tabuleiro: list[list[Cell]], id_time: int) -> Optional[PlayerTurnResponse]:
    time_oponente = 2 if id_time == 1 else 1
    professores_oponente = PROFESSORES_POR_TIME[time_oponente]
    jogadas_vitoria: list[PlayerTurnResponse] = []
    jogadas_bloqueio: list[PlayerTurnResponse] = []
    jogadas_normais: list[PlayerTurnResponse] = []
    for professor in PROFESSORES_POR_TIME[id_time]:
        posicao = encontrar_professor(tabuleiro, professor)
        if posicao is None:
            continue
        linha_atual, coluna_atual = posicao
        nivel_atual = tabuleiro[linha_atual][coluna_atual].level
        for linha_dst, coluna_dst in celulas_adjacentes(linha_atual, coluna_atual):
            celula_dst = tabuleiro[linha_dst][coluna_dst]
            if celula_dst.professor is not None:
                continue
            if celula_dst.level == 4:
                continue
            if celula_dst.level > nivel_atual + 1:
                continue
            if celula_dst.level == 3:
                jogadas_vitoria.append(PlayerTurnResponse(
                    professor=professor,
                    move_to=Position(row=linha_dst, col=coluna_dst),
                ))
                continue
            for linha_men, coluna_men in celulas_adjacentes(linha_dst, coluna_dst):
                celula_men = tabuleiro[linha_men][coluna_men]
                eh_origem = (linha_men, coluna_men) == (linha_atual, coluna_atual)
                if not (celula_men.professor is None or eh_origem):
                    continue
                if celula_men.level >= 4:
                    continue
                jogada = PlayerTurnResponse(
                    professor=professor,
                    move_to=Position(row=linha_dst, col=coluna_dst),
                    mentor_at=Position(row=linha_men, col=coluna_men),
                )
                celula_ja_sera_graduada = celula_men.level == 3
                if celula_ja_sera_graduada:
                    bloqueio = False
                    for prof_oponente in professores_oponente:
                        pos_oponente = encontrar_professor(tabuleiro, prof_oponente)
                        if pos_oponente and (linha_men, coluna_men) in celulas_adjacentes(*pos_oponente):
                            jogadas_bloqueio.append(jogada)
                            bloqueio = True
                            break
                    if not bloqueio:
                        jogadas_normais.append(jogada)
                else:
                    jogadas_normais.append(jogada)
    if jogadas_vitoria:
        return random.choice(jogadas_vitoria)
    if jogadas_bloqueio:
        return random.choice(jogadas_bloqueio)
    if jogadas_normais:
        melhor_jogada = None
        maior_pontuacao = float('-inf')
        for jogada in jogadas_normais:
            pontuacao = avaliar_jogada(tabuleiro, jogada, professores_oponente)
            pontuacao += random.uniform(0, 0.5) 
            if pontuacao > maior_pontuacao:
                maior_pontuacao = pontuacao
                melhor_jogada = jogada
        return melhor_jogada
    return None