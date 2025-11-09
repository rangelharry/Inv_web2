from modules.barcode_utils import gerar_qrcode, gerar_barcode
from modules.barcode_scanner import ler_codigo_imagem
from modules.reservas import ReservaManager
from modules.manutencao_preventiva import ManutencaoPreventivaManager
import datetime

def test_qrcode_barcode():
    print("=== TESTE QR CODE E BARCODE ===")
    dado = "ITEM12345"
    img_qr = gerar_qrcode(dado)
    img_bar = gerar_barcode(dado)
    img_qr.save("test_qrcode.png")
    img_bar.save("test_barcode.png")
    print("QR Code e Barcode gerados e salvos.")
    # Teste leitura
    resultado = ler_codigo_imagem("test_qrcode.png")
    print(f"Leitura QR Code: {resultado}")

def test_reservas():
    print("=== TESTE RESERVAS ===")
    reservas = ReservaManager()
    hoje = datetime.date.today()
    ok = reservas.reservar(1, "usuario1", hoje, hoje)
    print(f"Reserva criada: {ok}")
    conflito = reservas.reservar(1, "usuario2", hoje, hoje)
    print(f"Reserva em conflito: {not conflito}")
    print(f"Reservas: {reservas.listar_reservas(1)}")

def test_manutencao():
    print("=== TESTE MANUTENÇÃO PREVENTIVA ===")
    man = ManutencaoPreventivaManager()
    hoje = datetime.date.today()
    man.agendar_manutencao(1, hoje, "Troca de óleo")
    man.agendar_manutencao(1, hoje + datetime.timedelta(days=10), "Revisão geral")
    print(f"Próximas manutenções: {man.proximas_manutencoes(15)}")
    man.registrar_realizacao(1, hoje)
    print(f"Histórico: {man.listar_manutencoes(1)}")

if __name__ == "__main__":
    test_qrcode_barcode()
    test_reservas()
    test_manutencao()
