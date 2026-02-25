# Regras de Negócio — Gestão de Salas de Aula

Este documento descreve as regras de negócio do sistema de gestão de salas de aula, organizadas por tema, com indicação de status de implementação e prioridade.

---

## 1. Cadastro e Configuração de Salas

| Código | Regra | Status |
|--------|-------|--------|
| RN-01 | O horário de término da sala (`hora_fim`) deve ser sempre posterior ao de início (`hora_inicio`). | ✅ Implementado |
| RN-02 | O nome da sala deve ser único no sistema (sem duplicatas). | ✅ Implementado |
| RN-03 | A sala deve ter uma **capacidade máxima** (número de pessoas), impedindo reservas que extrapolem esse limite. | ✅ Implementado |
| RN-04 | Salas podem ter um **tipo** (Ex: Laboratório, Auditório, Sala Comum), para filtros e buscas mais eficientes. | ✅ Implementado |

---

## 2. Reservas — Criação e Validação

| Código | Regra | Status |
|--------|-------|--------|
| RN-05 | A data/hora de início da reserva deve ser **anterior** à de término. | ⬜ Pendente |
| RN-06 | Não é permitido fazer duas reservas **sobrepostas** para a mesma sala (conflito de horário). | ⬜ Pendente |
| RN-07 | A reserva só pode ser feita dentro do **horário de disponibilidade** da sala (`hora_inicio` a `hora_fim`). | ⬜ Pendente |
| RN-08 | Não é permitido reservar com **data/hora no passado**. | ⬜ Pendente |
| RN-09 | Cada reserva deve ter uma **duração mínima** configurável (ex: 30 minutos) e uma **duração máxima** (ex: 4 horas), para evitar monopolização. | ⬜ Pendente |
| RN-10 | Um mesmo usuário não pode ter mais de **N reservas ativas simultaneamente** (ex: 3), para garantir acesso democrático. | ⬜ Pendente |

---

## 3. Gestão de Tempo e Cancelamento

| Código | Regra | Status |
|--------|-------|--------|
| RN-11 | O usuário só pode **cancelar** sua reserva com antecedência mínima (ex: 1 hora antes do início). | ⬜ Pendente |
| RN-12 | Reservas **não utilizadas** (usuário não deu check-in dentro de X minutos do início) podem ser liberadas automaticamente. | ⬜ Pendente |
| RN-13 | O sistema pode enviar **notificações** (e-mail ou alerta no sistema) lembrando o usuário da reserva próxima. | ⬜ Pendente |
| RN-14 | Reservas só podem ser criadas com **antecedência mínima** configurável (ex: pelo menos 15 minutos antes do início). | ⬜ Pendente |

---

## 4. Permissões e Papéis de Usuário

| Código | Regra | Status |
|--------|-------|--------|
| RN-15 | Usuários comuns só podem **criar, ver e cancelar suas próprias** reservas. | ⬜ Pendente |
| RN-16 | Administradores podem criar, editar e excluir **salas** e **qualquer reserva**. | ⬜ Pendente |
| RN-17 | Somente usuários **autenticados** podem fazer reservas. | ✅ Parcialmente implementado |
| RN-18 | Administradores podem visualizar um **relatório de ocupação** por sala e por período. | ⬜ Pendente |

---

## 5. Otimização e Relatórios

| Código | Regra | Status |
|--------|-------|--------|
| RN-19 | O dashboard deve exibir a **taxa de ocupação** de cada sala (% do tempo disponível que está reservado no dia/semana). | ⬜ Pendente |
| RN-20 | Salas com baixo índice de utilização (< X%) em um período devem ser destacadas no painel do administrador. | ⬜ Pendente |
| RN-21 | O sistema deve permitir buscar salas disponíveis em um **intervalo de tempo específico** informado pelo usuário. | ⬜ Pendente |

---

## 6. Recorrência (Avançado)

| Código | Regra | Status |
|--------|-------|--------|
| RN-22 | O usuário pode criar **reservas recorrentes** (ex: toda segunda-feira das 10h às 12h), com limite máximo de semanas. | ⬜ Pendente |
| RN-23 | Ao criar recorrência, o sistema deve verificar **disponibilidade em todas as datas** antes de confirmar. | ⬜ Pendente |

---

## Priorização de Implementação

### 🔴 Alta Prioridade — impacto direto na usabilidade

- **RN-02** — Nome de sala único
- **RN-05** — Início antes do término na reserva
- **RN-06** — Sem conflito de horário entre reservas da mesma sala
- **RN-07** — Reserva dentro do horário de disponibilidade da sala
- **RN-08** — Proibir reservas no passado
- **RN-09** — Duração mínima e máxima por reserva
- **RN-10** — Limite de reservas ativas por usuário
- **RN-15** — Usuário gerencia apenas suas próprias reservas
- **RN-16** — Papel de Administrador com acesso total

### 🟡 Média Prioridade — melhora a experiência

- **RN-03** — Capacidade máxima da sala
- **RN-04** — Tipo de sala
- **RN-11** — Cancelamento com antecedência mínima
- **RN-17** — Autenticação obrigatória para reservas
- **RN-19** — Taxa de ocupação no dashboard
- **RN-21** — Busca de salas por intervalo de tempo

### 🟢 Baixa Prioridade — funcionalidades avançadas

- **RN-12** — Liberação automática de reservas não utilizadas
- **RN-13** — Notificações de reserva
- **RN-14** — Antecedência mínima para criação de reserva
- **RN-18** — Relatório de ocupação para administradores
- **RN-20** — Destaque de salas com baixa utilização
- **RN-22** — Reservas recorrentes
- **RN-23** — Verificação de disponibilidade em reservas recorrentes
