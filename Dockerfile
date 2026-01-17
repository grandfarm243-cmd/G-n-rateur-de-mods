FROM python:3.11-slim
WORKDIR /app
COPY generate_mod.py bot.py /app/
RUN pip install --no-cache-dir discord.py
ENV PYTHONUNBUFFERED=1
CMD ["python", "bot.py"]