# Ativar deploy por Watchtower

## Fluxo

O CD constrói uma imagem uma vez e publica o SHA. Promove o digest para
`:staging`, espera Watchtower atualizar e verifica `/health`, `/version` (SHA
exato) e `/cafes` (seed). A produção exige aprovação no GitHub Environment e
recebe o MESMO digest via tag `:production`. Nenhuma reconstrução ocorre na
promoção. As tags de canal são móveis; o artefato selecionado é identificado
por digest. CD, rollback e preparação usam o mesmo grupo de concorrência.

## 1. Preparar os canais no GHCR

Depois do merge desta alteração na main, abra **Actions → prepare-watchtower →
Run workflow**, escolha `main` e aprove o environment `production`.
Isso cria `:staging` e `:production` apontando para a imagem baseline que já
foi implantada manualmente, versão `abc12a0`. Não constrói imagem nem altera
banco. Recusa executar se algum dos canais já existir. Execute uma única vez.

## 2. Ajustar o Watchtower que já existe no MangaHub

No serviço `watchtower` do app MangaHub, mantenha os parâmetros atuais e adicione:

```yaml
    command:
      # mantenha os outros argumentos existentes
      - --scope
      - none
```

Não cole esse fragmento substituindo toda a lista: acrescente os dois argumentos.
`none` mantém o monitoramento dos containers sem scope do MangaHub e permite
coexistir com as instâncias separadas do Café. Não crie outro Watchtower sem
scope: instâncias sem scope podem parar as outras instâncias.

## 3. Editar os apps existentes do Café no TrueNAS

- No app staging, use [deploy/truenas-staging-watchtower.yml](deploy/truenas-staging-watchtower.yml).
- No app produção, use [deploy/truenas-production-watchtower.yml](deploy/truenas-production-watchtower.yml).
- Substitua as DUAS ocorrências de `REPLACE_WITH_RANDOM_PASSWORD` pela senha
  **já utilizada naquele banco**. Mudar POSTGRES_PASSWORD não altera a senha
  de um banco já inicializado. Não recrie apps, volumes nem o serviço `db`.
- Preserve o nome atual de cada app, o serviço `db` e o volume `pgdata`.
- Os arquivos incluem Watchtower com escopos separados, polling de 30 segundos
  e acesso ao Docker socket para recriar somente as APIs selecionadas por label.
  Banco e túnel não são selecionados para atualização automática.
- Guarde o YAML preenchido somente no NAS; não publique senhas no GitHub.

As imagens de canal devem existir ANTES desta etapa. Observe os logs do serviço
Watchtower: ele deve selecionar a API sem erros de conexão ao Docker/registro.
Se sua versão do Docker rejeitar o cliente Watchtower, não habilite promoção;
registre o erro para ajustar a compatibilidade antes de continuar.

## 4. Conferir URLs

Editar o app pode recriar o túnel temporário. Copie o endereço atual dos logs
de cada `cloudflared` e confira `/health`, `/version` e `/cafes`.
No GitHub, abra **Settings → Environments → staging / production → Environment
variables** e atualize `APP_URL` se mudou. Atualize também os links no README.

## 5. Habilitar e testar o pipeline

Em **Settings → Secrets and variables → Actions → Variables**, crie a variável
de repositório `WATCHTOWER_ENABLED` com valor `true`.
Abra **Actions → cd → Run workflow → main**.

1. O CI e build devem passar.
2. Staging deve atualizar em aproximadamente um ciclo de polling e passar nos
   smoke tests. O job espera até cerca de 12 minutos, permitindo inicialização.
3. Em **Review deployments**, aprove `production`.
4. Confira produção com o SHA novo e o workflow concluído.

Se um smoke test falhar, o job falha; produção não recebe a imagem quando staging
falha. Se produção falhar após promoção, dispare rollback. Isso não é um rollback
automático. Desabilitar `WATCHTOWER_ENABLED` impede futuras promoções pelos
workflows, mas não desfaz uma tag que já foi publicada.

## 6. Demonstrar rollback

Abra **Actions → rollback → Run workflow → main**, informe o SHA anterior
(`abc12a0` é a baseline inicial), aprove produção e observe `/version` retornar
ao SHA antigo. O workflow resolve o digest publicado, move somente `:production`
e verifica a recuperação. O banco e as migrations permanecem.

Se houver CD esperando aprovação, cancele esse CD antes de um rollback urgente:
o grupo de concorrência mantém uma operação de deploy/rollback por vez.
Pause novos merges até confirmar a recuperação. O concorrente pendente mais
recente pode substituir outro pendente na fila padrão do GitHub.

Registre os horários reais para DORA e vídeo. Esta implementação só estará
validada ponta a ponta após observar os dois ambientes atualizarem pelo Watchtower.

Fontes: [Watchtower scopes](https://containrrr.dev/watchtower/running-multiple-instances/),
[promoção preservando manifesto](https://docs.docker.com/reference/cli/docker/buildx/imagetools/create/).
