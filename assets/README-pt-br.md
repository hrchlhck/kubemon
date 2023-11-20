# kubemon
Uma ferramenta para monitoramento de containers distribuídos no Kubernetes.

## Sumário
- [Citação](#citação)
- [Dependências de Ambiente](#dependências-de-ambiente)
- [Dependências de Aplicação](#dependências-de-aplicação)
- [Diagramas](#diagramas)
- [Principais Funcionalidades](#principais-funcionalidades)
- [Instalação](#instalaçao)
- [Executando](#executando)
    - [Collector](#collector)
    - [Monitor](#monitor)
    - [CLI](#cli)
- [Referências](#referencias)

## Citação
```bibtex
@article{Kubemon2023,
    title = {Kubemon: extrator de métricas de desempenho de sistema operacional e aplicações conteinerizadas em ambientes de nuvem no domínio do provedor},
    year = {2023},
    author = {Pedro Horchulhack and Eduardo K. Viegas and Altair O. Santin and Felipe V. Ramos},
}
```

## Dependências de Ambiente
- Ubuntu 18.04
- Kubernetes v1.19
- Docker v.19.03.13
- Python 3.8
- make

## Dependências de Aplicação
- [psutil](https://github.com/giampaolo/psutil)
- [requests](https://github.com/psf/requests)
- [addict](https://github.com/mewwts/addict)
- [docker-py](https://github.com/docker/docker-py)
- [sty](https://github.com/feluxe/sty)
- [virtualenv](https://github.com/pypa/virtualenv)

## Diagramas
Diagrama simples da ferramenta. 
![Kubemon diagram](./diagram-pt.svg)

## Principais Funcionalidades
- Coleta métricas de sistema operacional, containers Docker e processos criados pelos containers
- Envia as métricas coletadas para o módulo ```collector```, que salva em um arquivo CSV
- Pode ser controlada remotamente por uma CLI básica

## Instalação
Antes de instalar a ferramenta, verifique se o Kubernetes e o Docker estão propriamente instalados no sistema. Além disso, a ferramenta deve ser baixada e extraída em todos os nós do cluster do Kubernetes para monitorar as métricas.

1. Baixe a última versão da ferramenta no link: [kubemon v2.0.0](https://github.com/hrchlhck/kubemon/archive/refs/tags/v2.0.0.zip) 

2. Extraia os arquivos do zip e entre no diretório

3. Crie um ambiente virtual do Python e ative-o
    ```sh
    $ python3 -m venv venv 
    $ source venv/bin/activate
    ```
4. Instale as dependências
    ```sh 
    (venv) $ pip install .
    ```

## Executando
As métricas coletadas serão salvas na máquina do ```cliente``` (Veja [Cliente](#diagrama) no diagrama) por padrão no diretório ```/tmp/data```. Essa configuração pode ser alterada no arquivo ```./kubemon/constants.py``` trocando o valor da variável ```ROOT_DIR```.

Exemplo: 
```python
# Antes
ROOT_DIR = "/tmp/data"

# Depois
ROOT_DIR = "/home/user/Documents/data"
```

Nas próximas seções será abordado como executar cada módulo da ferramenta.

Lista de comandos disponíveis:
```sh
usage: kubemon [-h] [-l] [-t TYPE] [-H IP] [-p PORT] [-f FILE1 FILE2] [-c [COMMAND ...]] [-i INTERVAL]

Comandos do Kubemon 

Comandos opcionais:
  -h, --help            show this help message and exit
  -l, --list            Lista os módulos existentes
  -t TYPE, --type TYPE  Funcionalidade do Kubemon. E.g. collector, monitor, docker...
  -H IP, --host IP      Endereço IP do módulo collector executando
  -p PORT, --port PORT  Porta do módulo collector (por padrão é 9822)
  -f FILE1 FILE2, --files FILE1 FILE2 Arquivos para juntar
  -c [COMMAND ...], --command [COMMAND ...]
                        Comando para ser executado pelo módulo CollectorClient
  -i INTERVAL, --interval INTERVAL
                        Janela de tempo para coleta de dados (por padrão é 5)
```
### Collector
```sh
(venv) $ make collector
[ Collector ] Started collector CLI at 0.0.0.0:9880
[ Collector ] Started collector at 0.0.0.0:9822
```

### Monitor
Assuming that the collector IP is ```192.168.0.3```, let's connect the monitors to it.

Assumindo que o IP do módulo ```collector``` é ```192.168.0.3```, podemos conectar os monitores com os comandos a seguir.

Existem três tipos de monitores:
1. OSMonitor - Coleta métricas de Sistema Operacional
2. DockerMonitor - Coleta métricas de containers Docker
3. ProcessMonitor - Coleta métricas de processos criados por containers

**A ferramenta deve ser executada com ```sudo```, porque algumas métricas estão disponíveis somente para usuários privilegiados.**

Neste caso, para executar os três monitores:
```sh
(venv) $ sudo python -m kubemon -t all -H 192.168.0.3
Connected OSMonitor_192_168_0_3_node_0 monitor to collector
...
```

### CLI
Assumindo o mesmo IP na seção [Monitor](#monitor), a porta para comunicação com o ```collector``` via CLI é ```9880```.

Até o momento existem os comandos:
1. ```/instances``` - Quantidade de instâncias ```monitor``` conectadas ao módulo ```collector```.
2. ```/start <output_dir>``` - Inicia a coleta de métricas e salva no diretório ```output_dir``` definido pelo usuário.

### Checando quantas instâncias ```monitor``` estão conectadas
```sh
(venv) $ python -m kubemon -t cli -H 192.168.0.3 -c /instances
Connected instances: 5
```

### Iniciando os monitores. Neste caso, os arquivos CSV serão salvos no caminho ```/tmp/data/test00/```
```sh
(venv) $ python -m kubemon -t cli -H 192.168.0.3 -c /start "test00"
Started 5 monitors
```

## Referências
- [Block layer statistics](https://www.kernel.org/doc/html/latest/block/stat.html)
- [/proc virtual file system](https://man7.org/linux/man-pages/man5/proc.5.html)
- [Evaluation of desktop operating systems under thrashing conditions](https://journal-bcs.springeropen.com/track/pdf/10.1007/s13173-012-0080-8.pdf)
- [cgroups](https://www.man7.org/linux/man-pages/man7/cgroups.7.html)
- [Docker runtime metrics](https://docs.docker.com/config/containers/runmetrics/)
