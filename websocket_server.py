import asyncio
import websockets
import json
import logging

# Configura o logging para dar mais informações
logging.basicConfig(level=logging.INFO)

# Guarda a lista de clientes (navegadores) conectados
connected_clients = set()

# AQUI ESTÁ A CORREÇÃO: A função agora só recebe 'websocket'
async def handler(websocket):
    """Lida com conexões de clientes e envia os eventos da viagem."""
    connected_clients.add(websocket)
    logging.info(f"Cliente conectado: {websocket.remote_address}")
    try:
        # Mantém a conexão aberta para ouvir mensagens do navegador
        async for message in websocket:
            try:
                data = json.loads(message)
                # Verifica se a mensagem é para iniciar a simulação
                if data.get("action") == "start_trip":
                    diario = data.get("diario", [])
                    logging.info(f"Recebido pedido para iniciar simulação com {len(diario)} turnos.")
                    
                    # Envia cada evento do diário com um intervalo de 2 segundos
                    for item in diario:
                        payload = json.dumps({"type": "trip_event", "data": item})
                        await websocket.send(payload)
                        await asyncio.sleep(2) # Pausa entre os eventos

                    # Ao final do loop, envia uma mensagem de conclusão
                    await websocket.send(json.dumps({"type": "trip_complete"}))
                    logging.info("Simulação concluída e enviada ao cliente.")

            except json.JSONDecodeError:
                logging.error("Erro: Mensagem recebida não é um JSON válido.")
            except Exception as e:
                logging.error(f"Erro durante a simulação: {e}")

    finally:
        # Remove o cliente da lista quando ele se desconectar
        connected_clients.remove(websocket)
        logging.info(f"Cliente desconectado: {websocket.remote_address}")

async def main():
    """Inicia o servidor WebSocket."""
    # Usando '0.0.0.0' para garantir que ele aceite conexões
    async with websockets.serve(handler, "0.0.0.0", 8765):
        logging.info("Servidor WebSocket iniciado em ws://0.0.0.0:8765")
        await asyncio.Future()  # Mantém o servidor rodando para sempre

if __name__ == "__main__":
    asyncio.run(main())