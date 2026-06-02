import re
import time
import logging
import serial

logger = logging.getLogger(__name__)


class BalancaToledoError(Exception):
    pass

class BalancaConexaoError(BalancaToledoError):
    pass

class BalancaTimeoutError(BalancaToledoError):
    pass

class BalancaRespostaError(BalancaToledoError):
    pass


class BalancaToledo:
    ENQ = b"\x05"

    def __init__(self, porta="COM4", baud_rate=9600, timeout=2.0, delay_leitura=0.5):
        self.porta = porta
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.delay_leitura = delay_leitura

    def ler_peso(self):
        try:
            with serial.Serial(
                port=self.porta,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            ) as ser:
                logger.info(f"Porta {self.porta} aberta.")
                return self._solicitar_peso(ser)
        except serial.SerialException as exc:
            msg = f"Nao foi possivel abrir '{self.porta}'. Detalhe: {exc}"
            raise BalancaConexaoError(msg) from exc

    def _solicitar_peso(self, ser):
        ser.reset_input_buffer()
        ser.write(self.ENQ)
        time.sleep(self.delay_leitura)
        resposta_bruta = ser.read_all()
        if not resposta_bruta:
            raise BalancaTimeoutError(f"Sem resposta em {self.timeout}s.")
        resposta_str = resposta_bruta.decode("ascii", errors="replace").strip()
        logger.info(f"Resposta bruta: {repr(resposta_str)}")
        return self._extrair_peso(resposta_str)

    def _extrair_peso(self, resposta):
        limpa = resposta.replace("\x02", "").replace("\x03", "").strip()
        logger.info(f"Resposta limpa: {repr(limpa)}")

        match = re.search(r"([\d]+[.,][\d]+)", limpa)
        if match:
            peso_str = match.group(1).replace(",", ".")
            return float(peso_str)

        match2 = re.search(r"(\d+)", limpa)
        if match2:
            gramas = int(match2.group(1))
            peso_float = gramas / 1000.0
            logger.info(f"Peso em gramas: {gramas} -> {peso_float:.3f} Kg")
            return peso_float

        raise BalancaRespostaError(f"Resposta invalida: {repr(resposta)}")
