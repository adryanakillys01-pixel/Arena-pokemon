# Arena Pokémon — multiplayer (versão 1)

Projeto de fã não oficial, em português. Dois jogadores em navegadores separados, com um servidor Python compartilhado. Não exige dependências Python externas.

## Jogar na mesma rede Wi-Fi
1. Instale Python 3.10 ou mais recente no computador que hospedará a partida.
2. Extraia o ZIP e abra um terminal na pasta `arena-pokemon`.
3. Execute `python server.py` (ou `python3 server.py`).
4. No computador, descubra o endereço IPv4 local (`ipconfig` no Windows; `ip addr` no Linux; Ajustes de Rede no macOS).
5. Nos dois celulares conectados à mesma rede Wi-Fi, abra `http://IP-DO-COMPUTADOR:8000` no navegador. Se necessário, permita conexões locais na porta 8000 no firewall. Não exponha essa porta à internet diretamente.
6. Um jogador cria a sala e o outro entra com o código. Cada um escolhe três Pokémon, sendo o primeiro o inicial. Os ataques ficam secretos até os dois confirmarem.

## Publicar no Render
1. Crie um repositório GitHub novo e envie o conteúdo desta pasta (server.py, index.html, requirements.txt, render.yaml, README.md e .gitignore).
2. No Render, crie um Web Service a partir desse repositório. Escolha ambiente Python, build `pip install -r requirements.txt` e start `python server.py`. A configuração render.yaml também pode ser usada como Blueprint. Confira plano e custos antes de criar.
3. Depois que a implantação estiver disponível, abra a URL HTTPS fornecida pelo Render nos dois celulares.

O servidor usa a variável PORT fornecida pelo provedor. O arquivo rooms.json contém estado e tokens privados; NÃO envie esse arquivo ao GitHub. O armazenamento padrão do Render pode ser efêmero: para preservar partidas após reinícios e deploys, configure armazenamento persistente compatível e ARENA_DATA apontando para o arquivo dentro desse armazenamento. Use somente uma instância de servidor nesta versão. Não há autenticação por senha nem proteção de produção contra abusos; compartilhe códigos apenas com os participantes.

## Implementado
- 23 Pokémon pré-configurados e 63 golpes cadastrados.
- 3 contra 3, nível 50, natureza neutra, 31 IVs e zero EVs.
- Sala de dois jogadores; equipes e ações ocultas antes de confirmar; validação no servidor.
- Dano, tipos, velocidade, prioridade, críticos, estados, trocas, atributos, algumas habilidades, cura e recuo.
- Registro de combate, revanche, placar da sala, estado salvo localmente no servidor.
- Imagens carregadas do acervo PokeAPI sprites (precisam de internet); ícone de reserva caso falhem.

## Limitações
O motor é simplificado, não é uma implementação integral das regras oficiais de todas as gerações. Não inclui PP, itens, todas as habilidades e efeitos (ex.: Cursed Body), transformações especiais, estratégias livres do anime, nem seleção manual do substituto de U-turn (usa a primeira reserva disponível). Nó de Grama tem poder fixo. Golpes e atributos são pré-configurados. A lógica encerra a partida quando o último Pokémon cai, antes dos efeitos residuais, conforme o regulamento usado nesta conversa. O placar começa em 0 × 0 para cada sala nova. Não importa automaticamente as partidas anteriores do chat. Fechar a página e voltar no mesmo navegador conserva a sessão; se apagar os dados do navegador, não há recuperação do token. O servidor local é destinado a uso privado.

## Verificação
Python e JavaScript passaram na validação de sintaxe. Teste automatizado direto das funções do servidor passou por criação/entrada na sala, sigilo de equipe e ataque, resolução de turnos, substituição, vitória, revanche e gravação do placar. Não foi possível verificar o transporte HTTP nem a apresentação em dois celulares neste ambiente. A publicação online ainda não foi realizada.
