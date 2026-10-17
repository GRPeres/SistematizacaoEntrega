# TrueNAS SCALE: implantação do projeto acadêmico

Repositório: https://github.com/GRPeres/SistematizacaoEntrega
Imagem: `ghcr.io/grperes/sistematizacaoentrega`

## Estado atual

O código está publicado. O workflow CD valida e publica a imagem no GHCR.
As etapas antigas do Render estão desabilitadas. **Automação de deploy no NAS,
aprovação e rollback pelo Actions ainda precisam ser configurados e executados.**
Não ative `DEPLOY_TARGET=render` para este destino.

## Interface TrueNAS

Use Apps → Discover Apps → Install via YAML. Crie dois aplicativos separados:
`cafe-staging` e `cafe-production`. Não altere o app MangaHub.
O arquivo `deploy/truenas-quick.yml` é um modelo para cada aplicativo.
Antes de colar no TrueNAS:

1. Substitua `REPLACE_WITH_IMAGE_DIGEST` pelo digest real publicado no GHCR.
2. Substitua as DUAS ocorrências de `REPLACE_WITH_RANDOM_PASSWORD` pela mesma
   senha aleatória alfanumérica, diferente entre staging e produção.
3. Instale primeiro staging. Confirme `/health`, `/version` e `/cafes` na URL do
   túnel, e compare `/version` com o SHA do build.
4. Após aprovação, instale produção usando o MESMO digest aprovado em staging.

Cada app tem PostgreSQL, rede e volume próprios. O banco não publica porta.
O túnel liga diretamente à API na rede Docker. O build atual exige CPU x86-64.
A imagem GHCR deve ser pública ou o TrueNAS deve autenticar no registro.

O serviço cloudflared imprime nos logs uma URL `https://...trycloudflare.com`.
Use essa URL em `/docs` para a documentação interativa da API.
Não exige conta, domínio nem token Cloudflare. A URL muda se o túnel for
recriado e não tem garantia de disponibilidade. Atualize README, GitHub
Environment e PDF da entrega se mudar. Não há hostname estável gratuito
configurado neste projeto.

## Alternativa: Compose CLI no NAS

Crie `.env.staging` e `.env.production` privados no NAS com os campos abaixo:

```dotenv
APP_IMAGE=ghcr.io/grperes/sistematizacaoentrega@sha256:REPLACE_WITH_IMAGE_DIGEST
DB_PASSWORD=REPLACE_WITH_RANDOM_PASSWORD
APP_PORT=8001
BIND_ADDRESS=127.0.0.1
```

Produção usa outra senha e porta 8002. Execute na pasta dos arquivos Compose:

```sh
docker compose --env-file .env.staging -p cafe-staging -f compose.nas.yml -f compose.quick-tunnel.yml pull
docker compose --env-file .env.staging -p cafe-staging -f compose.nas.yml -f compose.quick-tunnel.yml up -d
docker compose --env-file .env.staging -p cafe-staging -f compose.nas.yml -f compose.quick-tunnel.yml logs cloudflared
curl --fail http://127.0.0.1:8001/health
curl --fail http://127.0.0.1:8001/version
```

Repita para produção somente após validar staging. Use apenas um método de
gerenciamento por ambiente; não misture alterações na interface com Compose CLI
sobre os mesmos containers. Guarde arquivos privados com permissão restrita.

## Rollback e dados

Restaure o digest anterior conhecido no app de produção, atualize e confirme
`/health` e `/version`. Não reconstrua a imagem. Não use Watchtower nesta API:
aprovação e rollback exigem versões explícitas. Migrations são executadas na
inicialização; rollback da aplicação não desfaz migrations. Faça backup do banco
antes de mudanças de esquema e nunca execute `down -v` nesses ambientes.
A migration 0003 deve entrar somente após o primeiro deploy real de produção.

## Evidências para a entrega

Ainda é necessário registrar: PR com CI PostgreSQL verde, checks obrigatórios,
aprovação humana, deploy/rollback automatizados, migration 0003 após produção,
PR Dependabot revisado, release, métricas DORA reais, vídeo e PDF individual.
Um build verde não comprova essas etapas.

Fontes: [TrueNAS Custom Apps](https://apps.truenas.com/managing-apps/installing-custom-apps/),
[Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

## Verificação dos ambientes em 17/10/2026

- Staging: https://carl-wait-cingular-holder.trycloudflare.com
- Produção: https://fonts-sacramento-nations-reflection.trycloudflare.com
- Ambos responderam HTTP 200 em `/health`, `/version` e `/cafes` (cinco cafés).
- Versão reportada por ambos: `abc12a0c08466102be2451a492b6b7bf71bf669f`.
- As variáveis `APP_URL` foram registradas nos GitHub Environments correspondentes.
- Esta verificação comprova disponibilidade e versão, mas não confirma isolamento
  dos volumes/bancos nem execução automatizada do deploy pelo GitHub Actions.
