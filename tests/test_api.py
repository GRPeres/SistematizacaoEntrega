"""Testes de integração API + banco (PostgreSQL no CI)."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version(client, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "abc1234")
    assert client.get("/version").json() == {"version": "abc1234"}


def test_lista_inicial_vazia(client):
    assert client.get("/cafes").json() == []


def test_cria_e_lista_cafe(client):
    response = client.post("/cafes", json={"nome": "Bourbon Amarelo", "preco": "21.90"})
    assert response.status_code == 201
    assert response.json()["nome"] == "Bourbon Amarelo"
    assert response.json()["origem"] == "Não informada"
    assert len(client.get("/cafes").json()) == 1


def test_busca_por_id(client):
    id_cafe = client.post("/cafes", json={"nome": "Catuaí", "preco": "12.50"}).json()["id"]
    assert client.get(f"/cafes/{id_cafe}").json()["nome"] == "Catuaí"


def test_retorna_404_para_cafe_inexistente(client):
    assert client.get("/cafes/999").status_code == 404
    assert client.get("/cafes/999/preco").status_code == 404


def test_preco_com_desconto(client):
    id_cafe = client.post("/cafes", json={"nome": "Arara", "preco": "20.00"}).json()["id"]
    response = client.get(f"/cafes/{id_cafe}/preco?desconto=10")
    assert response.status_code == 200
    assert response.json()["preco_final"] == 18.0


def test_desconto_acima_do_limite_e_rejeitado(client):
    id_cafe = client.post("/cafes", json={"nome": "Acauã", "preco": "20.00"}).json()["id"]
    assert client.get(f"/cafes/{id_cafe}/preco?desconto=80").status_code == 422


def test_duplicidade_retorna_409(client):
    payload = {"nome": "Mundo Novo", "preco": "18.50"}
    assert client.post("/cafes", json=payload).status_code == 201
    assert client.post("/cafes", json=payload).status_code == 409


def test_valida_preco_positivo(client):
    assert client.post("/cafes", json={"nome": "Teste", "preco": -5}).status_code == 422


def test_valida_nome_curto(client):
    assert client.post("/cafes", json={"nome": "X", "preco": 12}).status_code == 422
