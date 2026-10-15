# Delta de referências de processamento

A entrada Lambda passou a citar RADStack, artigo primário que descreve caminhos batch e stream com Hadoop, Samza, Kafka e Druid. A entrada Kappa passou a ligar Kafka Streams ao WordCountDemo e ao procedimento oficial de reset; a classificação Kappa é uma análise declarada, sem afirmar que o upstream usa esse rótulo ou que o MakersHub implementa replay.

Foram descartadas como exemplo OSS atual Kamu e Materialize: o código acessível não elimina as restrições BSL. O protótipo blacklabeldata/kappa declara o padrão, mas sua manutenção de 2015 e seu entrypoint não bastaram para escolher a melhor demonstração.

- [2026-10-14 19:01:02 UTC] WordCountDemo — `GET https://raw.githubusercontent.com/apache/kafka/trunk/streams/examples/src/main/java/org/apache/kafka/streams/examples/wordcount/WordCountDemo.java` → `HTTP 200; sha256=aed61d1682337c9a6c8dd977511a13768075c91ec045dd3f61d8f33673b25ad6`.
- [2026-10-14 19:01:05 UTC] RADStack — `GET https://raw.githubusercontent.com/druid-io/druid/master/publications/radstack/radstack.pdf` → `HTTP 200; sha256=5e87571bd51906fe128e6738241a7b7b5756f5ba34174417c1760a5f9bafc568`.
