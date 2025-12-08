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
