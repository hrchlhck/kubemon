---
permalink: /pt-br/
---

# kubemon
Uma ferramenta para monitoramento de containers distribuídos no Kubernetes.

## Sumário
- [Dependências de Ambiente](#dependências-de-ambiente)
- [Dependências de Aplicação](#dependências-de-aplicação)
- [Diagramas](#diagramas)
- [Principais Funcionalidades](#principais-funcionalidades)
    - [Métricas coletadas](#métricas-coletadas)
- [Instalação](#instalacao)
- [Configuração](#configuracao)
- [Executando](#executando)
    - [Iniciando](#iniciando)
    - [Parando](#parando)
    - [Comandos](#todos-os-comandos)
- [Vídeo Demonstrativo](#video-demonstrativo)
- [Referências](#referencias)

## Dependências de Ambiente
- Ubuntu 18.04
- Kubernetes v1.19
- Docker v.19.03.13
- Python 3.8
- GNU Make 4.2.1

## Dependências de Aplicação
- [psutil](https://github.com/giampaolo/psutil)
- [Requisições](https://github.com/psf/Requisições)
- [docker-py](https://github.com/docker/docker-py)
- [virtualenv](https://github.com/pypa/virtualenv)
- [flask](https://github.com/pallets/flask)
- [flask_restfull](https://github.com/flask-restful/flask-restful)
- [gunicorn](https://github.com/benoitc/gunicorn)

## Diagramas
Diagrama simples da ferramenta. 
![Kubemon diagram](https://raw.githubusercontent.com/hrchlhck/kubemon/main/assets/diagram-pt.svg)

## Principais Funcionalidades
- Coleta métricas no domínio do provedor
- A coleta das métricas é realizada por pods do Kubernetes
- Pode ser configurado através de variáveis de ambientes do Kubernetes
- Coleta métricas de sistema operacional, contêineres Docker e processos criados pelos contêineres
- Envia as métricas coletadas para o componente ```coletor```, que salva os dados em um arquivo CSV
- Pode ser controlado remotamente por uma interface de linha de comando ou pela API do Python

### Métricas Coletadas
Para mais informações a respeito das métricas coletadas, por favor recorra a:
- Métricas de Sistema Operacional: Essas métricas são coletadas pelo pseudo-sistema de arquivos ```/proc``` e ```/sys/block/<dev>/stat``` do Linux usando a API ```psutil``` do Python.
    - CPU: [Miscellaneous kernel statistics in /proc/stat](https://www.kernel.org/doc/html/latest/filesystems/proc.html#miscellaneous-kernel-statistics-in-proc-stat)
    - Memória: [proc - process information pseudo-filesystem: /proc/vmstat](https://man7.org/linux/man-pages/man5/proc.5.html)
    - Disco : [Block layer statistics in /sys/block/\<dev\>/stat](https://www.kernel.org/doc/html/latest/block/stat.html#block-layer-statistics-in-sys-block-dev-stat)
    - Rede: [proc - process information pseudo-filesystem: /proc/net/dev](https://man7.org/linux/man-pages/man5/proc.5.html)
- Contêineres Docker: Tais métricas são coletadas pelo ```cgroups``` do Linux.
    - CPU: [cgroups - Linux control groups: cpu,cpuacct](https://www.man7.org/linux/man-pages/man7/cgroups.7.html)
    - Memória: [cgroups - Linux control groups: memory](https://www.man7.org/linux/man-pages/man7/cgroups.7.html)
    - Disco: [cgroups - Linux control groups: blkio](https://www.man7.org/linux/man-pages/man7/cgroups.7.html)
    - Rede: [proc - process information pseudo-filesystem: /proc/net/dev](https://man7.org/linux/man-pages/man5/proc.5.html)
- Processos Docker: Essas métricas são coletadas pelo pseudo-sistema de arquivos ```/proc``` do Linux usando a API ```psutil``` do Python.
    - CPU: [Miscellaneous kernel statistics in /proc/stat](https://www.kernel.org/doc/html/latest/filesystems/proc.html#miscellaneous-kernel-statistics-in-proc-stat)
    - Memória: [proc - process information pseudo-filesystem: /proc/vmstat](https://man7.org/linux/man-pages/man5/proc.5.html)
    - Disco: [Block layer statistics in /sys/block/\<dev\>/stat](https://www.kernel.org/doc/html/latest/block/stat.html#block-layer-statistics-in-sys-block-dev-stat)
    - Rede: [proc - process information pseudo-filesystem: /proc/net/dev](https://man7.org/linux/man-pages/man5/proc.5.html)

#### **Operating System**
|  Tipo   |  Unidade  | Métrica |
| ------- | --------- | ------ |
| CPU     | Quantidade <br> Quantidade <br> Quantidade <br> Quantidade <br> Ciclos <br> Ciclos <br> Ciclos <br> Ciclos <br> Ciclos <br> Ciclos <br> Ciclos <br> Ciclos <br> Ciclos <br> | Trocas de Contexto <br> Interrupções <br> Interrupções Soft <br> Chamadas de Sistema <br> Tempo do Usuário <br> Tempo do Sistema <br> Tempo Nice <br> Tempo Softirq <br> Tempo IRQ <br> Tempo de Espera de E/S <br> Tempo Guest <br> Tempo Guest Nice <br> Tempo em Ócio |
| Memória  | Quantidade <br> Quantidade <br> Quantidade <br> Quantidade <br> Quantidade <br> KB <br> KB <br> Quantidade <br> Quantidade <br> Quantidade <br> Quantidade <br> | Páginas Ativas (Anon) <br> Páginas Inativas (Anon) <br> Página Inativas (file) <br> Páginas Ativas (file) <br> Páginas Mapeadas <br> Páginas de Entrada desde o Boot (pgpgin) <br>  Páginas de Dsaída desde o Boot (pgpgout) <br> Páginas Livres (pgfree) <br> Falhas de Página (pgfault) <br> Falha de Página Rígida (pgmajfault) <br> Páginas Reusadas (pgreuse) |
| Disco    | Requisições <br> Requisições <br> Setores <br> Milisegundos <br> Requisições <br> Requisições <br> Setores <br> Milisegundos <br> Requisições <br> Milisegundos <br> Milisegundos <br> Requisições <br> Requisições <br> Setores <br> Milisegundos <br> Requisições <br> Milisegundos | Leitura E/S <br> Leitura E/S Merged com In-queue E/S <br> Setores Lidos <br> Tempo de Espera Total para Requisições de Leitura <br> Escrita E/S <br> Escrita E/S Merged com In-Queue E/S <br> Escrita Setores <br> Tempo Total de Espera para Requisições de Escrita <br> E/S em Flight <br> Tempo Total que o Bloco está Ativo <br> Tempo Total de Espera para Todas as Requisições <br> Descarte de E/S Processados  <br> Descarte de E/S Processados com In-Queue E/S <br> Setores Descartados <br> Tempo Total de Espera para Requisições de Descarte <br> Flush E/S Processados <br> Tempo Total de Espera para Requisições de Flush |
| Rede |  Bytes <br> Bytes <br> Pacotes <br> Pacotes  <br> Quantidade <br> Quantitade <br> Quantidade <br>  Quantidade <br> Quantidade <br> Quantidade <br> Quantidade | Enviados <br> Recebidos <br> Enviados <br> Recebidos <br> Total de erros de transmissão <br> Pacotes com erro de frame <br> Pacotes descartados <br> Pacotes comprimidos <br> Perdas de transmissão <br> Frames de Multicast <br> Número de Conexões |

#### **Docker Processes**
|  Type   |  Unit  | Metric |
| ------- | ------ | ------ |
| CPU     | Ciclos <br> Ciclos <br> Ciclos <br> Ciclos <br> Ciclos <br> | Tempo do Usuário <br> Tempo do Sistema <br> Tempo do Usuário dos Processos Filhos <br> Tempo do Sistema dos Processos Filhos <br> Tempo de Espera de E/S |
| Memória  | Páginas <br> Páginas <br> Páginas <br> Páginas <br> Páginas <br> | Tamanho total do programa (size) <br> Tamanho do Conjunto Residente (resident) <br> Páginas Residentes Compartilhadas (shared) <br> Texto (text) <br> Dados + Pilha (data) |
| Disco    | Requisições <br> Requisições <br> Bytes <br> Bytes <br> Chars <br> Chars <br> | Leitura <br> Escrita <br> Leitura <br> Escrita <br> Leitura <br> Escrita <br> |
| Rede |  Bytes <br> Bytes <br> Pacotes <br> Pacotes  <br> Quantidade <br> Quantitade <br> Quantidade <br>  Quantidade <br> Quantidade <br> Quantidade | Enviados <br> Recebidos <br> Enviados <br> Recebidos <br> Total de erros de transmissão <br> Pacotes com erro de frame <br> Pacotes descartados <br> Pacotes comprimidos <br> Perdas de transmissão <br> Frames de Multicast <br> |

#### **Docker**
|  Type   |  Unit  | Metric |
| ------- | ------ | ------ |
| CPU     | Ciclos <br> Ciclos <br> Quantidade <br> Quantidade <br> Ciclos <br> | Usuário <br> Sistema <br> Periods <br> Throttled <br> Throttled Time <br> |
| Memória  | Páginas <br> Páginas <br> Páginas <br> Páginas <br> Páginas <br> Páginas <br> Páginas <br> Páginas <br> Páginas <br> Páginas <br> Páginas <br> Páginas <br> | Resident Set Size (rss) <br> Chached <br> Mapped (mapped_file) <br> Paged In (pgpgin) <br> Paged Out (pgpgout) <br> Page Faults (pgfault) <br> Major Page Faults (pgmajfault) <br> Active (active_anon) <br> Inactive (inactive_anon) <br> Active File (active_file)<br> Inactive File (inactive_file) <br> Unevictable <br> |
| Disco    | Bytes <br> Bytes <br> Bytes <br> Bytes <br> Bytes <br> Bytes <br> | Leitura <br> Escrita <br> Sincronizados <br> Assíncronos <br> Descartados <br> Total <br> |
| Rede |  Bytes <br> Bytes <br> Pacotes <br> Pacotes  <br> Quantidade <br> Quantitade <br> Quantidade <br>  Quantidade <br> Quantidade <br> Quantidade | Enviados <br> Recebidos <br> Enviados <br> Recebidos <br> Total de erros de transmissão <br> Pacotes com erro de frame <br> Pacotes descartados <br> Pacotes comprimidos <br> Perdas de transmissão <br> Frames de Multicast <br> |


## Instalação
Antes de definitivamente instalar o Kubemon, verifique se o Kubernetes e o Docker estão propriamente instalados no sistema.

1. Baixe a última versão aqui: [kubemon](https://github.com/hrchlhck/kubemon/zipball/main) 

2. Extraia o arquivo ```.zip```  e entre no diretório extraído.

3. Atualize o campo ```nodeName``` no arquivo ```kubernetes/04_collector.yaml``` para o nome do control-plane do Kubernetes.

4. Aplique os objetos Kubernetes dentro do diretório ```kubernetes/```:
    ```sh
    $ kubectl apply -f kubernetes/
    namespace/kubemon created
    configmap/kubemon-env created
    persistentvolume/kubemon-volume created
    persistentvolumeclaim/kubemon-volume-claim created
    service/collector created
    service/monitor created
    pod/collector created
    daemonset.apps/kubemon-monitor created
    ```

## Configuração
A ferramenta tem algumas variáveis que podem ser configuradas pelo usuário. Por exemplo, alguns dos campos obrigatórios para serem configurados antes de iniciar a ferramenta é ```NUM_DAEMONS```, que especifica a quantidade esperada de nós para se coletar as métricas. Ainda, os componentes do Kubemon são configurados através de variáveis de ambiente dentro dos Pods do Kubernetes.

O arquivo de configuração está em ```kubernetes/01_configmap.yaml```. Na presente versão do Kubemon, o ConfigMap lista todas as variáveis para configuração. Você pode atualizar os valores delas de acordo com suas necessidades.

As métricas coletadas serão salvas no control-plane do Kubernetes por padrão, no diretório ```/mnt/kubemon-data```. Essa configuração pode ser alterada em ```./kubernetes/02_volumes.yaml```, atualizando o campo ```hostPath```.

Exemplo: 
```yaml
# Antes
...
hostPath:
    path: "/mnt/kubemon-data"
    
# Depois
...
hostPath:
    path: "/home/user/data"
```

## Executando
### Iniciando
Para iniciar a etapa de coleta, você pode iniciá-la através da linha de comando ou executar os comandos dentro do Python.

Exemplo usando a linha de comando:
```sh
$ make cli host=10.0.1.2
Waiting for collector to be alive
Collector is alive!
>>> start test000
Starting 2 daemons and saving data at 10.0.1.2:/home/kubemon/output/data/test000
```

Exemplo usando o Python:
```python
>>> from kubemon.collector import CollectorClient
>>> from kubemon.settings import CLI_PORT
>>> 
>>> cc = CollectorClient('10.0.1.2', CLI_PORT)
>>> cc.start('test000')
Starting 2 daemons and saving data at 10.0.1.2:/home/kubemon/output/data/test000
```

### Parando

Usando a linha de comando:
```sh
>>> stop
Stopped collector
```

Usando Python:
```python
...
>>> cc.stop()
Stopped collector
```

### Todos os Comandos:
Você pode listar todos os comandos implementados executando o comando ```help``` na linha de comando ou executando o método ```.help()``` no Python.

Todos os comandos:
```
'start': Start collecting metrics from all connected daemons in the collector.

    Args:
        - Directory name to be saving the data collected. Ex.: start test000
    
'instances': Lists all the connected monitor instances.
    
'daemons': Lists all the daemons (hosts) connected.
    
'stop': Stop all monitors if they're running.
    
'help': Lists all the available commands.
    
'alive': Tells if the collector is alive.
```

## Video Demonstrativo
Para assistir o vídeo, basta clicar na imagem a seguir.

[![Imagem do Video](https://img.youtube.com/vi/QwlOn1gwLpA/1.jpg)](https://youtu.be/QwlOn1gwLpA)

## Referências
- [Block layer statistics](https://www.kernel.org/doc/html/latest/block/stat.html)
- [/proc virtual file system](https://man7.org/linux/man-Páginas/man5/proc.5.html)
- [Evaluation of desktop operating systems under thrashing conditions](https://journal-bcs.springeropen.com/track/pdf/10.1007/s13173-012-0080-8.pdf)
- [cgroups](https://www.man7.org/linux/man-Páginas/man7/cgroups.7.html)
- [Docker runtime metrics](https://docs.docker.com/config/containers/runmetrics/)
