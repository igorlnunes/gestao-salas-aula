# Lista de Melhorias Sugeridas

Esta lista descreve melhorias potenciais para o projeto "config" (Gestão de Salas), focando em segurança, arquitetura e manutenibilidade.

## 1. Segurança e Configuração
- **Variáveis de Ambiente:** Migrar chaves sensíveis (`SECRET_KEY`, credenciais de banco de dados, `DEBUG`) para variáveis de ambiente usando `python-dotenv` ou `django-environ`.
- **Hosts Permitidos:** Configurar `ALLOWED_HOSTS` de forma restritiva para produção (atualmente permite `*` ou vazio).
- **HTTPS:** Enforçar HTTPS em produção (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`).

## 2. Banco de Dados e Modelagem
- **PostgreSQL:** Migrar de SQLite para PostgreSQL para ambientes de produção.
- **Validação de Reservas:** Mover a lógica de verificação de sobreposição de horários (atualmente parcial nas views/forms) para o método `clean()` do modelo `Reserva` ou para um `Service` dedicado, garantindo integridade dos dados em qualquer ponto de entrada.
- **Campos Adicionais:** Adicionar capacidade (número de assentos) e recursos (projetor, ar-condicionado) ao modelo `Sala`.

## 3. Frontend e Templates
- **Crispy Forms:** Utilizar `django-crispy-forms` ou `django-widget-tweaks` para renderização de formulários Bootstrap mais limpa e consistente, removendo a necessidade de definir classes CSS manualmente nos widgets do `forms.py`.
- **Arquivos Estáticos:** Configurar `WhiteNoise` para servir arquivos estáticos em produção. Considerar baixar as dependências do Bootstrap localmente ao invés de depender de CDN para maior robustez.
- **HTMX / JavaScript:** Adicionar interatividade (ex: validação de disponibilidade de sala em tempo real) sem recarregar a página completa.

## 4. Código e Arquitetura
- **Testes Automatizados:** O arquivo `webapp/tests.py` está vazio. É crucial implementar testes unitários para models (validações) e views (permissões, fluxo de reserva).
- **API REST:** Implementar `Django Rest Framework` (DRF) se houver planos para um frontend separado (React/Vue) ou aplicativo móvel.
- **Internacionalização (i18n):** Padronizar o idioma. O código mistura variáveis em inglês (`Room`, `welcome`) com strings em português. Usar `gettext` para traduções se o suporte a múltiplos idiomas for desejado.
- **Organização:** Se o projeto crescer, separar as lógicas de "Autenticação" e "Reservas" em apps distintos (ex: `accounts` e `reservations`).

## 5. Funcionalidades
- **Recuperação de Senha:** Implementar fluxo de "Esqueci minha senha".
- **Confirmação de E-mail:** Enviar e-mail de verificação após o cadastro.
- **Histórico:** Adicionar logs ou histórico de alterações para auditoria de quem reservou qual sala.
