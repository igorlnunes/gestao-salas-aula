# 📋 Regras de Negócio — Gestão de Salas de Aula

Este documento descreve as regras de negócio e sugestões para otimizar o uso e o tempo das salas de aula no projeto.

---

## 🏛️ 1. Cadastro e Configuração de Salas

| Regra | Descrição | Status |
|---|---|---|
| **RN-01** | O horário de término da sala (`hora_fim`) deve ser sempre posterior ao de início (`hora_inicio`). | ✅ Implementado |
| **RN-02** | O nome da sala deve ser único no sistema (sem duplicatas). | ✅ Implementado |
| **RN-03** | A sala deve ter uma **capacidade máxima** (número de pessoas), impedindo reservas que extrapolem esse limite. | ✅ Implementado |
| **RN-04** | Salas podem ter um **tipo** (Ex: Laboratório, Auditório, Sala Comum), para filtros e buscas mais eficientes. | ⏳ Pendente |

---

## 📅 2. Reservas — Criação e Validação

| Regra | Descrição | Prioridade |
|---|---|---|
| **RN-05** | A data/hora de início da reserva deve ser **anterior** à de término. | Alta |
| **RN-06** | Não é permitido fazer duas reservas **sobrepostas** para a mesma sala (conflito de horário). | Alta |
| **RN-07** | A reserva só pode ser feita dentro do **horário de disponibilidade** da sala (`hora_inicio` a `hora_fim`). | Alta |
| **RN-08** | Não é permitido reservar com **data/hora no passado**. | Alta |
| **RN-09** | Cada reserva deve ter uma **duração mínima** configurável (ex: 30 minutos) e uma **duração máxima** (ex: 4 horas). | Média |
| **RN-10** | Um mesmo usuário não pode ter mais de **N reservas ativas simultaneamente**. | Média |

---

## ⏰ 3. Gestão de Tempo e Cancelamento

| Regra | Descrição | Prioridade |
|---|---|---|
| **RN-11** | O usuário só pode **cancelar** sua reserva com antecedência mínima (ex: 1 hora antes do início). | Média |
| **RN-12** | Reservas **não utilizadas** (check-in não realizado) podem ser liberadas automaticamente. | Baixa |
| **RN-13** | Envio de **notificações** (e-mail ou alerta) lembrando o usuário da reserva próxima. | Baixa |
| **RN-14** | Reservas confirmadas com **antecedência mínima** de N minutos/horas. | Média |

---

## 👤 4. Permissões e Papéis de Usuário

| Regra | Descrição | Status |
|---|---|---|
| **RN-15** | Usuários comuns só podem **criar, ver e cancelar suas próprias** reservas. | ⏳ Pendente |
| **RN-16** | Administradores podem criar/editar/excluir **salas** e **qualquer reserva**. | ⏳ Pendente |
| **RN-17** | Somente usuários **autenticados** podem fazer reservas. | ✅ Implementado |
| **RN-18** | Administradores podem visualizar um **relatório de ocupação** por sala e por período. | ⏳ Pendente |

---

## 📊 5. Otimização e Relatórios

| Regra | Descrição | Prioridade |
|---|---|---|
| **RN-19** | Exibição da **taxa de ocupação** de cada sala no dashboard. | Média |
| **RN-20** | Destaque para salas com baixo índice de utilização (< X%). | Baixa |
| **RN-21** | Busca de salas disponíveis em um **intervalo de tempo específico**. | Média |

---

## 🔁 6. Recorrência (Avançado)

| Regra | Descrição | Prioridade |
|---|---|---|
| **RN-22** | Possibilidade de criar **reservas recorrentes** (ex: toda segunda-feira). | Baixa |
| **RN-23** | Verificação de **disponibilidade em todas as datas** da recorrência antes da confirmação. | Baixa |

---

## 🚦 Priorização para Implementação

1.  **Crítico (Essencial para funcionamento):** RN-02, RN-05, RN-06, RN-07, RN-08.
2.  **Importante (Melhoria de uso):** RN-03, RN-04, RN-09, RN-10, RN-15, RN-16.
3.  **Desejável (Otimização):** Demais regras.
