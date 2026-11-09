# Radar de pontos Livelo

Página pública com a pontuação dos parceiros Livelo e as promoções do dia, com filtros e ordenação por coluna. Abre sem login.

Os dados vêm da página pública de parceiros da Livelo. Este projeto não tem ligação oficial com a Livelo.

## Como funciona

- `index.html`: a página. Lê `dados.json` ao abrir.
- `dados.json`: os parceiros, as categorias e as pontuações.
- `scripts/atualizar.py`: busca as pontuações em livelo.com.br e regrava `dados.json`. As categorias já existentes são mantidas; parceiros novos entram como "Outros".
- `.github/workflows/atualizar.yml`: roda o script todo dia às 7h47 (horário de Brasília) e salva o resultado. Também pode ser disparado na hora.

## Configuração (uma vez)

1. Suba estes arquivos num repositório (por exemplo `radar-livelo`), na branch `main`.
2. Em **Settings > Pages**, em "Build and deployment", escolha **Deploy from a branch**, branch `main`, pasta `/ (root)`, e salve. Em alguns minutos a página fica em `https://SEU-USUARIO.github.io/radar-livelo/`.
3. Em **Settings > Actions > General**, em "Workflow permissions", marque **Read and write permissions** e salve. Sem isso, a rotina não consegue salvar os dados novos.
4. Em **Actions**, abra "Atualizar pontuações" e clique em **Run workflow** para testar.

## Atualizar na hora

Em **Actions > Atualizar pontuações > Run workflow**. Só quem tem acesso de escrita ao repositório vê esse botão. A página também mostra um link para lá.

## Se a rotina falhar

A Livelo pode mudar o layout da página de parceiros. Quando o script lê menos de 80% dos parceiros esperados, ele não altera nada e a rotina aparece com erro em Actions. A página continua no ar com os últimos dados. Aí o script precisa de ajuste.

Para mudar o horário, edite a linha `cron` em `.github/workflows/atualizar.yml` (o horário é em UTC; 10:47 UTC = 7:47 em Brasília).
