"""
Bateria de Testes Automatizados de Sanidade & Integridade do Radar Ceará.

O que faz:
    1. Testa se todos os módulos ativos de scripts/ podem ser importados sem erros de sintaxe ou dependências ausentes;
    2. Valida a consistência de constantes essenciais (ex: MODELO_GEMINI em config.py);
    3. Confere a integridade estrutural e o schema mínimo do payload 'site/radar_ce.json'.
"""

import json
import sys
import unittest
from pathlib import Path

# Garante scripts/ no PYTHONPATH durante a execução dos testes
RAIZ_PROJETO = Path(__file__).resolve().parent.parent.parent
DIR_SCRIPTS = RAIZ_PROJETO / "scripts"
if str(DIR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DIR_SCRIPTS))


class TestSanidadeModulos(unittest.TestCase):
    """Bateria A: Testa a importação limpa de todos os módulos de produção."""

    def test_importar_config(self):
        import config

        self.assertTrue(hasattr(config, "MODELO_GEMINI"))
        self.assertEqual(config.MODELO_GEMINI, "gemini-3.5-flash-lite")

    def test_importar_coletores(self):
        import coletores.google_trends as gt
        import coletores.instagram_apify as ig
        import coletores.meta_ads as meta
        import coletores.youtube as yt

        self.assertTrue(callable(gt.coletar_trends_ceara))
        self.assertTrue(callable(ig.coletar_comentarios_instagram_apify))
        self.assertTrue(callable(meta.coletar_meta_ads_ce))
        self.assertTrue(callable(yt.atualizar_videos_youtube))

    def test_importar_inteligencia(self):
        import inteligencia.gemini as gem
        import inteligencia.radar_tatico as rad

        self.assertTrue(callable(gem.processar_sentimento_comentarios))
        self.assertTrue(callable(rad.gerar_insights_radar_tatico_yt))
        self.assertTrue(callable(rad.gerar_insights_radar_tatico_ig))

    def test_importar_executaveis(self):
        import atualizar_trends_isolado
        import gerar_radar_ce

        self.assertTrue(callable(gerar_radar_ce.main))
        self.assertTrue(callable(atualizar_trends_isolado.atualizar_trends_isolado))


class TestArquivosAlvosEConfig(unittest.TestCase):
    """Bateria B: Garante a existência e integridade dos arquivos de alvos cadastrados."""

    def test_alvos_youtube(self):
        caminho_yt = RAIZ_PROJETO / "dados" / "canais_youtube_ce.txt"
        self.assertTrue(caminho_yt.exists(), "Arquivo canais_youtube_ce.txt deve existir.")
        with open(caminho_yt, "r", encoding="utf-8") as f:
            canais = [linha.strip() for linha in f if linha.strip() and not linha.strip().startswith("#")]
        self.assertGreaterEqual(len(canais), 20, "Deve haver pelo menos 20 canais de YouTube ativos monitorados.")

    def test_alvos_instagram(self):
        caminho_ig = RAIZ_PROJETO / "dados" / "perfis_instagram.txt"
        self.assertTrue(caminho_ig.exists(), "Arquivo perfis_instagram.txt deve existir.")
        with open(caminho_ig, "r", encoding="utf-8") as f:
            perfis = [linha.strip() for linha in f if linha.strip().startswith("@")]
        self.assertGreaterEqual(len(perfis), 15, "Deve haver pelo menos 15 perfis do Instagram ativos monitorados.")


class TestIntegridadePayloadSite(unittest.TestCase):
    """Bateria C: Garante que o payload central consumido pela SPA (radar_ce.json) é válido e íntegro."""

    def test_schema_radar_ce_json(self):
        caminho_json = RAIZ_PROJETO / "site" / "radar_ce.json"
        self.assertTrue(caminho_json.exists(), "O arquivo 'site/radar_ce.json' deve existir.")

        with open(caminho_json, "r", encoding="utf-8") as f:
            dados = json.load(f)

        # Chaves de nível raiz
        chaves_obrigatorias = [
            "titulo",
            "gerado_em",
            "versao",
            "radar_tatico_youtube",
            "radar_tatico_instagram",
            "monitor_redes",
            "sentimento_youtube",
            "sentimento_instagram",
        ]
        for chave in chaves_obrigatorias:
            self.assertIn(chave, dados, f"Chave raiz '{chave}' ausente no payload 'site/radar_ce.json'.")

        # Validação do radar tático
        for rede in ["radar_tatico_youtube", "radar_tatico_instagram"]:
            bloco = dados[rede]
            self.assertIn("status_dominio", bloco)
            self.assertIn(bloco["status_dominio"], ["DOMINANDO", "EQUILIBRADO", "SOB_PRESSAO", "ANALISANDO"])
            self.assertIn("alerta_imediato", bloco)
            self.assertIn("diretriz_estrategica_24h", bloco)

        # Validação do Google Trends
        trends = dados["monitor_redes"].get("google_trends_ce", {})
        self.assertIn("itens_4h", trends)
        self.assertIn("itens_24h", trends)
        self.assertIsInstance(trends.get("termos_socioeconomicos_ceara"), list)


if __name__ == "__main__":
    unittest.main()
