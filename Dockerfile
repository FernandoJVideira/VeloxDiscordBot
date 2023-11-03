FROM python:3.10

WORKDIR /bot

RUN pip install discord.py
RUN pip install wavelink
RUN pip install easy-pil

COPY . .

CMD ["python", "bot.py"]