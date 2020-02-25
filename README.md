# Desafio Noverde
Código para o desafio Noverde. Link para o desafio: https://github.com/noverde/challenge

## Como executar:
É necessário ter o AWS CLI e o SAM Framework CLI instalados na maquina.

Download do AWS Cli: https://aws.amazon.com/pt/cli/

Download do SAM Framework CLI: https://aws.amazon.com/serverless/sam/

Apos instalar os dois, rode o comando `aws configure` e adicione os tokens de alguma conta de servico da AWS.

Antes de fazer o build da aplicação, adicione um valor para a X_API_KEY na ***Linha 87*** do arquivo template.yaml

Para fazer o build e deploy da aplicação use os comandos:
`sam build`
seguido de 
`sam deploy --guided` (na primeira vez, após isso pode executar sem o --guided)

No output do terminal, após o comando de `sam deploy` aparecerão as urls das APIS, para fazer o teste.

## Fluxo
Ao fazer um POST, é criado um registro no DynamoDB com os dados enviados (após validação), neste momento também é inserida uma mensagem na fila, com o ID do registro. Esse mesmo ID é enviado como resposta da requisição.

Uma lambda é ativada quando uma mensagem é colocada na fila e essa lambda é a responsável por fazer a validação da Política de Crédito.

Outra lambda é responsável por fazer a consulta dos dados.
