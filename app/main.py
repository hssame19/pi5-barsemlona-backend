from fastapi import FastAPI, HTTPException
from datetime import date
from app.schemas import AITurnRequest, TurnPhase
from app.logic import choose_setup, choose_turn

app = FastAPI (
    title="Barsemlona - O jogador (não tão) inteligente",
    desc="API Barsemlona para o PI 5",
    version="0.1.0"
)

# @app.get("/hello")
# async def hello():
#     return "Olá mundo!"

# End point que verifica a saúde da API
@app.get("/health")
async def health():
    return date.today()

# Recebe um estado do tabuleiro e, a partir disso, decidir o que fazer
@app.post("/move")
async def move(body: AITurnRequest):
  """
  Endpoint principal chamado pelo orquestrador de partidas.
  
  Recebe o estado completo de um turno da partida e devolve a jogada escolhida.
  """
  if body.turn_phase == TurnPhase.SETUP:
     return choose_setup(body.board)
  else:
    jogada = choose_turn(body.board, int(body.your_team))
    return jogada