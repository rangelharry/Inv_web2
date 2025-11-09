import cv2
from pyzbar import pyzbar

# Função para ler QR Code ou código de barras de uma imagem

def ler_codigo_imagem(path_imagem: str):
    imagem = cv2.imread(path_imagem)
    codigos = pyzbar.decode(imagem)
    resultados = []
    for codigo in codigos:
        resultados.append(codigo.data.decode('utf-8'))
    return resultados

# Função para capturar da webcam (exemplo básico)
def ler_codigo_webcam():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        codigos = pyzbar.decode(frame)
        for codigo in codigos:
            texto = codigo.data.decode('utf-8')
            print(f"Código detectado: {texto}")
            cap.release()
            cv2.destroyAllWindows()
            return texto
        cv2.imshow('Leitor QR/Barcode', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return None
