FROM python:3.10

WORKDIR /bot

RUN pip install discord.py
RUN pip install wavelink

COPY . .

CMD ["python", "bot.py"]