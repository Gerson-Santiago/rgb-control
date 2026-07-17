# Pipeline Reference: run_tests.sh — novos arquivos de teste precisam de `git add` (Gate 0 bloqueia arquivos não rastreados).
import unittest
import os
from unittest.mock import patch, MagicMock, mock_open
from rgb_control.backend import Backend


class TestApplyColorResilience(unittest.TestCase):
    """
    Testa a resiliência do método apply_color() do Backend em cenários de falha
    de subprocesso, indisponibilidade do openrgb e corrupção do color_file.
    """

    def setUp(self) -> None:
        self.backend = Backend()

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_apply_color_all_attempts_fail_no_crash(
        self, mock_popen: MagicMock, mock_run: MagicMock
    ) -> None:
        """
        Quando openrgb falha nas 3 tentativas (returncode != 0), apply_color
        NÃO deve lançar exceção e deve tentar o pkexec como último recurso.
        """
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        # Não deve levantar exceção
        with patch("builtins.open", mock_open()):
            self.backend.apply_color("#FF0000", "Vermelho")

        # Verifica que tentou as 3 variantes
        self.assertEqual(mock_run.call_count, 2)  # tentativa 1 e 2
        mock_popen.assert_called_once()            # tentativa 3 via pkexec

    @patch("subprocess.run", side_effect=OSError("openrgb not found"))
    @patch("subprocess.Popen")
    def test_apply_color_subprocess_exception_no_crash(
        self, mock_popen: MagicMock, mock_run: MagicMock
    ) -> None:
        """
        Quando subprocess.run lança OSError (binário não encontrado),
        apply_color NÃO deve propagar a exceção para o caller.
        """
        with patch("builtins.open", mock_open()):
            # Não deve levantar exceção
            try:
                self.backend.apply_color("#00FF00", "Verde")
            except Exception as e:
                self.fail(f"apply_color não deveria lançar exceção, mas lançou: {e}")

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    def test_apply_color_black_uses_off_mode_without_color_arg(
        self, mock_popen: MagicMock, mock_run: MagicMock
    ) -> None:
        """
        Para a cor '#000000' (desligar LEDs), o modo deve ser 'off'
        e o argumento '--color' NÃO deve ser incluído na chamada.
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch("builtins.open", mock_open()):
            self.backend.apply_color("#000000", "Desativar")

        first_call_args = mock_run.call_args_list[0][0][0]
        self.assertIn("off", first_call_args)
        self.assertNotIn("--color", first_call_args)

    @patch("subprocess.run")
    def test_apply_color_writes_color_file_on_success(
        self, mock_run: MagicMock
    ) -> None:
        """
        Mesmo com openrgb tendo sucesso, o color_file deve ser atualizado
        com o valor hexadecimal correto.
        """
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        m = mock_open()
        with patch("builtins.open", m):
            self.backend.apply_color("#0000FF", "Azul")

        # Verifica que escreveu no color_file
        written_calls = [
            call for call in m().write.call_args_list
        ]
        # Pelo menos um write com o valor hexadecimal
        all_written = "".join(str(c) for c in written_calls)
        self.assertIn("0000FF", all_written)

    def test_get_current_color_corrupted_file_returns_default(self) -> None:
        """
        Quando o color_file existe mas contém dados inválidos (não #RRGGBB),
        get_current_color deve retornar a cor padrão de fábrica (#FF0000).
        """
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="NOT_A_COLOR")):
                result = self.backend.get_current_color()
        self.assertEqual(result, "#FF0000")

    def test_get_current_color_file_too_short_returns_default(self) -> None:
        """
        Quando color_file contém um valor hexadecimal incompleto (ex: '#FFF'),
        get_current_color deve retornar o default '#FF0000'.
        """
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="#FFF")):
                result = self.backend.get_current_color()
        self.assertEqual(result, "#FF0000")

    def test_get_current_color_no_file_returns_default(self) -> None:
        """
        Quando color_file não existe, get_current_color deve retornar '#FF0000'.
        """
        with patch("os.path.exists", return_value=False):
            result = self.backend.get_current_color()
        self.assertEqual(result, "#FF0000")

    def test_set_led_mode_with_invalid_pid_no_crash(self) -> None:
        """
        Quando o PID_FILE contém texto não numérico, set_led_mode não deve
        lançar exceção — a falha deve ser capturada e logada silenciosamente.
        """
        def exists_side_effect(path: str) -> bool:
            return True  # status_file e PID_FILE existem

        with patch("os.path.exists", side_effect=exists_side_effect):
            with patch("builtins.open", mock_open(read_data="NOT_A_PID")):
                try:
                    self.backend.set_led_mode(True)
                except Exception as e:
                    self.fail(
                        f"set_led_mode não deveria lançar exceção com PID inválido, mas lançou: {e}"
                    )

    def test_set_led_mode_no_pid_file_writes_status_only(self) -> None:
        """
        Quando PID_FILE não existe, set_led_mode deve escrever o status_file
        mas NÃO tentar enviar sinal SIGUSR1.
        """
        def exists_side_effect(path: str) -> bool:
            # status_file existe (para abrir escrita), PID_FILE não existe
            return path == self.backend.status_file

        m = mock_open()
        with patch("os.path.exists", side_effect=exists_side_effect):
            with patch("builtins.open", m):
                with patch("os.kill") as mock_kill:
                    self.backend.set_led_mode(True)
                    mock_kill.assert_not_called()

        m.assert_called_once_with(self.backend.status_file, "w")


if __name__ == "__main__":
    unittest.main()
