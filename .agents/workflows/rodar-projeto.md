---
description: Como rodar o projeto de Gestão de Salas de Aula
---

Para rodar o projeto, siga os passos abaixo no seu terminal:

1. **Ative o ambiente virtual:**
   ```bash
   source .venv/bin/activate
   ```

2. **Instale as dependências (se necessário):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Aplique as migrações do banco de dados:**
   ```bash
   python manage.py migrate
   ```

4. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

O projeto estará disponível em `http://127.0.0.1:8000/`.

---
**Dica:** Se você precisar acessar a área administrativa, crie um superusuário com:
```bash
python manage.py createsuperuser
```
