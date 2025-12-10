from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

USER_API_URL = "http://users-api:8001/graphql"
VIACEP_URL = "https://viacep.com.br/ws/{cep}/json/"


@app.post("/usuario")
async def criar_usuario(nome: str, email: str, cep: str):
    async with httpx.AsyncClient() as client:
        via_cep_resp = await client.get(VIACEP_URL.format(cep=cep))

    if via_cep_resp.status_code != 200:
        raise HTTPException(400, "Erro ao consultar ViaCEP")

    via_cep_data = via_cep_resp.json()

    if "erro" in via_cep_data:
        raise HTTPException(404, "CEP não encontrado no ViaCEP")

    logradouro = via_cep_data.get("logradouro")
    bairro = via_cep_data.get("bairro")
    cidade = via_cep_data.get("localidade")
    estado = via_cep_data.get("uf")

    mutation = """
        mutation CreateUser(
        $nome: String!,
        $email: String!,
        $cep: String!,
        $logradouro: String!,
        $bairro: String!,
        $cidade: String!,
        $estado: String!
        ) {
        createUser(
            nome: $nome,
            email: $email,
            cep: $cep,
            logradouro: $logradouro,
            bairro: $bairro,
            cidade: $cidade,
            estado: $estado
        ) {
            id
            nome
            email
            address {
            cep
            logradouro
            bairro
            cidade
            estado
            }
        }
        }
    """

    variables = {
        "nome": nome,
        "email": email,
        "cep": cep,
        "logradouro": logradouro,
        "bairro": bairro,
        "cidade": cidade,
        "estado": estado
    }

    if not all([logradouro, bairro, cidade, estado]):
        raise HTTPException(400, "CEP retornou dados incompletos")

    async with httpx.AsyncClient() as client:
        gql_resp = await client.post(USER_API_URL, json={"query": mutation, "variables": variables})

    data = gql_resp.json()

    if "errors" in data:
        raise HTTPException(500, data["errors"])

    return data["data"]["createUser"]

@app.get("/usuarios")
async def listar_usuarios(page: int = 1, per_page: int = 10):
    query = """
    query Users($page: Int!, $perPage: Int!) {
      usersPaginated(page: $page, perPage: $perPage) {
        items {
          id
          nome
          email
          address {
            cep
            logradouro
            bairro
            cidade
            estado
          }
        }
        page
        perPage
        total
        totalPages
      }
    }
    """

    variables = {
        "page": page,
        "perPage": per_page
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            USER_API_URL,
            json={"query": query, "variables": variables}
        )

    data = response.json()

    if "errors" in data:
        raise HTTPException(500, data["errors"])

    return data["data"]["usersPaginated"]

@app.get("/usuarios/{user_id}")
async def buscar_usuario(user_id: int):
    query = """
    query UserById($id: Int!) {
      userById(id: $id) {
        id
        nome
        email
        address {
          cep
          logradouro
          bairro
          cidade
          estado
        }
      }
    }
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            USER_API_URL,
            json={"query": query, "variables": {"id": user_id}}
        )

    data = response.json()

    if "errors" in data:
        raise HTTPException(404, "Usuário não encontrado")

    return data["data"]["userById"]

@app.put("/usuarios/{user_id}")
async def atualizar_usuario(
    user_id: int,
    nome: str,
    email: str
):
    mutation = """
    mutation UpdateUser($id: Int!, $nome: String!, $email: String!) {
      updateUser(id: $id, nome: $nome, email: $email) {
        id
        nome
        email
      }
    }
    """

    variables = {
        "id": user_id,
        "nome": nome,
        "email": email
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            USER_API_URL,
            json={"query": mutation, "variables": variables}
        )

    data = response.json()

    if "errors" in data:
        raise HTTPException(400, data["errors"])

    return data["data"]["updateUser"]

@app.delete("/usuarios/{user_id}")
async def deletar_usuario(user_id: int):
    mutation = """
    mutation DeleteUser($id: Int!) {
      deleteUser(id: $id) {
        id
        nome
        email
      }
    }
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            USER_API_URL,
            json={"query": mutation, "variables": {"id": user_id}}
        )

    data = response.json()

    if "errors" in data:
        raise HTTPException(400, data["errors"])

    return {
        "message": "Usuário removido com sucesso",
        "usuario_removido": data["data"]["deleteUser"]
    }

